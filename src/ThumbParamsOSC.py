import json
import openvr
import sys
import os
import time
import traceback
import ctypes
import argparse
from osc import OSC


def get_absolute_path(relative_path) -> str:
    """
    Gets absolute path from relative path
    Parameters:
        relative_path (str): Relative path
    Returns:
        str: Absolute path
    """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def cls() -> None:
    """
    Clears Console.
    Returns:
        None
    """
    os.system('cls' if os.name == 'nt' else 'clear')


def get_debug_string(parameter, value, floating="", always = False) -> str:
    """
    Gets a string for the debug output.
    Parameters:
        parameter (str): Name of the parameter
        value (any): Value of the parameter
        floating (str): Floating value of the parameter
    Returns:
        str: Debug output string
    """
    if isinstance(value, float):
        value = f"{value:.4f}"

    tmp = ""
    if floating != "" and float(floating) > 0:
        tmp = f"Floating: {floating}s"
    tmp2 = ""
    if always:
        tmp2 = "-Always send-"
    return f"{parameter.ljust(23, ' ')}\t{str(value).ljust(10, ' ')}\t{tmp}\t{tmp2}\n"


def print_debugoutput() -> None:
    """
    Prints the debugoutput string.
    Returns:
        None
    """
    _debugoutput = ""
    cls()

    if config["ControllerType"]["enabled"]:
        _debugoutput += get_debug_string("ControllerType", config["ControllerType"]["last_value"], "", config["ControllerType"]["always"])
    if config["LeftThumb"]["enabled"]:
        _debugoutput += get_debug_string("LeftThumb", config["LeftThumb"]["last_value"], "", config["LeftThumb"]["always"])
    if config["RightThumb"]["enabled"]:
        _debugoutput += get_debug_string("RightThumb", config["RightThumb"]["last_value"], "", config["RightThumb"]["always"])
    if config["LeftABButtons"]["enabled"]:
        _debugoutput += get_debug_string("LeftABButtons", config["LeftABButtons"]["last_value"], "", config["LeftABButtons"]["always"])
    if config["RightABButtons"]["enabled"]:
        _debugoutput += get_debug_string("RightABButtons", config["RightABButtons"]["last_value"], "", config["RightABButtons"]["always"])

    for action in actions:
        if action["enabled"]:
            if action["type"] == "vector2":
                _debugoutput += get_debug_string(action["osc_parameter"][0], action["last_value"][0], action["floating"][0], action["always"][0])
                _debugoutput += get_debug_string(action["osc_parameter"][1], action["last_value"][1], action["floating"][1], action["always"][1])
                if len(action["osc_parameter"]) > 2:
                    _debugoutput += get_debug_string(action["osc_parameter"][2], action["last_value"][2], action["floating"][2], action["always"][2])
            else:
                _debugoutput += get_debug_string(action["osc_parameter"], action["last_value"], action["floating"], action["always"])

    print(_debugoutput)


def get_value(action: dict) -> bool | float | tuple:
    """
    Gets the value of an action by querying SteamVR.
    Parameters:
        action (dict): Action
    Returns:
        any: Value of the action
    """
    match action['type']:
        case "boolean":
            return bool(openvr.VRInput().getDigitalActionData(action['handle'], openvr.k_ulInvalidInputValueHandle).bState)
        case "vector1":
            return float(openvr.VRInput().getAnalogActionData(action['handle'], openvr.k_ulInvalidInputValueHandle).x)
        case "vector2":
            tmp = openvr.VRInput().getAnalogActionData(action['handle'], openvr.k_ulInvalidInputValueHandle)
            return tmp.x, tmp.y
        case _:
            raise TypeError("Unknown action type: " + action['type'])


def get_controllertype() -> int:
    """
    Gets the type of controller from SteamVR.
    Returns:
        int: Type of controller (0 = Unknown, 1 = Knuckles, 2 = Oculus/Meta Touch)
    """
    for i in range(1, openvr.k_unMaxTrackedDeviceCount):
        device_class = openvr.VRSystem().getTrackedDeviceClass(i)
        if device_class == 2:
            match openvr.VRSystem().getStringTrackedDeviceProperty(i, openvr.Prop_ControllerType_String):
                case 'knuckles':
                    return 1
                case 'oculus_touch':
                    return 2
                case _:
                    return 0
    return 0


def set_avatar_change(addr, value) -> None:
    """
    Sends all the last values to VRChat via OSC after the avatar has changed.
    Parameters:
        addr (str): OSC address
        value (any): Value of the parameter
    Returns:
        None
    """
    global osc

    if osc.curr_avatar == value:
        return
    
    osc.curr_avatar = value

    if config["ControllerType"]["enabled"]:
        osc.send("ControllerType", config["ControllerType"]["last_value"])
    if config["LeftThumb"]["enabled"]:
        osc.send("LeftThumb", config["LeftThumb"]["last_value"])
    if config["RightThumb"]["enabled"]:
        osc.send("RightThumb", config["RightThumb"]["last_value"])
    if config["LeftABButtons"]["enabled"]:
        osc.send("LeftABButtons", config["LeftABButtons"]["last_value"])
    if config["RightABButtons"]["enabled"]:
        osc.send("RightABButtons", config["RightABButtons"]["last_value"])

    for action in actions:
        osc.send(action, action["last_value"])


def handle_input() -> None:
    """
    Handles SteamVR input and sends it to VRChat.
    Returns:
        None
    """

    _event = openvr.VREvent_t()
    _has_events = True
    while _has_events:
        _has_events = application.pollNextEvent(_event)
    openvr.VRInput().updateActionState(actionsets)

    osc.refresh_time()

    if config["ControllerType"]["enabled"]:
        if osc.curr_time - config["ControllerType"]["timestamp"] > 10.0:
            _controller_type = get_controllertype()
            config["ControllerType"]["timestamp"] = osc.curr_time
            if config["ControllerType"]["last_value"] != _controller_type:
                osc.send("ControllerType", _controller_type)
            else:
                config["ControllerType"]["last_value"] = _controller_type

    _strinputs = ""
    for action in actions[:8]: # Touch Actions
        val = get_value(action)
        _strinputs += "1" if val else "0"
        osc.send(action, val)

    if config["LeftThumb"]["enabled"]:
        _leftthumb = _strinputs[:4].rfind("1") + 1
        if config["LeftThumb"]["last_value"] != _leftthumb or config["LeftThumb"]["always"]:
            osc.send("LeftThumb", _leftthumb)
        else:
            config["LeftThumb"]["last_value"] = _leftthumb

    if config["RightThumb"]["enabled"]:
        _rightthumb = _strinputs[4:].rfind("1") + 1
        if config["RightThumb"]["last_value"] != _rightthumb or config["RightThumb"]["always"]:
            osc.send("RightThumb", _rightthumb)
        else:
            config["RightThumb"]["last_value"] = _rightthumb

    if config["LeftABButtons"]["enabled"]:
        _leftab = _strinputs[0] == "1" and _strinputs[1] == "1"
        if config["LeftABButtons"]["last_value"] != _leftab or config["LeftABButtons"]["always"]:
            osc.send("LeftABButtons", _leftab)
        else:
            config["LeftABButtons"]["last_value"] = _leftab

    if config["RightABButtons"]["enabled"]:
        _rightab = _strinputs[4] == "1" and _strinputs[5] == "1"
        if config["RightABButtons"]["last_value"] != _rightab or config["RightABButtons"]["always"]:
            osc.send("RightABButtons", _rightab)
        else:
            config["RightABButtons"]["last_value"] = _rightab

    for action in actions[8:]:
        val = get_value(action)
        osc.send(action, val)

    if args.debug:
        print_debugoutput()


# Argument Parser
parser = argparse.ArgumentParser(description='ThumbParamsOSC: Takes button data from SteamVR and sends it to an OSC-Client')
parser.add_argument('-d', '--debug', required=False, action='store_true', help='prints values for debugging')
parser.add_argument('-i', '--ip', required=False, type=str, help="set OSC ip. Default=127.0.0.1")
parser.add_argument('-p', '--port', required=False, type=str, help="set OSC port. Default=9000")
args = parser.parse_args()

if os.name == 'nt':
    ctypes.windll.kernel32.SetConsoleTitleW("ThumbParamsOSC v1.3.2" + (" (Debug)" if args.debug else ""))

first_launch_file = get_absolute_path("bindings/first_launch")
config_path = get_absolute_path('config.json')
manifest_path = get_absolute_path("app.vrmanifest")
application = openvr.init(openvr.VRApplication_Utility)
openvr.VRInput().setActionManifestPath(config_path)
openvr.VRApplications().addApplicationManifest(manifest_path)
if os.path.isfile(first_launch_file):
    openvr.VRApplications().setApplicationAutoLaunch("i5ucc.thumbparamsosc", True)
    os.remove(first_launch_file)
action_set_handle = openvr.VRInput().getActionSetHandle("/actions/thumbparams")
actionsets = (openvr.VRActiveActionSet_t * 1)()
actionset = actionsets[0]
actionset.ulActionSet = action_set_handle

config = json.load(open(config_path))
actions = config["actions"]
for action in actions:
    action["handle"] = openvr.VRInput().getActionHandle(action['name'])

config["IP"] = args.ip if args.ip else config["IP"]
config["Port"] = args.port if args.port else config["Port"]
POLLINGRATE = 1 / float(config['PollingRate'])
osc = OSC(config, set_avatar_change)

cls()
if not args.debug:
    print("ThumbParamsOSC running...\n")
    print("You can minimize this window.\n")
    print("Press CTRL+C to exit.\n")
    print(f"IP:\t\t\t{osc.ip}")
    print(f"Port:\t\t\t{osc.port}")
    print(f"Server Port:\t\t{osc.server_port}")
    print(f"HTTP Port:\t\t{osc.http_port}")
    print(f"PollingRate:\t\t{POLLINGRATE}s ({config['PollingRate']} Hz)")
    print(f"StickMoveTolerance:\t{osc.stick_tolerance} ({config['StickMoveTolerance']}%)")
    print("\nOpen Configurator.exe to change sent Parameters and other Settings.")

# Main Loop
while True:
    try:
        handle_input()
        time.sleep(POLLINGRATE)
    except KeyboardInterrupt:
        cls()
        sys.exit()
    except Exception:
        cls()
        print("UNEXPECTED ERROR\n")
        print("Please Create an Issue on GitHub with the following information:\n")
        traceback.print_exc()
        input("\nPress ENTER to exit")
        sys.exit()
