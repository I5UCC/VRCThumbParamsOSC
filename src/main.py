import json
import sys
import os
import time
import traceback
import ctypes
import argparse
from osc import OSC
from ovr import OVR
from zeroconf._exceptions import NonUniqueNameException


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

    for action in config["actions"]:
        if action["enabled"]:
            if action["type"] == "vector2":
                _debugoutput += get_debug_string(action["osc_parameter"][0], action["last_value"][0], action["floating"][0], action["always"][0])
                _debugoutput += get_debug_string(action["osc_parameter"][1], action["last_value"][1], action["floating"][1], action["always"][1])
                if len(action["osc_parameter"]) > 2:
                    _debugoutput += get_debug_string(action["osc_parameter"][2], action["last_value"][2], action["floating"][2], action["always"][2])
            else:
                _debugoutput += get_debug_string(action["osc_parameter"], action["last_value"], action["floating"], action["always"])

    print(_debugoutput)


def resend_parameters(avatar_id) -> None:
    """
    Resends all parameters to the new avatar.
    Parameters:
        avatar_id (str): Avatar ID
    Returns:
        None
    """
    global osc

    if osc.curr_avatar == avatar_id:
        return
    
    osc.curr_avatar = avatar_id

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

    for action in config["actions"]:
        osc.send(action, action["last_value"])


def handle_input() -> None:
    """
    Handles SteamVR input and sends it to VRChat.
    Returns:
        None
    """

    ovr.poll_next_events()
    osc.refresh_time()

    if config["ControllerType"]["enabled"] and (osc.curr_time - config["ControllerType"]["timestamp"] > 10.0 or config["ControllerType"]["always"]):
        _controller_type = ovr.get_controllertype()
        config["ControllerType"]["timestamp"] = osc.curr_time
        if config["ControllerType"]["last_value"] != _controller_type or config["ControllerType"]["always"]:
            osc.send("ControllerType", _controller_type)
            config["ControllerType"]["last_value"] = _controller_type

    _strinputs = ""
    for action in config["actions"][:8]: # Touch Actions
        val = ovr.get_value(action)
        _strinputs += "1" if val else "0"
        osc.send(action, val)

    if config["LeftThumb"]["enabled"]:
        _leftthumb = _strinputs[:4].rfind("1") + 1
        if config["LeftThumb"]["last_value"] != _leftthumb or config["LeftThumb"]["always"]:
            osc.send("LeftThumb", _leftthumb)
            config["LeftThumb"]["last_value"] = _leftthumb

    if config["RightThumb"]["enabled"]:
        _rightthumb = _strinputs[4:].rfind("1") + 1
        if config["RightThumb"]["last_value"] != _rightthumb or config["RightThumb"]["always"]:
            osc.send("RightThumb", _rightthumb)
            config["RightThumb"]["last_value"] = _rightthumb

    if config["LeftABButtons"]["enabled"]:
        _leftab = _strinputs[0] == "1" and _strinputs[1] == "1"
        if config["LeftABButtons"]["last_value"] != _leftab or config["LeftABButtons"]["always"]:
            osc.send("LeftABButtons", _leftab)
            config["LeftABButtons"]["last_value"] = _leftab

    if config["RightABButtons"]["enabled"]:
        _rightab = _strinputs[4] == "1" and _strinputs[5] == "1"
        if config["RightABButtons"]["last_value"] != _rightab or config["RightABButtons"]["always"]:
            osc.send("RightABButtons", _rightab)
            config["RightABButtons"]["last_value"] = _rightab

    for action in config["actions"][8:]:
        val = ovr.get_value(action)
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

CONFIG_PATH = get_absolute_path('config.json')
MANIFEST_PATH = get_absolute_path("app.vrmanifest")
FIRST_LAUNCH_FILE = get_absolute_path("bindings/first_launch")
config = json.load(open(CONFIG_PATH))
config["IP"] = args.ip if args.ip else config["IP"]
config["Port"] = args.port if args.port else config["Port"]
POLLINGRATE = 1 / float(config['PollingRate'])

try:
    ovr = OVR(config, CONFIG_PATH, MANIFEST_PATH, FIRST_LAUNCH_FILE)
    osc = OSC(config, lambda addr, value: resend_parameters(value))
except OSError as e:
    print("You can only bind to the port 9001 once.")
    print(traceback.format_exc())
    if os.name == "nt":
        ctypes.windll.user32.MessageBoxW(0, "You can only bind to the port 9001 once.", "AvatarParameterSync - Error", 0)
    sys.exit(1)
except NonUniqueNameException as e:
    print.error("NonUniqueNameException, trying again...")
    os.execv(sys.executable, ['python'] + sys.argv)
except Exception as e:
    print("UNEXPECTED ERROR\n")
    print("Please Create an Issue on GitHub with the following information:\n")
    traceback.print_exc()
    input("\nPress ENTER to exit")
    sys.exit(1)

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
