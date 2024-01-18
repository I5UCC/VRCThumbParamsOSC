import logging
import math
import threading

from inputs import get_gamepad, UnpluggedError


class XInputController:
    """
    A class to represent an XInput Controller.

    Attributes:
    ----------
    MAX_TRIG_VAL : float
        The maximum value for the trigger.
    MAX_JOY_VAL : float
        The maximum value for the joystick.
    config : dict
        The configuration dictionary.
    deadzone : float
        The deadzone for the joystick.
    is_plugged : bool
        The state of the controller's connection.
    _monitor_thread : threading.Thread
        The thread that monitors the controller's input.

    Methods:
    -------
    _monitor_controller():
        Monitors the controller's input in a loop.
    normalize_joy(v: float) -> float:
        Normalizes the joystick value between -1 and 1.
    normalize_trigger(v: float) -> float:
        Normalizes the trigger value between 0 and 1.
    poll_next_events():
        Polls the next events from the gamepad.
    get_value(action: dict):
        Retrieves the value of a specified action.
    """
    MAX_TRIG_VAL = math.pow(2, 8)
    MAX_JOY_VAL = math.pow(2, 15)

    def __init__(self, config: dict, deadzone=0.2):
        """
        Constructs all the necessary attributes for the XInputController object.

        Parameters:
        ----------
            config : dict
                The configuration dictionary.
            deadzone : float, optional
                The deadzone for the joystick (default is 0.2).
        """
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

        self.event_actions = {
            "ABS_Y": ("LeftJoystickY", self.normalize_joy),
            "ABS_X": ("LeftJoystickX", self.normalize_joy),
            "ABS_RY": ("RightJoystickY", self.normalize_joy),
            "ABS_RX": ("RightJoystickX", self.normalize_joy),
            "ABS_Z": ("LeftTrigger", self.normalize_trigger),
            "ABS_RZ": ("RightTrigger", self.normalize_trigger),
            "BTN_TL": ("LeftBumper", bool),
            "BTN_TR": ("RightBumper", bool),
            "BTN_SOUTH": ("A", bool),
            "BTN_NORTH": ("Y", bool),
            "BTN_WEST": ("X", bool),
            "BTN_EAST": ("B", bool),
            "BTN_THUMBL": ("LeftThumb", bool),
            "BTN_THUMBR": ("RightThumb", bool),
            "BTN_SELECT": ("Back", bool),
            "BTN_START": ("Start", bool),
            "BTN_TRIGGER_HAPPY1": ("LeftDPad", bool),
            "BTN_TRIGGER_HAPPY2": ("RightDPad", bool),
            "BTN_TRIGGER_HAPPY3": ("UpDPad", bool),
            "BTN_TRIGGER_HAPPY4": ("DownDPad", bool),
        }

        self.is_plugged = True

        self._monitor_thread = threading.Thread(
            target=self._monitor_controller, args=()
        )
        self._monitor_thread.daemon = True
        self._monitor_thread.start()

    def _monitor_controller(self) -> None:
        """
        Monitors the controller's input in a loop.
        """
        while True:
            self.poll_next_events()

    def normalize_joy(self, v) -> float:
        """
        Normalizes the joystick value between -1 and 1.

        Parameters:
        ----------
            v : float
                The joystick value.

        Returns:
        -------
            float
                The normalized joystick value.
        """
        return v / XInputController.MAX_JOY_VAL

    def normalize_trigger(self, v) -> float:
        """
        Normalizes the trigger value between 0 and 1.

        Parameters:
        ----------
            v : float
                The trigger value.

        Returns:
        -------
            float
                The normalized trigger value.
        """
        return v / XInputController.MAX_TRIG_VAL

    def poll_next_events(self) -> None:
        """
        Polls the next events from the gamepad.

        This method retrieves the next events from the gamepad, normalizes the joystick and trigger values, 
        and sets the corresponding attributes on the XInputController object. If the gamepad is unplugged, 
        it sets the is_plugged attribute to False.
        """
        try:
            events = get_gamepad()
            self.is_plugged = True

            for event in events:
                action = self.event_actions.get(event.code)
                if action:
                    setattr(self, action[0], action[1](event.state))
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

    def get_value(self, action: dict) -> float:
        """
        Retrieves the value of a specified action.

        Parameters:
        ----------
            action : dict
                The action to retrieve the value for.

        Returns:
        -------
            The value of the action. If the action is a joystick or DPad action, it returns a tuple of two floats. 
            If the action is not found, it raises a ValueError.
        """
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


def map_range(v, old_min, old_max, new_min, new_max) -> float:
    """
    Maps a value from one range to another.

    Parameters:
    ----------
        v : float
            The value to map.
        old_min : float
            The minimum value of the old range.
        old_max : float
            The maximum value of the old range.
        new_min : float
            The minimum value of the new range.
        new_max : float
            The maximum value of the new range.

    Returns:
    -------
        float
            The value mapped to the new range.
    """
    return new_min + (new_max - new_min) * (v - old_min) / (old_max - old_min)


def dz_scaled_radial(x: float, y: float, deadzone: float) -> tuple[float, float]:
    """
    Scales the input values radially based on a deadzone.

    Parameters:
    ----------
        x : float
            The X value of the input.
        y : float
            The Y value of the input.
        deadzone : float
            The deadzone.

    Returns:
    -------
        tuple[float, float]
            The scaled X and Y values.
    """
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
