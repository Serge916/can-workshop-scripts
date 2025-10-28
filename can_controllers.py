import os
import can


class N5CanController:

    def __init__(self):
        # Set up the CAN interfaces on the system
        os.system("sudo ip link set can1 type can bitrate 1000000")
        os.system("sudo ifconfig can1 up")
        self.dev = can.interface.Bus(channel="can1", bustype="socketcan")
        self.setupMotor()

    def close(self):
        self.send(identifier=0x601, data=0x2B40600006000000)
        os.system("sudo ifconfig can1 down")

    def setupMotor(self):
        # Start node
        self.send(identifier=0x0, data=0x0101, len=2)
        # Mode of operation = velocity (2)
        self.send(identifier=0x601, data=0x2F60600002000000)
        # Ready to switch on
        self.send(identifier=0x601, data=0x2B40600006000000)
        # Switched on
        self.send(identifier=0x601, data=0x2B40600007000000)
        # Operation enabled
        self.send(identifier=0x601, data=0x2B4060000F000000)

    def send(self, identifier: int, data: int, len: int = 8):
        msg = can.Message(
            is_extended_id=False,
            arbitration_id=identifier,
            data=data.to_bytes(len, byteorder="big"),
        )
        self.dev.send(msg)

    def recv(self):
        return self.dev.recv()
