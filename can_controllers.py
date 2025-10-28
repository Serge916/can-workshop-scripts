import os
import can



class N5CanController:

    def __init__(self):
        # Set up the CAN interfaces on the system
        os.system("sudo ip link set can1 type can bitrate 1000000")
        os.system("sudo ifconfig can1 up")
        self.dev = can.interface.Bus(channel="can1", bustype="socketcan")
        self._setupMotor()

    def _setupMotor(self):
        # Start node
        self.send(identifier=0x0, data=N5CanController.formatNetworkManagement(cmd=0x01, nodeID=0x01))
        # Mode of operation = profile velocity (3)
        self.send(identifier=0x601, data=N5CanController.formatServiceDataObject(
            cmd=0x2F, idx=0x6060, subidx=0x00, data=0x03
        ))
        # Ready to switch on
        self.send(identifier=0x601, data=N5CanController.formatServiceDataObject(
            cmd=0x2B, idx=0x6040, subidx=0x00, data=0x0006
        ))
        # Switched on
        self.send(identifier=0x601, data=N5CanController.formatServiceDataObject(
            cmd=0x2B, idx=0x6040, subidx=0x00, data=0x0007
        ))
        # Operation enabled
        self.send(identifier=0x601, data=N5CanController.formatServiceDataObject(
            cmd=0x2B, idx=0x6040, subidx=0x00, data=0x000F
        ))
        # Set profile acceleration (6083h) = 1000
        self.send(identifier=0x601, data=N5CanController.formatServiceDataObject(
            cmd=0x23, idx=0x6083, subidx=0x00, data=1000
        ))
        # Set profile deceleration (6084h) = 1000
        self.send(identifier=0x601, data=N5CanController.formatServiceDataObject(
            cmd=0x23, idx=0x6084, subidx=0x00, data=1000
        ))


    def close(self):
        self.send(identifier=0x601, data=(0x2B40600006000000).to_bytes(8, byteorder='big'))
        os.system("sudo ifconfig can1 down")

    def setSpeed(self, speed:int):
        # Build SDO payload for object 6042h:00h (Vl Target Velocity)
        payload = N5CanController.formatServiceDataObject(
            cmd=0x23,     # expedited, 4-byte data
            idx=0x60FF,   # target velocity object
            subidx=0x00,  # sub-index
            data=speed
        )
        self.send(identifier=0x601, data=payload)


    def send(self, identifier: int, data: bytes, extended_id:bool=False):
        msg = can.Message(
            is_extended_id=extended_id,
            arbitration_id=identifier,
            data=data,
        )
        self.dev.send(msg)

    def recv(self):
        return self.dev.recv()

    @staticmethod
    def formatServiceDataObject(cmd: int, idx:int, subidx:int, data:int):
        if cmd not in (0x2F,0x2B,0x27,0x23):
            raise(ValueError, "Not a valid CMD value.")

        cmd = cmd.to_bytes(1)
        idx = idx.to_bytes(2, 'little', signed=False)
        subidx = subidx.to_bytes(1)
        # SDO messages must be 8-Byte long. In case it is not. Fill with 0
        data = data.to_bytes(4,'little', signed=True)
        return cmd+idx+subidx+data  

    @staticmethod
    def formatNetworkManagement(cmd: int, nodeID:int):
        if cmd not in (0x01,0x02,0x80,0x81, 0x82):
            raise(ValueError, "Not a valid CMD value.")

        cmd = cmd.to_bytes(1)
        nodeID = nodeID.to_bytes(1)
        return cmd+nodeID    
