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

# Set up UDP OSC client
oscClient = udp_client.SimpleUDPClient(IP, PORT)

# Init OpenVR and Actionsets
application = openvr.init(openvr.VRApplication_Utility)
action_path = os.path.join(resource_path(ovrConfig["BindingsFolder"]), ovrConfig["ActionManifestFile"])
appmanifest_path = resource_path(ovrConfig["AppManifestFile"])
openvr.VRApplications().addApplicationManifest(appmanifest_path)
openvr.VRInput().setActionManifestPath(action_path)
actionSetHandle = openvr.VRInput().getActionSetHandle(ovrConfig["ActionSetHandle"])

def GetControllertype():
    for i in range(1, openvr.k_unMaxTrackedDeviceCount):
        device_class = openvr.VRSystem().getTrackedDeviceClass(i)
        if device_class == 2:
            return openvr.VRSystem().getStringTrackedDeviceProperty(i, openvr.Prop_ControllerType_String)

# Set up OpenVR Action Handles
leftTrigger = openvr.VRInput().getActionHandle(ovrConfig["TriggerActions"]["lefttrigger"])
rightTrigger = openvr.VRInput().getActionHandle(ovrConfig["TriggerActions"]["righttrigger"])
buttonActionHandles = []
for k in ovrConfig["ButtonActions"]:
    buttonActionHandles.append(openvr.VRInput().getActionHandle(ovrConfig["ButtonActions"][k]))

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

    # Get data for all button actions
    _strinputs = ""
    for i in buttonActionHandles:
        _strinputs += str(openvr.VRInput().getDigitalActionData(i, openvr.k_ulInvalidInputValueHandle).bState)

    # Get values for leftThumb and rightThumb (0-4)
    _leftthumb = _strinputs[:4].rfind("1") + 1
    _rightthumb = _strinputs[4:].rfind("1") + 1

    # Send data via OSC
    if config["SendInts"]:
        if config["ParametersInt"]["ControllerType"][1]:
            controller = GetControllertype()
            match controller:
                case 'knuckles':
                    oscClient.send_message(config["ParametersInt"]["ControllerType"][0], 1)
                case _:
                    oscClient.send_message(config["ParametersInt"]["ControllerType"][0], 0)
        if config["ParametersInt"]["LeftThumb"][1]:
            oscClient.send_message(config["ParametersInt"]["LeftThumb"][0], int(_leftthumb))
        if config["ParametersInt"]["RightThumb"][1]:
            oscClient.send_message(config["ParametersInt"]["RightThumb"][0], int(_rightthumb))

    if config["SendFloats"]:
        # Get values for TriggerLeft and TriggerRight (0.0-1.0)
        _lefttriggervalue = openvr.VRInput().getAnalogActionData(leftTrigger, openvr.k_ulInvalidInputValueHandle).x
        _righttriggervalue = openvr.VRInput().getAnalogActionData(rightTrigger, openvr.k_ulInvalidInputValueHandle).x
        if config["ParametersFloat"]["LeftTrigger"][1]:
            oscClient.send_message(config["ParametersFloat"]["LeftTrigger"][0], float(_lefttriggervalue))
        if config["ParametersFloat"]["RightTrigger"][1]:
            oscClient.send_message(config["ParametersFloat"]["RightTrigger"][0], float(_righttriggervalue))

    if config["SendBools"]:
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
            oscClient.send_message(config["ParametersBool"]["LeftABButtons"][0], bool(int(_strinputs[0])) & bool(int(_strinputs[1])))
        if config["ParametersBool"]["RightABButtons"][1]:
            oscClient.send_message(config["ParametersBool"]["RightABButtons"][0], bool(int(_strinputs[4])) & bool(int(_strinputs[5])))

    # debug output
    if args.debug:
        move(11, 0)
        print("DEBUG OUTPUT:")
        if config["SendInts"]:
            print("---------- Ints ------------")
            print("LeftThumb:\t", _leftthumb, "\t\tEnabled:", config["ParametersInt"]["LeftThumb"][1])
            print("RightThumb:\t", _rightthumb, "\t\tEnabled:", config["ParametersInt"]["RightThumb"][1])
        if config["SendFloats"]:
            print("--------- Floats -----------")
            print("LeftTrigger:\t", f'{_lefttriggervalue:.6f}', "\tEnabled:", config["ParametersFloat"]["LeftTrigger"][1])
            print("RightTrigger:\t", f'{_righttriggervalue:.6f}', "\tEnabled:", config["ParametersFloat"]["RightTrigger"][1])
        if config["SendBools"]:
            print("--------- Bools ------------")
            print("LeftAButton:\t", bool(int(_strinputs[0])), " ", "\tEnabled:", config["ParametersBool"]["LeftAButton"][1])
            print("LeftBButton:\t", bool(int(_strinputs[1])), " ", "\tEnabled:", config["ParametersBool"]["LeftBButton"][1])
            print("LeftABButtons:\t", bool(int(_strinputs[0])) & bool(int(_strinputs[1])), " ", "\tEnabled:", config["ParametersBool"]["LeftABButtons"][1])
            print("LeftTrackPad:\t", bool(int(_strinputs[2])), " ", "\tEnabled:", config["ParametersBool"]["LeftTrackPad"][1])
            print("LeftThumbStick:\t", bool(int(_strinputs[3])), " ", "\tEnabled:", config["ParametersBool"]["LeftThumbStick"][1])
            print("RightAButton:\t", bool(int(_strinputs[4])), " ", "\tEnabled:", config["ParametersBool"]["RightAButton"][1])
            print("RightBButton:\t", bool(int(_strinputs[5])), " ", "\tEnabled:", config["ParametersBool"]["RightBButton"][1])
            print("RightABButtons:\t", bool(int(_strinputs[4])) & bool(int(_strinputs[5])), " ", "\tEnabled:", config["ParametersBool"]["RightABButtons"][1])
            print("RightTrackPad:\t", bool(int(_strinputs[6])), " ", "\tEnabled:", config["ParametersBool"]["RightTrackPad"][1])
            print("RightThumbStick:", bool(int(_strinputs[7])), " ", "\tEnabled:", config["ParametersBool"]["RightThumbStick"][1])


cls()
print("ThumbParamsOSC running...\n")
print("IP:\t\t", IP)
print("Port:\t\t", PORT)
print("SendInts:\t", config["SendInts"])
print("SendBools:\t", config["SendBools"])
print("SendFloats:\t", config["SendFloats"])
print("\nYou can minimize this window.")
print("\nPress CTRL + C to exit or just close the window.")

# Main Loop
while True:
    try:
        handle_input()
        time.sleep(0.04)
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
