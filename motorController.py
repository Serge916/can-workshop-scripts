# Basic example on how to use the N5CanController to control the motor
# Possible reasons for failure:
# - Not booting up the Raspberry with the HAT on

from can_controllers import N5CanController
import time

# Create CAN objects
can = N5CanController("can1")

print("Motor is set up")
try:
    while True:
        print("Moving forward for 2s")
        can.setSpeed(200)   
        time.sleep(2)
        print("Faster for 2s")
        can.setSpeed(500)   
        time.sleep(2)
        print("Stopping")
        can.setSpeed(0)     
        time.sleep(2)
        print("Moving backward for 2s")
        can.setSpeed(-200)  
        time.sleep(2)
        print("Faster for 2s")
        can.setSpeed(-500)   
        time.sleep(2)
        print("Stopping")
        can.setSpeed(0)     
        time.sleep(2)
finally:
    can.close()