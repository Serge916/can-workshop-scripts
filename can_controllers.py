import os
import can

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


class temporal:

    def __init__(self, nodeID: int, interface: str, bitrate: int = CAN_MAX_BITRATE):
        if bitrate < 1 or bitrate > CAN_MAX_BITRATE:
            raise (ValueError, "Choose a valid bitrate value.")
        self.interface = interface
        self.nodeID = nodeID
        # Set up the CAN interfaces on the system
        os.system(f"sudo ip link set {self.interface} type can bitrate {bitrate}")
        os.system(f"sudo ifconfig {self.interface} up")
        self.dev = can.interface.Bus(channel=self.interface, bustype="socketcan")

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
