import logging
import math
import threading

from inputs import get_gamepad, UnpluggedError


class XInputController:
    MAX_TRIG_VAL = math.pow(2, 8)
    MAX_JOY_VAL = math.pow(2, 15)

    def __init__(self, config: dict):
        self.config = config

        self.LeftJoystickY = 0
        self.LeftJoystickX = 0
        self.RightJoystickY = 0
        self.RightJoystickX = 0
        self.LeftTrigger = 0
        self.RightTrigger = 0
        self.LeftBumper = 0
        self.RightBumper = 0
        self.A = 0
        self.X = 0
        self.Y = 0
        self.B = 0
        self.LeftThumb = 0
        self.RightThumb = 0
        self.Back = 0
        self.Start = 0
        self.LeftDPad = 0
        self.RightDPad = 0
        self.UpDPad = 0
        self.DownDPad = 0
        self.DPadX = 0
        self.DPadY = 0

        self.is_plugged = True

        self._monitor_thread = threading.Thread(
            target=self._monitor_controller, args=()
        )
        self._monitor_thread.daemon = True
        self._monitor_thread.start()

    def read(self):  # return the buttons/triggers that you care about in this methode
        x = self.LeftJoystickX
        y = self.LeftJoystickY
        a = self.A
        b = self.X  # b=1, x=2
        rb = self.RightBumper
        return [x, y, a, b, rb]

    def _monitor_controller(self):
        while True:
            self.poll_next_events()

    def poll_next_events(self):
        try:
            events = get_gamepad()
            self.is_plugged = True
            for event in events:
                if event.code == "ABS_Y":
                    self.LeftJoystickY = round(
                        event.state / XInputController.MAX_JOY_VAL, 4
                    )  # normalize between -1 and 1
                elif event.code == "ABS_X":
                    self.LeftJoystickX = round(
                        event.state / XInputController.MAX_JOY_VAL, 4
                    )  # normalize between -1 and 1
                elif event.code == "ABS_RY":
                    self.RightJoystickY = round(
                        event.state / XInputController.MAX_JOY_VAL, 4
                    )  # normalize between -1 and 1
                elif event.code == "ABS_RX":
                    self.RightJoystickX = round(
                        event.state / XInputController.MAX_JOY_VAL, 4
                    )  # normalize between -1 and 1
                elif event.code == "ABS_Z":
                    self.LeftTrigger = round(
                        event.state / XInputController.MAX_TRIG_VAL, 4
                    )  # normalize between 0 and 1
                elif event.code == "ABS_RZ":
                    self.RightTrigger = round(
                        event.state / XInputController.MAX_TRIG_VAL, 4
                    )  # normalize between 0 and 1
                elif event.code == "BTN_TL":
                    self.LeftBumper = event.state
                elif event.code == "BTN_TR":
                    self.RightBumper = event.state
                elif event.code == "BTN_SOUTH":
                    self.A = event.state
                elif event.code == "BTN_NORTH":
                    self.Y = event.state  # previously switched with X
                elif event.code == "BTN_WEST":
                    self.X = event.state  # previously switched with Y
                elif event.code == "BTN_EAST":
                    self.B = event.state
                elif event.code == "BTN_THUMBL":
                    self.LeftThumb = event.state
                elif event.code == "BTN_THUMBR":
                    self.RightThumb = event.state
                elif event.code == "BTN_SELECT":
                    self.Back = event.state
                elif event.code == "BTN_START":
                    self.Start = event.state
                elif event.code == "BTN_TRIGGER_HAPPY1":
                    self.LeftDPad = event.state
                elif event.code == "BTN_TRIGGER_HAPPY2":
                    self.RightDPad = event.state
                elif event.code == "BTN_TRIGGER_HAPPY3":
                    self.UpDPad = event.state
                elif event.code == "BTN_TRIGGER_HAPPY4":
                    self.DownDPad = event.state
                elif event.code == "ABS_HAT0X":
                    self.DPadX = event.state
                    if event.state == 1:
                        self.LeftDPad = 0
                        self.RightDPad = 1
                    elif event.state == -1:
                        self.LeftDPad = 1
                        self.RightDPad = 0
                    else:
                        self.LeftDPad = 0
                        self.RightDPad = 0
                elif event.code == "ABS_HAT0Y":
                    self.DPadY = -event.state  # set upwards positive
                    if event.state == 1:
                        self.UpDPad = 0
                        self.DownDPad = 1
                    elif event.state == -1:
                        self.UpDPad = 1
                        self.DownDPad = 0
                    else:
                        self.UpDPad = 0
                        self.DownDPad = 0
                elif event.code != "SYN_REPORT":
                    logging.error(f"Event code not found: {event.code}")
        except UnpluggedError:
            self.is_plugged = False

    def get_value(self, action: dict):
        name = action["name"]
        if hasattr(self, name):
            return getattr(self, name)
        elif name == "LeftJoystickXY":
            return self.LeftJoystickX, self.LeftJoystickY
        elif name == "RightJoystickXY":
            return self.RightJoystickX, self.RightJoystickY
        elif name == "DPadXY":
            return self.DPadX, self.DPadY
        else:
            raise ValueError(f"Value for {name} not found.")
