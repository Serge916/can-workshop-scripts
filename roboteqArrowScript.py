# filename: roboteq_pynput_control.py
from can_controllers import RoboteqCanController
from pynput import keyboard
import time

# --- Constants ---
SPEED = 400
HALF = SPEED / 2

# Mapping key objects to simple direction strings
ARROWS = {
    keyboard.Key.up: "UP",
    keyboard.Key.down: "DOWN",
    keyboard.Key.left: "LEFT",
    keyboard.Key.right: "RIGHT",
}

# Define motor speeds for each key combination
KEY_TO_TUPLE_MAP = {
    frozenset({"UP"}): (SPEED, SPEED),
    frozenset({"DOWN"}): (-SPEED, -SPEED),
    frozenset({"RIGHT"}): (SPEED, 0),
    frozenset({"LEFT"}): (0, SPEED),
    frozenset({"UP", "RIGHT"}): (SPEED, HALF),
    frozenset({"UP", "LEFT"}): (HALF, SPEED),
    frozenset({"DOWN", "RIGHT"}): (-SPEED, -HALF),
    frozenset({"DOWN", "LEFT"}): (-HALF, -SPEED),
}

# --- Globals ---
pressed = set()
last_combo = None


def update_speed(controller):
    """Send motor speeds based on current pressed keys."""
    global last_combo
    combo = frozenset(pressed)
    if combo != last_combo:
        left, right = KEY_TO_TUPLE_MAP.get(combo, (0, 0))
        controller.setSpeed(left, channel=2)
        controller.setSpeed(right, channel=1)
        # Optional feedback
        print(f"{sorted(list(combo)) or ['(none)']} -> L:{left} R:{right}")
        last_combo = combo


def on_press(key):
    """Handle key press events."""
    if key == keyboard.Key.esc:
        return False  # Stop listener (Esc to quit)
    if key in ARROWS:
        pressed.add(ARROWS[key])


def on_release(key):
    """Handle key release events."""
    if key in ARROWS:
        pressed.discard(ARROWS[key])


def main():
    print("Arrow keys control the robot (Esc to quit)")

    controller = RoboteqCanController(nodeID=3, interface="can1")

    try:
        listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        listener.start()

        while listener.is_alive():
            update_speed(controller)
            time.sleep(0.05)  # 20 Hz update loop

    finally:
        controller.setSpeed(0, channel=2)
        controller.setSpeed(0, channel=1)
        controller.close()
        print("\nController stopped and closed.")


if __name__ == "__main__":
    main()
