# Basic example on how to communicate the both CAN channels within the HAT
# Possible reasons for failure:
# - Not booting up the Raspberry with the HAT on

import os
import can

# Set up the CAN interfaces on the system
os.system("sudo ip link set can1 type can bitrate 100000")
os.system("sudo ifconfig can1 up")

try:
    # Create CAN objects
    can1 = can.interface.Bus(channel="can1", bustype="socketcan")
    # Create a CAN mesage struct
    msg = can.Message(
        is_extended_id=False, arbitration_id=0x601, data=0x2B4060000F000000.to_bytes(8)
    )
    # Send the messages from CAN1
    can1.send(msg)
    # Receive the message from CAN1. Takes one message per function call
    print("Listening....")
    while True:
        recMsg = can1.recv()
        print(recMsg)
finally:
    # Close the interface for a clean exit
    msg = can.Message(
        is_extended_id=False, arbitration_id=0x601, data=0x2B40600006000000.to_bytes(8)
    )
    can1.send(msg)
    os.system("sudo ifconfig can1 down")
