# Basic example on how to communicate the both CAN channels within the HAT
# Possible reasons for failure:
# - Not booting up the Raspberry with the HAT on

import os
import can

# Set up the CAN interfaces on the system
os.system('sudo ip link set can0 type can bitrate 100000')
os.system('sudo ifconfig can0 up')
os.system('sudo ip link set can1 type can bitrate 100000')
os.system('sudo ifconfig can1 up')

try:
    # Create CAN objects
    can0 = can.interface.Bus(channel = 'can0', bustype = 'socketcan')
    can1 = can.interface.Bus(channel = 'can1', bustype = 'socketcan')
    # Create a CAN mesage struct
    msg = can.Message(is_extended_id=False, arbitration_id=0x123, data=[0, 1, 2, 3, 4, 5, 6, 9])
    msg1 = can.Message(is_extended_id=False, arbitration_id=0x123, data=[0, 1, 2, 3, 4, 5, 6, 4])
    # Send the messages from CAN0
    can0.send(msg)
    can0.send(msg1)
    # Receive the message from CAN1. Takes one message per function call
    recMsg=can1.recv()
    recMsg1=can1.recv()
    print(recMsg)
    print(recMsg1)
finally:
    # Close the interface for a clean exit
    os.system('sudo ifconfig can0 down')
    os.system('sudo ifconfig can1 down')
