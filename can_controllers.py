import os
import can
import time

CAN_MAX_BITRATE = 1000000  # I'm setting it to CAN. Change it case of XL.


class N5CanController:

    def __init__(self, nodeID: int, interface: str, bitrate: int = CAN_MAX_BITRATE):
        if bitrate < 1 or bitrate > CAN_MAX_BITRATE:
            raise (ValueError, "Choose a valid bitrate value.")
        self.interface = interface
        self.nodeID = nodeID
        # Set up the CAN interfaces on the system
        os.system(f"sudo ip link set {self.interface} type can bitrate {bitrate}")
        os.system(f"sudo ifconfig {self.interface} up")
        self.dev = can.interface.Bus(channel=self.interface, bustype="socketcan")
        self._setupMotor()

    def _setupMotor(self):
        # Start node
        self.send(
            identifier=0x0,
            data=N5CanController.formatNetworkManagement(cmd=0x01, nodeID=self.nodeID),
        )
        # Mode of operation = profile velocity (3)
        self.send(
            identifier=0x600 + self.nodeID,
            data=N5CanController.formatServiceDataObjectDownload(
                cmd=0x2F, idx=0x6060, subidx=0x00, data=0x03
            ),
        )
        # Ready to switch on
        self.send(
            identifier=0x600 + self.nodeID,
            data=N5CanController.formatServiceDataObjectDownload(
                cmd=0x2B, idx=0x6040, subidx=0x00, data=0x0006
            ),
        )
        # Switched on
        self.send(
            identifier=0x600 + self.nodeID,
            data=N5CanController.formatServiceDataObjectDownload(
                cmd=0x2B, idx=0x6040, subidx=0x00, data=0x0007
            ),
        )
        # Operation enabled
        self.send(
            identifier=0x600 + self.nodeID,
            data=N5CanController.formatServiceDataObjectDownload(
                cmd=0x2B, idx=0x6040, subidx=0x00, data=0x000F
            ),
        )
        # Set profile acceleration (6083h) = 1000
        self.send(
            identifier=0x600 + self.nodeID,
            data=N5CanController.formatServiceDataObjectDownload(
                cmd=0x23, idx=0x6083, subidx=0x00, data=1000
            ),
        )
        # Set profile deceleration (6084h) = 1000
        self.send(
            identifier=0x600 + self.nodeID,
            data=N5CanController.formatServiceDataObjectDownload(
                cmd=0x23, idx=0x6084, subidx=0x00, data=1000
            ),
        )

    def close(self):
        self.send(
            identifier=0x600 + self.nodeID,
            data=N5CanController.formatServiceDataObjectDownload(
                cmd=0x2B, idx=0x6040, subidx=0x00, data=0x0006
            ),
        )
        os.system(f"sudo ifconfig {self.interface} down")

    def setSpeed(self, speed: int):
        # Build SDO payload for object 6042h:00h (Vl Target Velocity)
        payload = N5CanController.formatServiceDataObjectDownload(
            cmd=0x23,  # expedited, 4-byte data
            idx=0x60FF,  # target velocity object
            subidx=0x00,  # sub-index
            data=speed,
        )
        self.send(identifier=0x600 + self.nodeID, data=payload)

    def getStatusWord(self) -> int:
        """Read 6041h (Statusword) and return it as an int."""
        # Initiate SDO upload
        self.send(
            identifier=0x600 + self.nodeID,
            data=N5CanController.formatServiceDataObjectUpload(
                idx=0x6041,  # target velocity object
                subidx=0x00,  # sub-index
            ),
        )

        # Wait for SDO response
        msg = self.recv()
        while msg.arbitration_id != 0x581:
            msg = self.recv()

        if msg.data[0] == 0x80:
            print(f"SDO Upload error code: {msg.data[4:8]}")

        # Bytes 4–5 (little-endian) hold the Statusword
        val = int.from_bytes(msg.data[4:6], "little")
        return val

    def send(self, identifier: int, data: bytes, extended_id: bool = False):
        msg = can.Message(
            is_extended_id=extended_id,
            arbitration_id=identifier,
            data=data,
        )
        self.dev.send(msg)

    def recv(self):
        return self.dev.recv()

    @staticmethod
    def formatServiceDataObjectDownload(cmd: int, idx: int, subidx: int, data: int):
        if cmd not in (0x2F, 0x2B, 0x27, 0x23):
            raise (ValueError, "Not a valid CMD value.")

        cmd = cmd.to_bytes(1)
        idx = idx.to_bytes(2, "little", signed=False)
        subidx = subidx.to_bytes(1)
        # SDO messages must be 8-Byte long. In case it is not. Fill with 0
        data = data.to_bytes(4, "little", signed=True)
        return cmd + idx + subidx + data

    @staticmethod
    def formatServiceDataObjectUpload(idx: int, subidx: int):
        idx = idx.to_bytes(2, "little", signed=False)
        subidx = subidx.to_bytes(1)
        # SDO messages must be 8-Byte long. In case it is not. Fill with 0
        return bytes([0x40]) + idx + subidx + bytes(4)

    @staticmethod
    def formatNetworkManagement(cmd: int, nodeID: int):
        if cmd not in (0x01, 0x02, 0x80, 0x81, 0x82):
            raise (ValueError, "Not a valid CMD value.")

        cmd = cmd.to_bytes(1)
        nodeID = nodeID.to_bytes(1)
        return cmd + nodeID


class RoboteqCanController:
    def __init__(self, nodeID: int, interface: str, bitrate: int = CAN_MAX_BITRATE):
        if bitrate < 1 or bitrate > CAN_MAX_BITRATE:
            raise ValueError("Choose a valid bitrate value.")
        self.interface = interface
        self.nodeID = nodeID

        # Setup CAN interface (ignore if already up)
        os.system(f"sudo ip link set {self.interface} type can bitrate {bitrate}")
        os.system(f"sudo ifconfig {self.interface} up")
        self.dev = can.interface.Bus(channel=self.interface, bustype="socketcan")

        self._setupMotor()

    def _setupMotor(self):
        """Initializes the motor controller into operational state."""

        # (Optional but recommended while testing) Disable command watchdog
        self.send(
            0x600 + self.nodeID,
            RoboteqCanController.formatSDODownload(
                cmd=0x2B, idx=0x3008, subidx=0x00, data=0
            ),
        )  # RWD=0

        # NMT Start
        self.send(0x000, self.formatNetworkManagement(cmd=0x01, nodeID=self.nodeID))

        # --- DS402 enable path ---
        # Ready to switch on -> Switched on
        self.send(
            0x600 + self.nodeID,
            RoboteqCanController.formatSDODownload(
                cmd=0x2B, idx=0x6040, subidx=0x00, data=0x0006
            ),
        )
        self.send(
            0x600 + self.nodeID,
            RoboteqCanController.formatSDODownload(
                cmd=0x2B, idx=0x6040, subidx=0x00, data=0x0007
            ),
        )

        # Mode of operation = Profile Velocity (3)  [U8 write => 0x2F]
        self.send(
            0x600 + self.nodeID,
            RoboteqCanController.formatSDODownload(
                cmd=0x2F, idx=0x6060, subidx=0x00, data=3
            ),
        )

        # Accel/Decel are U32 (use 0x23)
        self.send(
            0x600 + self.nodeID,
            RoboteqCanController.formatSDODownload(
                cmd=0x23, idx=0x6048, subidx=0x01, data=20000
            ),
        )  # accel
        self.send(
            0x600 + self.nodeID,
            RoboteqCanController.formatSDODownload(
                cmd=0x23, idx=0x6049, subidx=0x01, data=20000
            ),
        )  # decel

        # Operation enabled
        self.send(
            0x600 + self.nodeID,
            RoboteqCanController.formatSDODownload(
                cmd=0x2B, idx=0x6040, subidx=0x00, data=0x000F
            ),
        )

    def stop(self):
        """Stop the motor and disable voltage."""
        self.send(
            0x600 + self.nodeID,
            RoboteqCanController.formatSDODownload(
                cmd=0x2B, idx=0x6040, subidx=0x00, data=0x00
            ),
        )

    def setSpeed(self, rpm: int, channel: int):
        match channel:
            case 1:
                idx = 0x60FF
            case 2:
                idx = 0x68FF
            case 3:
                idx = 0x68FF
            case _:
                raise (ValueError, "Not valid channel value")

        self.send(
            0x600 + self.nodeID,
            RoboteqCanController.formatSDODownload(
                cmd=0x23, idx=idx, subidx=0x00, data=rpm
            ),
        )

    # -------------------- Diagnostics (SDO reads) --------------------

    def getStatusWord(self) -> int:
        """Read 0x6041 (Statusword, U16)."""
        self.send(0x600 + self.nodeID, self.formatSDOUpload(0x6041, 0x00))
        msg = self.recv()
        while msg.arbitration_id != 0x580 + self.nodeID:
            msg = self.recv()
        if msg.data[0] == 0x80:
            print(f"SDO Upload error: {msg.data.hex()}")
            return None
        return int.from_bytes(msg.data[4:6], "little", signed=False)

    def get_error_register(self) -> int:
        """Read 0x1001:00 (U8)."""
        self.send(0x600 + self.nodeID, self.formatSDOUpload(0x1001, 0x00))
        msg = self.recv()
        return msg.data[4]

    def get_fault_code(self) -> int:
        """Read 0x603F:00 (U16)."""
        self.send(0x600 + self.nodeID, self.formatSDOUpload(0x603F, 0x00))
        msg = self.recv()
        while msg.arbitration_id != 0x580 + self.nodeID:
            msg = self.recv()
        return int.from_bytes(msg.data[4:6], "little", signed=False)

    # -------------------- Low-level helpers --------------------

    def close(self):
        os.system(f"sudo ifconfig {self.interface} down")

    def send(self, identifier: int, data: bytes):
        msg = can.Message(is_extended_id=False, arbitration_id=identifier, data=data)
        self.dev.send(msg)

    def recv(self):
        return self.dev.recv()

    @staticmethod
    def formatSDODownload(cmd: int, idx: int, subidx: int, data: int):
        """
        Build an expedited SDO download frame payload.
        You must pass the correct 'cmd' for the data width you intend:
          0x23 = 4 bytes (U32/S32), 0x2B = 2 bytes (U16), 0x2F = 1 byte (U8)
        """
        idx_b = idx.to_bytes(2, "little")
        sub_b = subidx.to_bytes(1, "little")
        data_b = int(data).to_bytes(4, "little", signed=True)  # always 4 bytes in frame
        return bytes([cmd]) + idx_b + sub_b + data_b

    @staticmethod
    def formatSDOUpload(idx: int, subidx: int):
        """Format an SDO upload request."""
        return bytes([0x40]) + idx.to_bytes(2, "little") + bytes([subidx]) + bytes(4)

    @staticmethod
    def formatNetworkManagement(cmd: int, nodeID: int):
        """NMT: 0x01=Start, 0x02=Stop, 0x80=Pre-Op, etc."""
        return bytes([cmd, nodeID])
