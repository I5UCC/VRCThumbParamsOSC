import json
import openvr
import sys
import os
import time
import traceback
import ctypes
import argparse
import zeroconf
from pythonosc import udp_client, dispatcher, osc_server
from tinyoscquery.queryservice import OSCQueryService
from tinyoscquery.utility import get_open_tcp_port, get_open_udp_port, check_if_tcp_port_open, check_if_udp_port_open
from tinyoscquery.query import OSCQueryBrowser, OSCQueryClient
from psutil import process_iter
from threading import Thread


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


def is_running() -> bool:
    """
    Checks if VRChat is running.
    Returns:
        bool: True if VRChat is running, False if not
    """
    _proc_name = "VRChat.exe" if os.name == 'nt' else "VRChat"
    return _proc_name in (p.name() for p in process_iter())


def wait_get_oscquery_client() -> OSCQueryClient:
    """
    Waits for VRChat to be discovered and ready and returns the OSCQueryClient.
    Returns:
        OSCQueryClient: OSCQueryClient for VRChat
    """
    service_info = None
    print("Waiting for VRChat to be discovered.")
    while service_info is None:
        browser = OSCQueryBrowser()
        time.sleep(2) # Wait for discovery
        service_info = browser.find_service_by_name("VRChat")
    print("VRChat discovered!")
    client = OSCQueryClient(service_info)
    print("Waiting for VRChat to be ready.")
    while client.query_node(AVATAR_CHANGE_PARAMETER) is None:
        time.sleep(2)
    print("VRChat ready!")
    return client


def osc_server_serve() -> None:
    """
    Starts the OSC server.
    Returns:
        None
    """
    print(f"Starting OSC client on {IP}:{SERVER_PORT}:{HTTP_PORT}")
    server.serve_forever(2)


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
    global curr_avatar

    if curr_avatar == value:
        return
    
    curr_avatar = value

    if config["ControllerType"]["enabled"]:
        send_parameter("ControllerType", config["ControllerType"]["last_value"])
    if config["LeftThumb"]["enabled"]:
        send_parameter("LeftThumb", config["LeftThumb"]["last_value"])
    if config["RightThumb"]["enabled"]:
        send_parameter("RightThumb", config["RightThumb"]["last_value"])
    if config["LeftABButtons"]["enabled"]:
        send_parameter("LeftABButtons", config["LeftABButtons"]["last_value"])
    if config["RightABButtons"]["enabled"]:
        send_parameter("RightABButtons", config["RightABButtons"]["last_value"])

    for action in actions:
        send_osc(action, action["last_value"])


def send_parameter(parameter: str, value) -> None:
    """
    Sends a parameter to VRChat via OSC.
    Parameters:
        parameter (str): Name of the parameter
        value (any): Value of the parameter
        floating (str): Floating value of the parameter, just for for debug output
    Returns:
        None
    """
    oscClient.send_message(AVATAR_PARAMETERS_PREFIX + parameter, value)


def send_boolean_toggle(action: dict, value: bool) -> None:
    """
    Sends a boolean action as a toggle to VRChat via OSC.
    Parameters:
        action (dict): Action
        value (bool): Value of the parameter
    Returns:
        None
    """
    if not action["enabled"]:
        return
    
    if value:
        action["last_value"] = not action["last_value"]
        time.sleep(0.1)
        send_parameter(action["osc_parameter"], action["last_value"])
        return
    
    if action["always"]:
        send_parameter(action["osc_parameter"], action["last_value"])


def send_boolean(action: dict, value: bool) -> None:
    """
    Sends a boolean action to VRChat via OSC.
    Parameters:
        action (dict): Action
        value (bool): Value of the parameter
    Returns:
        None
    """
    global curr_time

    if not action["enabled"] or (not action["always"] and action["last_value"] == value):
        return

    if action["floating"]:
        if value:
            action["timestamp"] = curr_time
        elif not value and curr_time - action["timestamp"] <= action["floating"]: 
            value = action["last_value"]
    
    if not action["always"]:
        action["last_value"] = value
    else:
        send_parameter(action["osc_parameter"], value)


def send_vector1(action: dict, value: float) -> None:
    """
    Sends a vector1 action to VRChat via OSC.
    Parameters:
        action (dict): Action
        value (float): Value of the parameter
    Returns:
        None
    """
    global curr_time

    if not action["enabled"] or (not action["always"] and action["last_value"] == value):
        return
    
    if action["floating"]:
        if value > action["last_value"]:
            action["timestamp"] = curr_time
        elif value < action["last_value"] and curr_time - action["timestamp"] <= action["floating"]: 
            value = action["last_value"]

    if not action["always"]:
        action["last_value"] = value
    else:
        send_parameter(action["osc_parameter"], value)


def send_vector2(action: dict, value: tuple) -> None:
    """
    Sends a vector2 action to VRChat via OSC.
    Parameters:
        action (dict): Action
        value (tuple): X and Y value of the parameter in a tuple
    Returns:
        None
    """
    global curr_time

    val_x, val_y = value
    tmp = (val_x > STICKTOLERANCE or val_y > STICKTOLERANCE) or (val_x < -STICKTOLERANCE or val_y < -STICKTOLERANCE)

    if action["floating"]:
        if val_x:
            action["timestamp"][0] = curr_time
        elif not val_x and curr_time - action["timestamp"][0] <= action["floating"][0]: 
            val_x = action["last_value"][0]
        if val_y:
            action["timestamp"][1] = curr_time
        elif not val_y and curr_time - action["timestamp"][1] <= action["floating"][1]:
            val_y = action["last_value"][1]

    if not action["always"]:
        action["last_value"] = [val_x, val_y, tmp]

    if action["enabled"][0] and (action["always"][0] or action["last_value"][0] != val_x):
        send_parameter(action["osc_parameter"][0], val_x)
    if action["enabled"][1] and (action["always"][1] or action["last_value"][1] != val_y):
        send_parameter(action["osc_parameter"][1], val_y)
    if len(action["osc_parameter"]) > 2 and action["enabled"][2] and (action["always"][2] or action["last_value"][2] != tmp):
        send_parameter(action["osc_parameter"][2], tmp)


def send_osc(action: dict | str, value: bool | float | tuple) -> None:
    """
    Sends an OSC message to VRChat.
    Parameters:
        action (dict | str): Action or OSC address
        value (bool | float | tuple): Value of the parameter
    Returns:
        None
    """
    if isinstance(action, str):
        send_parameter(action, value)
        return
    
    match action['type']:
        case "boolean":
            if action["floating"] == -1:
                send_boolean_toggle(action, value)
            else:
                send_boolean(action, value)
        case "vector1":
            send_vector1(action, value)
        case "vector2":
            send_vector2(action, value)
        case _:
            raise TypeError("Unknown action type: " + action['type'])


def handle_input() -> None:
    """
    Handles SteamVR input and sends it to VRChat.
    Returns:
        None
    """
    global curr_time

    _event = openvr.VREvent_t()
    _has_events = True
    while _has_events:
        _has_events = application.pollNextEvent(_event)
    openvr.VRInput().updateActionState(actionsets)

    curr_time = time.time()

    if config["ControllerType"]["enabled"]:
        if curr_time - config["ControllerType"]["timestamp"] > 10.0:
            _controller_type = get_controllertype()
            config["ControllerType"]["timestamp"] = curr_time
            if config["ControllerType"]["last_value"] != _controller_type:
                send_osc("ControllerType", _controller_type)
            else:
                config["ControllerType"]["last_value"] = _controller_type

    _strinputs = ""
    for action in actions[:8]: # Touch Actions
        val = get_value(action)
        _strinputs += "1" if val else "0"
        send_osc(action, val)

    if config["LeftThumb"]["enabled"]:
        _leftthumb = _strinputs[:4].rfind("1") + 1
        if config["LeftThumb"]["last_value"] != _leftthumb or config["LeftThumb"]["always"]:
            send_osc("LeftThumb", _leftthumb)
        else:
            config["LeftThumb"]["last_value"] = _leftthumb

    if config["RightThumb"]["enabled"]:
        _rightthumb = _strinputs[4:].rfind("1") + 1
        if config["RightThumb"]["last_value"] != _rightthumb or config["RightThumb"]["always"]:
            send_osc("RightThumb", _rightthumb)
        else:
            config["RightThumb"]["last_value"] = _rightthumb

    if config["LeftABButtons"]["enabled"]:
        _leftab = _strinputs[0] == "1" and _strinputs[1] == "1"
        if config["LeftABButtons"]["last_value"] != _leftab or config["LeftABButtons"]["always"]:
            send_osc("LeftABButtons", _leftab)
        else:
            config["LeftABButtons"]["last_value"] = _leftab

    if config["RightABButtons"]["enabled"]:
        _rightab = _strinputs[4] == "1" and _strinputs[5] == "1"
        if config["RightABButtons"]["last_value"] != _rightab or config["RightABButtons"]["always"]:
            send_osc("RightABButtons", _rightab)
        else:
            config["RightABButtons"]["last_value"] = _rightab

    for action in actions[8:]:
        val = get_value(action)
        send_osc(action, val)

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

IP = args.ip if args.ip else config["IP"]
PORT = args.port if args.port else config["Port"]
SERVER_PORT = config["Server_Port"]
HTTP_PORT = config["HTTP_Port"]
POLLINGRATE = 1 / float(config['PollingRate'])
STICKTOLERANCE = int(config['StickMoveTolerance']) / 100
AVATAR_PARAMETERS_PREFIX = "/avatar/parameters/"
AVATAR_CHANGE_PARAMETER = "/avatar/change"

oscClient = udp_client.SimpleUDPClient(IP, PORT)

disp = dispatcher.Dispatcher()
disp.map(AVATAR_CHANGE_PARAMETER, set_avatar_change)

if SERVER_PORT != 9001:
    print("OSC Server port is not default, testing port availability and advertising OSCQuery endpoints")
    if SERVER_PORT <= 0 or not check_if_udp_port_open(SERVER_PORT):
        SERVER_PORT = get_open_udp_port()
    if HTTP_PORT <= 0 or not check_if_tcp_port_open(HTTP_PORT):
        HTTP_PORT = SERVER_PORT if check_if_tcp_port_open(SERVER_PORT) else get_open_tcp_port()
else:
    print("OSC Server port is default.")

try:
    print("Waiting for VRChat to start.")
    while not is_running():
        time.sleep(3)
    print("VRChat started!")
    qclient = wait_get_oscquery_client()
    curr_avatar = qclient.query_node(AVATAR_CHANGE_PARAMETER).value[0]
    server = osc_server.ThreadingOSCUDPServer((IP, SERVER_PORT), disp)
    server_thread = Thread(target=osc_server_serve, daemon=True)
    server_thread.start()
    oscqs = OSCQueryService("ThumbParamsOSC", HTTP_PORT, SERVER_PORT)
    oscqs.advertise_endpoint(AVATAR_CHANGE_PARAMETER, access="readwrite")
except OSError as e:
    print("You can only bind to the port 9001 once.")
    print(traceback.format_exc())
    if os.name == "nt":
        ctypes.windll.user32.MessageBoxW(0, "You can only bind to the port 9001 once.", "AvatarParameterSync - Error", 0)
    sys.exit(1)
except zeroconf._exceptions.NonUniqueNameException as e:
    print.error("NonUniqueNameException, trying again...")
    os.execv(sys.executable, ['python'] + sys.argv)

cls()
if not args.debug:
    print("ThumbParamsOSC running...\n")
    print("You can minimize this window.\n")
    print("Press CTRL+C to exit.\n")
    print(f"IP:\t\t\t{IP}")
    print(f"Port:\t\t\t{PORT}")
    print(f"PollingRate:\t\t{POLLINGRATE}s ({config['PollingRate']} Hz)")
    print(f"StickMoveTolerance:\t{STICKTOLERANCE} ({config['StickMoveTolerance']}%)")
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
