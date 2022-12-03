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

# Set window name on Windows
if os.name == 'nt':
    ctypes.windll.kernel32.SetConsoleTitleW("ThumbParamsOSC")


def move(y, x):
    """Moves console cursor."""
    print("\033[%d;%dH" % (y, x))


def cls():
    """Clears Console"""
    os.system('cls' if os.name == 'nt' else 'clear')


def resource_path(relative_path):
    """Gets absolute path from relative path"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


# load configs
config = json.load(open(resource_path('config.json')))
ovrConfig=json.load(open(resource_path('ovrConfig.json')))
IP = args.ip if args.ip else config["IP"]
PORT = args.port if args.port else config["Port"]
pollingrate = 1 / float(config['PollingRate'])

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


def print_startup_message():
    print("ThumbParamsOSC running...\n")
    print("IP:\t\t", IP)
    print("Port:\t\t", PORT)
    print("SendInts:\t", config["SendInts"])
    print("SendBools:\t", config["SendBools"])
    print("SendFloats:\t", config["SendFloats"])
    print(f"PollingRate:\t {pollingrate}s ({config['PollingRate']} Hz)")


def print_debug_message(controller, strinputs, leftthumb, rightthumb, lefttriggervalue, righttriggervalue, leftabbuttons, rightabbuttons, leftstickmoved, rightstickmoved, rightstickup, rightstickdown):
    move(0, 0)
    if config["SendInts"]:
        print("----------------------- Ints ------------------------")
        print("Controller:\t\t", controller, "\t\tEnabled:", config["ParametersInt"]["ControllerType"][1])
        print("LeftThumb:\t\t", leftthumb, "\t\tEnabled:", config["ParametersInt"]["LeftThumb"][1])
        print("RightThumb:\t\t", rightthumb, "\t\tEnabled:", config["ParametersInt"]["RightThumb"][1])
    if config["SendFloats"]:
        print("---------------------- Floats -----------------------")
        print("LeftTrigger:\t\t", f'{lefttriggervalue:.4f}', "\tEnabled:", config["ParametersFloat"]["LeftTrigger"][1])
        print("RightTrigger:\t\t", f'{righttriggervalue:.4f}', "\tEnabled:", config["ParametersFloat"]["RightTrigger"][1])
    if config["SendBools"]:
        print("----------------------- Bools -----------------------")
        if config["ParametersBool"]["LeftAButton"][1]
        print("LeftAButton:\t\t", bool(int(strinputs[0])), " ", "\tEnabled:", )
        print("LeftBButton:\t\t", bool(int(strinputs[1])), " ", "\tEnabled:", config["ParametersBool"]["LeftBButton"][1])
        print("LeftABButtons:\t\t", leftabbuttons, " ", "\tEnabled:", config["ParametersBool"]["LeftABButtons"][1])
        print("LeftTrackPad:\t\t", bool(int(strinputs[2])), " ", "\tEnabled:", config["ParametersBool"]["LeftTrackPad"][1])
        print("LeftThumbStick:\t\t", bool(int(strinputs[3])), " ", "\tEnabled:", config["ParametersBool"]["LeftThumbStick"][1])
        print("RightAButton:\t\t", bool(int(strinputs[4])), " ", "\tEnabled:", config["ParametersBool"]["RightAButton"][1])
        print("RightBButton:\t\t", bool(int(strinputs[5])), " ", "\tEnabled:", config["ParametersBool"]["RightBButton"][1])
        print("RightABButtons:\t\t", rightabbuttons, " ", "\tEnabled:", config["ParametersBool"]["RightABButtons"][1])
        print("RightTrackPad:\t\t", bool(int(strinputs[6])), " ", "\tEnabled:", config["ParametersBool"]["RightTrackPad"][1])
        print("RightThumbStick:\t", bool(int(strinputs[7])), " ", "\tEnabled:", config["ParametersBool"]["LeftStickMoved"][1])
        print("LeftStickMoved:\t\t", leftstickmoved, " ", "\tEnabled:", config["ParametersBool"]["LeftStickMoved"][1])
        print("RightStickMoved:\t", rightstickmoved, " ", "\tEnabled:", config["ParametersBool"]["RightStickMoved"][1])
        print("RightStickUp:\t\t", rightstickup, " ", "\tEnabled:", config["ParametersBool"]["RightStickUp"][1])
        print("RightStickDown:\t\t", rightstickdown, " ", "\tEnabled:", config["ParametersBool"]["RightStickDown"][1])


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
    
    # Initialize variables
    _strinputs = ""
    _controller = 0
    _leftthumb = 0
    _rightthumb = 0
    _lefttriggervalue = 0.0
    _righttriggervalue = 0.0
    _leftstickmoved = False
    _rightstickmoved = False
    _rightstickup = False
    _rightstickdown = False
    _leftabbuttons = False
    _rightabbuttons = False

    # Get data for all button actions
    
    for i in buttonActionHandles:
        _strinputs += str(openvr.VRInput().getDigitalActionData(i, openvr.k_ulInvalidInputValueHandle).bState)

    # Send data via OSC
    if config["SendInts"]:
        _controller = get_controllertype()
        if config["ParametersInt"]["ControllerType"][1]:
            oscClient.send_message(config["ParametersInt"]["ControllerType"][0], int(_controller))
        if config["ParametersInt"]["LeftThumb"][1]:
            _leftthumb = _strinputs[:4].rfind("1") + 1
            oscClient.send_message(config["ParametersInt"]["LeftThumb"][0], int(_leftthumb))
        if config["ParametersInt"]["RightThumb"][1]:
            _rightthumb = _strinputs[4:].rfind("1") + 1
            oscClient.send_message(config["ParametersInt"]["RightThumb"][0], int(_rightthumb))

    if config["SendFloats"]:
        if config["ParametersFloat"]["LeftTrigger"][1]:
            _lefttriggervalue = openvr.VRInput().getAnalogActionData(leftTrigger, openvr.k_ulInvalidInputValueHandle).x
            oscClient.send_message(config["ParametersFloat"]["LeftTrigger"][0], float(_lefttriggervalue))
        if config["ParametersFloat"]["RightTrigger"][1]:
            _righttriggervalue = openvr.VRInput().getAnalogActionData(rightTrigger, openvr.k_ulInvalidInputValueHandle).x
            oscClient.send_message(config["ParametersFloat"]["RightTrigger"][0], float(_righttriggervalue))

    if config["SendBools"]:
        _leftxyvalue = openvr.VRInput().getAnalogActionData(leftxy, openvr.k_ulInvalidInputValueHandle)
        _rightxyvalue = openvr.VRInput().getAnalogActionData(rightxy, openvr.k_ulInvalidInputValueHandle)

        if config["ParametersBool"]["LeftAButton"][1]:
            oscClient.send_message(config["ParametersBool"]["LeftAButton"][0], bool(int(_strinputs[0])))
        if config["ParametersBool"]["LeftBButton"][1]:
            oscClient.send_message(config["ParametersBool"]["LeftBButton"][0], bool(int(_strinputs[1])))
        if config["ParametersBool"]["LeftTrackPad"][1]:
            oscClient.send_message(config["ParametersBool"]["LeftTrackPad"][0], bool(int(_strinputs[2])))
        if config["ParametersBool"]["LeftThumbStick"][1]:
            oscClient.send_message(config["ParametersBool"]["LeftThumbStick"][0], bool(int(_strinputs[3])))
        
        if config["ParametersBool"]["RightAButton"][1]:
            oscClient.send_message(config["ParametersBool"]["RightAButton"][0], bool(int(_strinputs[4])))
        if config["ParametersBool"]["RightBButton"][1]:
            oscClient.send_message(config["ParametersBool"]["RightBButton"][0], bool(int(_strinputs[5])))
        if config["ParametersBool"]["RightTrackPad"][1]:
            oscClient.send_message(config["ParametersBool"]["RightTrackPad"][0], bool(int(_strinputs[6])))
        if config["ParametersBool"]["RightThumbStick"][1]:
            oscClient.send_message(config["ParametersBool"]["RightThumbStick"][0], bool(int(_strinputs[7])))

        if config["ParametersBool"]["LeftABButtons"][1]:
            _leftabbuttons = bool(int(_strinputs[0])) & bool(int(_strinputs[1]))
            oscClient.send_message(config["ParametersBool"]["LeftABButtons"][0], _leftabbuttons)
        if config["ParametersBool"]["RightABButtons"][1]:
            _rightabbuttons = bool(int(_strinputs[4])) & bool(int(_strinputs[5]))
            oscClient.send_message(config["ParametersBool"]["RightABButtons"][0], _rightabbuttons)

        if config["ParametersBool"]["LeftStickMoved"][1]:
            _leftstickmoved = abs(_leftxyvalue.x) > 0.05 or abs(_leftxyvalue.y) > 0.05
            oscClient.send_message(config["ParametersBool"]["LeftStickMoved"][0], _leftstickmoved)
        if config["ParametersBool"]["RightStickMoved"][1]:
            _rightstickmoved = abs(_rightxyvalue.x) > 0.05 or abs(_rightxyvalue.y) > 0.05
            oscClient.send_message(config["ParametersBool"]["RightStickMoved"][0], _rightstickmoved)

        if config["ParametersBool"]["RightStickUp"][1]:
            _rightstickup = _rightxyvalue.y > 0.8
            oscClient.send_message(config["ParametersBool"]["RightStickUp"][0], _rightstickup)
        if config["ParametersBool"]["RightStickDown"][1]:
            _rightstickdown = _rightxyvalue.y < -0.8
            oscClient.send_message(config["ParametersBool"]["RightStickDown"][0], _rightstickdown)


    # debug output
    if args.debug:
        print_debug_message(_controller, _strinputs, _leftthumb, _rightthumb, _lefttriggervalue, _righttriggervalue, _leftabbuttons, _rightabbuttons, _leftstickmoved, _rightstickmoved, _rightstickup, _rightstickdown)


cls()
if not args.debug:
    print_startup_message()

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
