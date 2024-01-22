import asyncio
import logging
import math
import time

from xinput_joystick import XInputJoystick

DEFAULT_ACTIONS = {
    "LeftJoystickY": 0.0,
    "LeftJoystickX": 0.0,
    "RightJoystickY": 0.0,
    "RightJoystickX": 0.0,
    "LeftTrigger": 0.0,
    "RightTrigger": 0.0,
    "LeftBumper": False,
    "RightBumper": False,
    "A": False,
    "X": False,
    "Y": False,
    "B": False,
    "LeftThumb": False,
    "RightThumb": False,
    "Back": False,
    "Start": False,
    "LeftDPad": False,
    "RightDPad": False,
    "UpDPad": False,
    "DownDPad": False,
}


def normalize_joy(v) -> float:
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
    return v / XboxController.MAX_JOY_VAL


def normalize_trigger(v) -> float:
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
    return v / XboxController.MAX_TRIG_VAL


axis_mapping = {
    "l_thumb_x": ("LeftJoystickX", normalize_joy),
    "l_thumb_y": ("LeftJoystickY", normalize_joy),
    "r_thumb_x": ("RightJoystickX", normalize_joy),
    "r_thumb_y": ("RightJoystickY", normalize_joy),
    "left_trigger": ("LeftTrigger", normalize_trigger),
    "right_trigger": ("RightTrigger", normalize_trigger),
}

button_mapping = {
    1: "UpDPad",
    2: "DownDPad",
    3: "LeftDPad",
    4: "RightDPad",
    5: "Start",
    6: "Back",
    7: "LeftThumb",
    8: "RightThumb",
    9: "LeftBumper",
    10: "RightBumper",
    13: "A",
    14: "B",
    15: "X",
    16: "Y",
}


class XboxController:
    MAX_TRIG_VAL = math.pow(2, 8)
    MAX_JOY_VAL = math.pow(2, 15)

    def __init__(self, polling_rate=1000, deadzone=0.2):
        self.polling_rate = polling_rate
        self.deadzone = deadzone
        self.actions = DEFAULT_ACTIONS
        self.running = True

        self.last_check = 0
        self.joystick = None
        self._init_joystick()

    @property
    def is_plugged(self):
        return (
            isinstance(self.joystick, XInputJoystick) and self.joystick.is_connected()
        )

    def _init_joystick(self):
        joysticks = XInputJoystick.enumerate_devices()
        if len(joysticks) > 0:
            self.joystick = joysticks[0]
        else:
            self.joystick = None
            return

        j = self.joystick

        @j.event
        def on_axis(axis, value):
            if axis in axis_mapping:
                mapping, func = axis_mapping[axis]
                self.actions[mapping] = func(value)
                logging.info(f"{mapping}: {self.actions[mapping]}")
            else:
                logging.warning(f"Axis not found: {axis} = {value}")

        @j.event
        def on_button(button, pressed):
            if button in button_mapping:
                self.actions[button_mapping[button]] = bool(pressed)
            else:
                logging.warning(f"Button not found: {button} = {pressed}")

    def poll(self):
        if not self.is_plugged:
            if time.time() - self.last_check > 10000:
                self._init_joystick()
                self.last_check = time.time()
        if self.is_plugged:
            self.joystick.dispatch_events()

    async def polling_loop(self):
        while self.running:
            self.poll()
            await asyncio.sleep(1 / self.polling_rate)

    def get_value(self, action: dict) -> bool | tuple[float, float]:
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
        if name in self.actions:
            return self.actions[name]
        elif name == "LeftJoystickXY":
            return dz_scaled_radial(
                self.actions["LeftJoystickX"],
                self.actions["LeftJoystickY"],
                self.deadzone,
            )
        elif name == "RightJoystickXY":
            return dz_scaled_radial(
                self.actions["RightJoystickX"],
                self.actions["RightJoystickY"],
                self.deadzone,
            )
        elif name == "DPadXY":
            x = -float(self.actions["LeftDPad"]) + float(self.actions["RightDPad"])
            y = -float(self.actions["DownDPad"]) + float(self.actions["UpDPad"])
            return x, y
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


def test_controller():
    controller = XboxController()
    asyncio.run(controller.polling_loop())


if __name__ == "__main__":
    test_controller()
