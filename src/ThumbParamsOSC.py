import json
import traceback
import openvr
import sys
import os
import time
import ctypes
import argparse
from pythonosc import udp_client

# Argument Parser
parser = argparse.ArgumentParser(description='ThumbParamsOSC: Takes button data from SteamVR and sends it to an OSC-Client')
parser.add_argument('-d', '--debug', required=False, action='store_true', help='prints values for debugging')
parser.add_argument('-i', '--ip', required=False, type=str, help="set OSC ip. Default=127.0.0.1")
parser.add_argument('-p', '--port', required=False, type=str, help="set OSC port. Default=9000")
args = parser.parse_args()


def move(y, x):
    """Moves console cursor."""
    print("\033[%d;%dH" % (y, x))


# Set window name on Windows
if os.name == 'nt':
    ctypes.windll.kernel32.SetConsoleTitleW("ThumbParamsOSC")


def cls():
    """Clears Console"""
    os.system('cls' if os.name == 'nt' else 'clear')


def resource_path(relative_path):
    """Gets absolute path from relative path"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


# load configs
config = json.load(open(resource_path('config.json')))
ovrConfig = json.load(open(resource_path('ovrConfig.json')))
IP = args.ip if args.ip else config["IP"]
PORT = args.port if args.port else config["Port"]
pollingrate = 1 / float(config['PollingRate'])
sticktolerance = int(config['StickMoveTolerance']) / 100

# Set up UDP OSC client
oscClient = udp_client.SimpleUDPClient(IP, PORT)

# Init OpenVR and Actionsets
application = openvr.init(openvr.VRApplication_Utility)
action_path = os.path.join(resource_path(ovrConfig["BindingsFolder"]), ovrConfig["ActionManifestFile"])
appmanifest_path = resource_path(ovrConfig["AppManifestFile"])
openvr.VRApplications().addApplicationManifest(appmanifest_path)
openvr.VRInput().setActionManifestPath(action_path)
actionSetHandle = openvr.VRInput().getActionSetHandle(ovrConfig["ActionSetHandle"])


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


# Set up OpenVR Action Handles
leftTrigger = openvr.VRInput().getActionHandle(ovrConfig["TriggerActions"]["lefttrigger"])
rightTrigger = openvr.VRInput().getActionHandle(ovrConfig["TriggerActions"]["righttrigger"])
buttonActionHandles = []
for k in ovrConfig["ButtonActions"]:
    buttonActionHandles.append(openvr.VRInput().getActionHandle(ovrConfig["ButtonActions"][k]))

leftxy = openvr.VRInput().getActionHandle(ovrConfig["StickActions"]["leftstickxy"])
rightxy = openvr.VRInput().getActionHandle(ovrConfig["StickActions"]["rightstickxy"])


def handle_input():
    """Handles all the OpenVR Input and sends it via OSC"""
    # Set up OpenVR events and Action sets
    event = openvr.VREvent_t()
    has_events = True
    while has_events:
        has_events = application.pollNextEvent(event)
    _actionsets = (openvr.VRActiveActionSet_t * 1)()
    _actionset = _actionsets[0]
    _actionset.ulActionSet = actionSetHandle
    openvr.VRInput().updateActionState(_actionsets)

    # String for collecting debug output information
    _debugoutput = ""

    # Get data for all button actions
    _strinputs = ""
    for i in buttonActionHandles:
        _strinputs += str(openvr.VRInput().getDigitalActionData(i, openvr.k_ulInvalidInputValueHandle).bState)

    # Send data via OSC
    if config["SendInts"]:
        _controller = get_controllertype()
        if config["ParametersInt"]["ControllerType"][1]:
            _debugoutput += f"ControllerType:\t\t{_controller}\n"
            oscClient.send_message(config["ParametersInt"]["ControllerType"][0], int(_controller))
        if config["ParametersInt"]["LeftThumb"][1]:
            _leftthumb = _strinputs[:4].rfind("1") + 1
            _debugoutput += f"LeftThumb:\t\t{_leftthumb}\n"
            oscClient.send_message(config["ParametersInt"]["LeftThumb"][0], int(_leftthumb))
        if config["ParametersInt"]["RightThumb"][1]:
            _rightthumb = _strinputs[4:].rfind("1") + 1
            _debugoutput += f"RightThumb:\t\t{_rightthumb}\n"
            oscClient.send_message(config["ParametersInt"]["RightThumb"][0], int(_rightthumb))

    if config["SendFloats"]:
        if config["ParametersFloat"]["LeftTrigger"][1]:
            _lefttriggervalue = openvr.VRInput().getAnalogActionData(leftTrigger, openvr.k_ulInvalidInputValueHandle).x
            _debugoutput += f"LeftTrigger:\t\t{_lefttriggervalue:.4f}\n"
            oscClient.send_message(config["ParametersFloat"]["LeftTrigger"][0], float(_lefttriggervalue))
        if config["ParametersFloat"]["RightTrigger"][1]:
            _righttriggervalue = openvr.VRInput().getAnalogActionData(rightTrigger, openvr.k_ulInvalidInputValueHandle).x
            _debugoutput += f"RightTrigger:\t\t{_righttriggervalue:.4f}\n"
            oscClient.send_message(config["ParametersFloat"]["RightTrigger"][0], float(_righttriggervalue))

    if config["SendBools"]:
        if config["ParametersBool"]["LeftAButton"][1]:
            _tmp = bool(int(_strinputs[0]))
            _debugoutput += f"LeftAButton:\t\t{_tmp}\n"
            oscClient.send_message(config["ParametersBool"]["LeftAButton"][0], _tmp)
        if config["ParametersBool"]["LeftBButton"][1]:
            _tmp = bool(int(_strinputs[1]))
            _debugoutput += f"LeftBButton:\t\t{_tmp}\n"
            oscClient.send_message(config["ParametersBool"]["LeftBButton"][0], _tmp)
        if config["ParametersBool"]["LeftTrackPad"][1]:
            _tmp = bool(int(_strinputs[2]))
            _debugoutput += f"LeftTrackPad:\t\t{_tmp}\n"
            oscClient.send_message(config["ParametersBool"]["LeftTrackPad"][0], _tmp)
        if config["ParametersBool"]["LeftThumbStick"][1]:
            _tmp = bool(int(_strinputs[3]))
            _debugoutput += f"LeftThumbStick:\t\t{_tmp}\n"
            oscClient.send_message(config["ParametersBool"]["LeftThumbStick"][0], _tmp)

        if config["ParametersBool"]["RightAButton"][1]:
            _tmp = bool(int(_strinputs[4]))
            _debugoutput += f"RightAButton:\t\t{_tmp}\n"
            oscClient.send_message(config["ParametersBool"]["RightAButton"][0], _tmp)
        if config["ParametersBool"]["RightBButton"][1]:
            _tmp = bool(int(_strinputs[5]))
            _debugoutput += f"RightBButton:\t\t{_tmp}\n"
            oscClient.send_message(config["ParametersBool"]["RightBButton"][0], _tmp)
        if config["ParametersBool"]["RightTrackPad"][1]:
            _tmp = bool(int(_strinputs[6]))
            _debugoutput += f"RightTrackPad:\t\t{_tmp}\n"
            oscClient.send_message(config["ParametersBool"]["RightTrackPad"][0], _tmp)
        if config["ParametersBool"]["RightThumbStick"][1]:
            _tmp = bool(int(_strinputs[7]))
            _debugoutput += f"RightThumbStick:\t{_tmp}\n"
            oscClient.send_message(config["ParametersBool"]["RightThumbStick"][0], _tmp)

        if config["ParametersBool"]["LeftABButtons"][1]:
            _tmp = bool(int(_strinputs[0])) & bool(int(_strinputs[1]))
            _debugoutput += f"LeftABButtons:\t\t{_tmp}\n"
            oscClient.send_message(config["ParametersBool"]["LeftABButtons"][0], _tmp)
        if config["ParametersBool"]["RightABButtons"][1]:
            _tmp = bool(int(_strinputs[4])) & bool(int(_strinputs[5]))
            _debugoutput += f"RightABButtons:\t\t{_tmp}\n"
            oscClient.send_message(config["ParametersBool"]["RightABButtons"][0], _tmp)

        if config["ParametersBool"]["LeftStickMoved"][1]:
            _leftxyvalue = openvr.VRInput().getAnalogActionData(leftxy, openvr.k_ulInvalidInputValueHandle)
            _tmp = abs(_leftxyvalue.x) > sticktolerance or abs(_leftxyvalue.y) > sticktolerance
            _debugoutput += f"LeftStickMoved:\t\t{_tmp}\n"
            oscClient.send_message(config["ParametersBool"]["LeftStickMoved"][0], _tmp)

        _rightxyvalue = openvr.VRInput().getAnalogActionData(rightxy, openvr.k_ulInvalidInputValueHandle)
        if config["ParametersBool"]["RightStickMoved"][1]:
            _tmp = abs(_rightxyvalue.x) > sticktolerance or abs(_rightxyvalue.y) > sticktolerance
            _debugoutput += f"RightStickMoved:\t{_tmp}\n"
            oscClient.send_message(config["ParametersBool"]["RightStickMoved"][0], _tmp)
        if config["ParametersBool"]["RightStickUp"][1]:
            _tmp = _rightxyvalue.y > 0.8
            _debugoutput += f"RightStickUp:\t\t{_tmp}\n"
            oscClient.send_message(config["ParametersBool"]["RightStickUp"][0], _tmp)
        if config["ParametersBool"]["RightStickDown"][1]:
            _tmp = _rightxyvalue.y < -0.8
            _debugoutput += f"RightStickDown:\t\t{_tmp}\n"
            oscClient.send_message(config["ParametersBool"]["RightStickDown"][0], _tmp)

    # debug output
    if args.debug:
        move(0, 0)
        print(_debugoutput)


cls()
if not args.debug:
    print("ThumbParamsOSC running...\n")
    print("You can minimize this window.\n")
    print(f"IP:\t\t{IP}")
    print(f"Port:\t\t{PORT}")
    print(f"SendInts:\t{config['SendInts']}")
    print(f"SendBools:\t{config['SendBools']}")
    print(f"SendFloats:\t{config['SendFloats']}")
    print(f"PollingRate:\t{pollingrate}s ({config['PollingRate']} Hz)")

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
