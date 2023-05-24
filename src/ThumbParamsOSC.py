import json
import openvr
import sys
import os
import time
import traceback
import ctypes
import argparse
from pythonosc import udp_client


def get_absolute_path(relative_path):
    """Gets absolute path from relative path"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def cls():
    """Clears Console"""
    os.system('cls' if os.name == 'nt' else 'clear')


def get_value(action):
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


def get_controllertype():
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


def send_osc_message(parameter, value):
    oscClient.send_message("/avatar/parameters/" + parameter, value)


def add_to_debugoutput(parameter, value):
    global _debugoutput

    if isinstance(value, float):
        value = f"{value:.4f}"

    _debugoutput += f"{parameter.ljust(23, ' ')}\t{value}\n"


def handle_input():
    global _debugoutput
    
    _debugoutput = ""
    _event = openvr.VREvent_t()
    _has_events = True
    while _has_events:
        _has_events = application.pollNextEvent(_event)
    _actionsets = (openvr.VRActiveActionSet_t * 1)()
    _actionset = _actionsets[0]
    _actionset.ulActionSet = action_set_handle
    openvr.VRInput().updateActionState(_actionsets)

    if config["ControllerType"]:
        _controller_type = get_controllertype()
        add_to_debugoutput("ControllerType", _controller_type)
        send_osc_message("ControllerType", _controller_type)

    button_actions = actions[:8]
    _strinputs = ""
    for action in button_actions:
        if not action["enabled"]:
            continue
        val = get_value(action)
        add_to_debugoutput(action["osc_parameter"], val)
        send_osc_message(action["osc_parameter"], val)
        _strinputs += "1" if val else "0"
    if config["LeftThumb"]:
        _leftthumb = _strinputs[:4].rfind("1") + 1
        add_to_debugoutput("LeftThumb", _leftthumb)
        send_osc_message("LeftThumb", _leftthumb)
    if config["RightThumb"]:
        _rightthumb = _strinputs[4:].rfind("1") + 1
        add_to_debugoutput("RightThumb", _rightthumb)
        send_osc_message("RightThumb", _rightthumb)
    if config["LeftABButtons"]:
        _leftab = _strinputs[0] == "1" and _strinputs[1] == "1"
        add_to_debugoutput("LeftABButtons", _leftab)
        send_osc_message("LeftABButtons", _leftab)
    if config["RightABButtons"]:
        _rightab = _strinputs[4] == "1" and _strinputs[5] == "1"
        add_to_debugoutput("RightABButtons", _rightab)
        send_osc_message("RightABButtons", _rightab)

    click_actions = actions[8:16]
    for action in click_actions:
        if not action["enabled"]:
            continue
        val = get_value(action)
        add_to_debugoutput(action["osc_parameter"], val)
        send_osc_message(action["osc_parameter"], val)
    
    trigger_actions = actions[16:18]
    for action in trigger_actions:
        if not action["enabled"]:
            continue
        val = get_value(action)
        add_to_debugoutput(action["osc_parameter"], val)
        send_osc_message(action["osc_parameter"], val)
    
    position_actions = actions[18:]
    for action in position_actions:
        val_x, val_y = get_value(action)
        if action["enabled"][0]:
            add_to_debugoutput(action["osc_parameter"][0], val_x)
            send_osc_message(action["osc_parameter"][0], val_x)
        if action["enabled"][1]:
            add_to_debugoutput(action["osc_parameter"][1], val_y)
            send_osc_message(action["osc_parameter"][1], val_y)
        if len(action["osc_parameter"]) > 2 and action["enabled"][2]:
            tmp = (val_x > sticktolerance or val_y > sticktolerance)
            add_to_debugoutput(action["osc_parameter"][2], tmp)
            send_osc_message(action["osc_parameter"][2], tmp)
    
    if args.debug:
        cls()
        print(_debugoutput.strip())


# Argument Parser
parser = argparse.ArgumentParser(description='ThumbParamsOSC: Takes button data from SteamVR and sends it to an OSC-Client')
parser.add_argument('-d', '--debug', required=False, action='store_true', help='prints values for debugging')
parser.add_argument('-i', '--ip', required=False, type=str, help="set OSC ip. Default=127.0.0.1")
parser.add_argument('-p', '--port', required=False, type=str, help="set OSC port. Default=9000")
args = parser.parse_args()

if os.name == 'nt':
    ctypes.windll.kernel32.SetConsoleTitleW("ThumbParamsOSC - Debug" if args.debug else "ThumbParamsOSC")

config_path = get_absolute_path('config.json')
manifest_path = get_absolute_path("app.vrmanifest")

application = openvr.init(openvr.VRApplication_Utility)
openvr.VRInput().setActionManifestPath(config_path)
openvr.VRApplications().addApplicationManifest(manifest_path)
action_set_handle = openvr.VRInput().getActionSetHandle("/actions/thumbparams")

config = json.load(open(config_path))
actions = config["actions"]
for action in actions:
    action["handle"] = openvr.VRInput().getActionHandle(action['name'])
IP = args.ip if args.ip else config["IP"]
PORT = args.port if args.port else config["Port"]
oscClient = udp_client.SimpleUDPClient(IP, PORT)
pollingrate = 1 / float(config['PollingRate'])
sticktolerance = int(config['StickMoveTolerance']) / 100

cls()
if not args.debug:
    print("ThumbParamsOSC running...\n")
    print("You can minimize this window.\n")
    print("Press CTRL+C to exit.\n")
    print(f"IP:\t\t\t{IP}")
    print(f"Port:\t\t\t{PORT}")
    print(f"PollingRate:\t\t{pollingrate}s ({config['PollingRate']} Hz)")
    print(f"StickMoveTolerance:\t{sticktolerance} ({config['StickMoveTolerance']}%)")
    print("\nOpen Configurator.exe to change sent Parameters and other Settings.")

# Main Loop
while True:
    try:
        handle_input()
        time.sleep(pollingrate)
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
