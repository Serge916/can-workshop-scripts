# Basic example on how to use the N5CanController to control the motor
# Possible reasons for failure:
# - Not booting up the Raspberry with the HAT on

from can_controllers import N5CanController
import time

# Create CAN objects
can = N5CanController("can1")

print("Motor is set up")
try:
    # Set up speed target
    can.setSpeed(600)
    # Check in StatusWord wether limit was reached   
    while not (can.getStatusWord() & (1<<9)):
        pass
    print("Velocity reached. Now spinning for 5s")
    time.sleep(5)
finally:
    can.close()