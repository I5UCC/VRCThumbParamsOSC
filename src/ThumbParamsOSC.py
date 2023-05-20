import json
import openvr
import sys
import os
import time
import traceback
import ctypes
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
            return openvr.VRInput().getAnalogActionData(action['handle'], openvr.k_ulInvalidInputValueHandle)
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
    oscClient.send_message(osc_prefix + parameter, value)


def handle_input():
    _event = openvr.VREvent_t()
    _has_events = True
    while _has_events:
        _has_events = application.pollNextEvent(_event)
    _actionsets = (openvr.VRActiveActionSet_t * 1)()
    _actionset = _actionsets[0]
    _actionset.ulActionSet = action_set_handle
    openvr.VRInput().updateActionState(_actionsets)

    if config["SendControllerType"]:
        _controller_type = get_controllertype()
        print("ControllerType" + "\t\t\t\t" + str(_controller_type))
        send_osc_message("ControllerType", _controller_type)

    button_actions = actions[:8]
    _strinputs = ""
    for action in button_actions:
        if not action["enabled"]:
            continue
        val = get_value(action)
        print(action["osc_parameter"] + "\t\t\t\t" + str(val))
        send_osc_message(action["osc_parameter"], val)
        _strinputs += "1" if val else "0"
    if config["SendTouchParamsInt"]:
        _rightthumb = _strinputs[4:].rfind("1") + 1
        _leftthumb = _strinputs[:4].rfind("1") + 1
        print("LeftThumb" + "\t\t\t\t" + str(_leftthumb))
        print("RightThumb" + "\t\t\t\t" + str(_rightthumb))
        send_osc_message(left_thumb, _leftthumb)
        send_osc_message(right_thumb, _rightthumb)

    click_actions = actions[8:16]
    for action in click_actions:
        if not action["enabled"]:
            continue
        val = get_value(action)
        print(action["osc_parameter"] + "\t\t\t" + str(val))
        send_osc_message(action["osc_parameter"], val)
    
    trigger_actions = actions[16:18]
    for action in trigger_actions:
        if not action["enabled"]:
            continue
        val = get_value(action)
        print(action["osc_parameter"] + "\t\t\t\t" + f"{val:.4f}")
        send_osc_message(action["osc_parameter"], val)
    
    position_actions = actions[18:]
    for action in position_actions:
        val = get_value(action)
        if action["enabled"][0]:
            print(action["osc_parameter"][0] + "   \t\t\t" + f"{val.x:.4f}")
            send_osc_message(action["osc_parameter"][0], val.x)
        if action["enabled"][1]:
            print(action["osc_parameter"][1] + "   \t\t\t" + f"{val.y:.4f}")
            send_osc_message(action["osc_parameter"][1], val.y)
        if len(action["osc_parameter"]) > 2 and action["enabled"][2]:
            tmp = (val.x > sticktolerance or val.y > sticktolerance)
            print(action["osc_parameter"][2] + "   \t\t\t" + str(tmp))
            send_osc_message(action["osc_parameter"][2], tmp)


if os.name == 'nt':
    ctypes.windll.kernel32.SetConsoleTitleW("ThumbParamsOSC")

config_path = get_absolute_path('config.json')
config = json.load(open(config_path))
application = openvr.init(openvr.VRApplication_Utility)
openvr.VRInput().setActionManifestPath(config_path)
action_set_handle = openvr.VRInput().getActionSetHandle("/actions/thumbparams")
actions = config["actions"]
for action in actions:
    action["handle"] = openvr.VRInput().getActionHandle(action['name'])
oscClient = udp_client.SimpleUDPClient("127.0.0.1", 9000)
osc_prefix = "/avatar/parameters/"
pollingrate = 1 / float(config['PollingRate'])
sticktolerance = int(config['StickMoveTolerance']) / 100
left_thumb = osc_prefix + "LeftThumb"
right_thumb = osc_prefix + "RightThumb"

# Main Loop
while True:
    try:
        cls()
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
