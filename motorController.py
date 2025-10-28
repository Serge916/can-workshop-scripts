# Basic example on how to communicate the both CAN channels within the HAT
# Possible reasons for failure:
# - Not booting up the Raspberry with the HAT on

from can_controllers import N5CanController


# Create CAN objects
can = N5CanController()

# Create a CAN mesage struct
can.send(identifier=0x601, data=0x2B4060000F000000)
# Receive the message from CAN1. Takes one message per function call
print("Listening....")
try:
    while True:
        print(can.recv())
finally:
    pass
    can.close()