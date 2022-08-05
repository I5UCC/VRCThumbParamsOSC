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


# load config
config = json.load(open(os.path.join(os.path.join(resource_path('config.json')))))
IP = args.ip if args.ip else config["IP"]
PORT = args.port if args.port else config["Port"]

# Set up UDP OSC client
oscClient = udp_client.SimpleUDPClient(IP, PORT)

# Init OpenVR and Actionsets
application = openvr.init(openvr.VRApplication_Utility)
action_path = os.path.join(resource_path(config["BindingsFolder"]), config["ActionManifestFile"])
openvr.VRInput().setActionManifestPath(action_path)
actionSetHandle = openvr.VRInput().getActionSetHandle(config["ActionSetHandle"])

# Set up OpenVR Action Handles
leftTrigger = openvr.VRInput().getActionHandle(config["TriggerActions"]["lefttrigger"])
rightTrigger = openvr.VRInput().getActionHandle(config["TriggerActions"]["righttrigger"])
buttonActionHandles = []
for k in config["ButtonActions"]:
    buttonActionHandles.append(openvr.VRInput().getActionHandle(config["ButtonActions"][k]))


def handle_input():
    """Handles all the OpenVR Input and sends it via OSC"""
    # Set up OpenVR events and Action sets
    event = openvr.VREvent_t()
    has_events = True
    while has_events:
        has_events = application.pollNextEvent(event)
    actionSets = (openvr.VRActiveActionSet_t * 1)()
    actionSet = actionSets[0]
    actionSet.ulActionSet = actionSetHandle
    openvr.VRInput().updateActionState(actionSets)

    # Get data for all button actions
    lrInputs = ""
    for i in buttonActionHandles:
        lrInputs += str(openvr.VRInput().getDigitalActionData(i, openvr.k_ulInvalidInputValueHandle).bState)

    # Get values for leftThumb and rightThumb (0-4)
    leftThumb = lrInputs[:4].rfind("1") + 1
    rightThumb = lrInputs[4:].rfind("1") + 1

    # Get values for TriggerLeft and TriggerRight (0.0-1.0)
    leftTriggerValue = openvr.VRInput().getAnalogActionData(leftTrigger, openvr.k_ulInvalidInputValueHandle).x
    rightTriggerValue = openvr.VRInput().getAnalogActionData(rightTrigger, openvr.k_ulInvalidInputValueHandle).x

    # Send data via OSC
    oscClient.send_message(config["ParametersInt"]["LeftThumb"], int(leftThumb))
    oscClient.send_message(config["ParametersInt"]["RightThumb"], int(rightThumb))

    oscClient.send_message(config["ParametersFloat"]["LeftTrigger"], float(leftTriggerValue))
    oscClient.send_message(config["ParametersFloat"]["RightTrigger"], float(rightTriggerValue))

    if config["SendBools"]:
        oscClient.send_message(config["ParametersBool"]["LeftAButton"], bool(int(lrInputs[0])))
        oscClient.send_message(config["ParametersBool"]["LeftBButton"], bool(int(lrInputs[1])))
        oscClient.send_message(config["ParametersBool"]["LeftTrackPad"], bool(int(lrInputs[2])))
        oscClient.send_message(config["ParametersBool"]["LeftThumbStick"], bool(int(lrInputs[3])))
        oscClient.send_message(config["ParametersBool"]["RightAButton"], bool(int(lrInputs[4])))
        oscClient.send_message(config["ParametersBool"]["RightBButton"], bool(int(lrInputs[5])))
        oscClient.send_message(config["ParametersBool"]["RightTrackPad"], bool(int(lrInputs[6])))
        oscClient.send_message(config["ParametersBool"]["RightThumbStick"], bool(int(lrInputs[7])))

        oscClient.send_message(config["ParametersBool"]["LeftABButton"], bool(int(lrInputs[0])) & bool(int(lrInputs[1])))
        oscClient.send_message(config["ParametersBool"]["RightABButton"], bool(int(lrInputs[4])) & bool(int(lrInputs[5])))

    # debug output
    if args.debug:
        move(10, 0)
        print("DEBUG OUTPUT:")
        print("---------- Ints ------------")
        print("LeftThumb:\t", leftThumb)
        print("RightThumb:\t", rightThumb)
        print("--------- Floats -----------")
        print("LeftTrigger:\t", f'{leftTriggerValue:.6f}')
        print("RightTrigger:\t", f'{rightTriggerValue:.6f}')
        if config["SendBools"]:
            print("--------- Bools ------------")
            print("LeftAButton:\t", bool(int(lrInputs[0])))
            print("LeftBButton:\t", bool(int(lrInputs[1])))
            print("LeftABButton:\t", bool(int(lrInputs[0])) & bool(int(lrInputs[1])))
            print("LeftTrackPad:\t", bool(int(lrInputs[2])))
            print("LeftThumbStick:\t", bool(int(lrInputs[3])))
            print("RightAButton:\t", bool(int(lrInputs[4])))
            print("RightBButton:\t", bool(int(lrInputs[5])))
            print("RightABButton:\t", bool(int(lrInputs[4])) & bool(int(lrInputs[5])))
            print("RightTrackPad:\t", bool(int(lrInputs[6])))
            print("RightThumbStick:", bool(int(lrInputs[7])))
        


cls()
print("ThumbParamsOSC running...\n")
print("IP:\t\t", IP)
print("Port:\t\t", PORT)
print("SendBools:\t", config["SendBools"])
print("\nYou can minimize this window.")
print("\nPress CTRL + C to exit or just close the window.")

# Main Loop
while True:
    try:
        handle_input()
        time.sleep(0.005)
    except KeyboardInterrupt:
        cls()
        exit()
    except Exception as e:
        cls()
        print("UNEXPECTED ERROR\n")
        print("Please Create an Issue on GitHub with the following information:\n")
        traceback.print_exc()
        input("\nPress ENTER to exit")
        exit()