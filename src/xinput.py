import logging
import math
import threading

from inputs import get_gamepad, UnpluggedError


class XInputController:
    MAX_TRIG_VAL = math.pow(2, 8)
    MAX_JOY_VAL = math.pow(2, 15)

    def __init__(self, config: dict, deadzone=0.2):
        self.config = config
        self.deadzone = deadzone

        self.LeftJoystickY = 0.0
        self.LeftJoystickX = 0.0
        self.RightJoystickY = 0.0
        self.RightJoystickX = 0.0
        self.LeftTrigger = 0.0
        self.RightTrigger = 0.0
        self.LeftBumper = False
        self.RightBumper = False
        self.A = False
        self.X = False
        self.Y = False
        self.B = False
        self.LeftThumb = False
        self.RightThumb = False
        self.Back = False
        self.Start = False
        self.LeftDPad = False
        self.RightDPad = False
        self.UpDPad = False
        self.DownDPad = False
        self.DPadX = 0.0
        self.DPadY = 0.0

        self.is_plugged = True

        self._monitor_thread = threading.Thread(
            target=self._monitor_controller, args=()
        )
        self._monitor_thread.daemon = True
        self._monitor_thread.start()

    def _monitor_controller(self):
        while True:
            self.poll_next_events()

    def normalize_joy(self, v):
        # normalize between -1 and 1
        return v / XInputController.MAX_JOY_VAL

    def normalize_trigger(self, v):
        # normalize between -1 and 1
        return v / XInputController.MAX_TRIG_VAL

    def poll_next_events(self):
        try:
            events = get_gamepad()
            self.is_plugged = True
            for event in events:
                if event.code == "ABS_Y":
                    self.LeftJoystickY = self.normalize_joy(event.state)
                elif event.code == "ABS_X":
                    self.LeftJoystickX = self.normalize_joy(event.state)
                elif event.code == "ABS_RY":
                    self.RightJoystickY = self.normalize_joy(event.state)
                elif event.code == "ABS_RX":
                    self.RightJoystickX = self.normalize_joy(event.state)
                elif event.code == "ABS_Z":
                    self.LeftTrigger = self.normalize_trigger(event.state)
                elif event.code == "ABS_RZ":
                    self.RightTrigger = self.normalize_trigger(event.state)
                elif event.code == "BTN_TL":
                    self.LeftBumper = bool(event.state)
                elif event.code == "BTN_TR":
                    self.RightBumper = bool(event.state)
                elif event.code == "BTN_SOUTH":
                    self.A = bool(event.state)
                elif event.code == "BTN_NORTH":
                    self.Y = bool(event.state)  # previously switched with X
                elif event.code == "BTN_WEST":
                    self.X = bool(event.state)  # previously switched with Y
                elif event.code == "BTN_EAST":
                    self.B = bool(event.state)
                elif event.code == "BTN_THUMBL":
                    self.LeftThumb = bool(event.state)
                elif event.code == "BTN_THUMBR":
                    self.RightThumb = bool(event.state)
                elif event.code == "BTN_SELECT":
                    self.Back = bool(event.state)
                elif event.code == "BTN_START":
                    self.Start = bool(event.state)
                elif event.code == "BTN_TRIGGER_HAPPY1":
                    self.LeftDPad = bool(event.state)
                elif event.code == "BTN_TRIGGER_HAPPY2":
                    self.RightDPad = bool(event.state)
                elif event.code == "BTN_TRIGGER_HAPPY3":
                    self.UpDPad = bool(event.state)
                elif event.code == "BTN_TRIGGER_HAPPY4":
                    self.DownDPad = bool(event.state)
                elif event.code == "ABS_HAT0X":
                    self.DPadX = event.state
                    if event.state == 1:
                        self.LeftDPad = False
                        self.RightDPad = True
                    elif event.state == -1:
                        self.LeftDPad = True
                        self.RightDPad = False
                    else:
                        self.LeftDPad = False
                        self.RightDPad = False
                elif event.code == "ABS_HAT0Y":
                    self.DPadY = -event.state  # set upwards positive
                    if event.state == 1:
                        self.UpDPad = False
                        self.DownDPad = True
                    elif event.state == -1:
                        self.UpDPad = True
                        self.DownDPad = False
                    else:
                        self.UpDPad = False
                        self.DownDPad = False
                elif event.code != "SYN_REPORT":
                    logging.error(f"Event code not found: {event.code}")
        except UnpluggedError:
            self.is_plugged = False

    def get_value(self, action: dict):
        name = action["name"]
        if hasattr(self, name):
            return getattr(self, name)
        elif name == "LeftJoystickXY":
            return dz_scaled_radial(
                self.LeftJoystickX, self.LeftJoystickY, self.deadzone
            )
        elif name == "RightJoystickXY":
            return dz_scaled_radial(
                self.RightJoystickX, self.RightJoystickY, self.deadzone
            )
        elif name == "DPadXY":
            return float(self.DPadX), float(self.DPadY)
        else:
            raise ValueError(f"Value for {name} not found.")


def map_range(v, old_min, old_max, new_min, new_max):
    return new_min + (new_max - new_min) * (v - old_min) / (old_max - old_min)


def dz_scaled_radial(x: float, y: float, deadzone: float) -> tuple[float, float]:
    input_magnitude = math.sqrt(x**2 + y**2)
    if input_magnitude < deadzone:
        return 0.0, 0.0
    else:
        x_normalized = x / input_magnitude
        y_normalized = y / input_magnitude
        # Formula:
        # max_value = 1
        # min_value = 0
        # retval = input_normalized * (min_value + (max_value - min_value) * ((input_magnitude - deadzone) / (max_value - deadzone)))
        mapped_magnitude = map_range(input_magnitude, deadzone, 1, 0, 1)
        new_x = x_normalized * mapped_magnitude
        new_y = y_normalized * mapped_magnitude
        return new_x, new_y
