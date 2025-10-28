# Basic example on how to use the N5CanController to control the motor
# Possible reasons for failure:
# - Not booting up the Raspberry with the HAT on

from can_controllers import N5CanController
import time

# Create CAN objects
can = N5CanController()

print("Motor is set up")

print("Moving forward for 2s")
can.setSpeed(300)   # run forward
time.sleep(2)
print("Moving backward for 2s")
can.setSpeed(-300)  # reverse
time.sleep(2)
print("Stopping")
can.setSpeed(0)      # stop
time.sleep(2)

can.close()