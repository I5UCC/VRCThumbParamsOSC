import json
import openvr
import sys
import os
import time
import ctypes
import argparse
from pythonosc import udp_client

# Argument Parser
parser = argparse.ArgumentParser(
    description='ThumbParamsOSC: Takes button data from SteamVR and sends it to an OSC-Client')
parser.add_argument('-d', '--debug', required=False,
                    action='store_true', help='prints values for debugging')
parser.add_argument('-i', '--ip', required=False, type=str,
                    help="set OSC ip. Default=127.0.0.1")
parser.add_argument('-p', '--port', required=False,
                    type=str, help="set OSC port. Default=9000")
args = parser.parse_args()

# Set window name
ctypes.windll.kernel32.SetConsoleTitleW("ThumbParamsOSC")

# Moves Console Cursor


def move(y, x):
    print("\033[%d;%dH" % (y, x))

# Clears Console


def cls():
    os.system('cls' if os.name == 'nt' else 'clear')

# Gets absolute path from relative path


def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(
        os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


# load config
config = json.load(
    open(os.path.join(os.path.join(resource_path('config.json')))))

# Set up UDP OSC client
oscClient = udp_client.SimpleUDPClient(
    args.ip if args.ip else config["IP"], args.port if args.port else config["Port"])

# Init OpenVR and Actionsets
application = openvr.init(openvr.VRApplication_Utility)
action_path = os.path.join(resource_path(
    config["BindingsFolder"]), config["ActionManifestFile"])
openvr.VRInput().setActionManifestPath(action_path)
actionSetHandle = openvr.VRInput().getActionSetHandle(
    config["ActionSetHandle"])

# Set up OpenVR Action Handles
leftTrigger = openvr.VRInput().getActionHandle(
    config["TriggerActions"]["lefttrigger"])
rightTrigger = openvr.VRInput().getActionHandle(
    config["TriggerActions"]["righttrigger"])
buttonActionHandles = []
for k in config["ButtonActions"]:
    buttonActionHandles.append(
        openvr.VRInput().getActionHandle(config["ButtonActions"][k]))


def handle_input():
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
        lrInputs += str(openvr.VRInput().getDigitalActionData(i,
                        openvr.k_ulInvalidInputValueHandle).bState)

    # Get values for leftThumb and rightThumb (0-4)
    leftThumb = lrInputs[:4].rfind("1") + 1
    rightThumb = lrInputs[4:].rfind("1") + 1

    # Get values for TriggerLeft and TriggerRight (0.0-1.0)
    leftTriggerValue = openvr.VRInput().getAnalogActionData(
        leftTrigger, openvr.k_ulInvalidInputValueHandle).x
    rightTriggerValue = openvr.VRInput().getAnalogActionData(
        rightTrigger, openvr.k_ulInvalidInputValueHandle).x

    # Send data via OSC
    oscClient.send_message(config["VRCParameters"]
                           ["LeftTrigger"], float(leftTriggerValue))
    oscClient.send_message(config["VRCParameters"]
                           ["RightTrigger"], float(rightTriggerValue))
    oscClient.send_message(config["VRCParameters"]
                           ["LeftThumb"], int(leftThumb))
    oscClient.send_message(config["VRCParameters"]
                           ["RightThumb"], int(rightThumb))

    # debug output
    if args.debug:
        move(7, 0)
        print("DEBUG OUTPUT:")
        print("============================")
        print("Arguments:\t", args)
        print("Inputs:\t\t", lrInputs)
        print("LeftThumb:\t", leftThumb)
        print("RightThumb:\t", rightThumb)
        print("LeftTrigger:\t", f'{leftTriggerValue:.6f}')
        print("RightTrigger:\t", f'{rightTriggerValue:.6f}')


cls()
print("============================")
print("VRCThumbParamsOSC running...")
print("Sending to {}:{}".format(config["IP"], config["Port"]))
print("============================")
print("You can minimize this window...")
print("Press CTRL+C to exit or just close the window")

while True:
    try:
        handle_input()
        time.sleep(0.005)
    except KeyboardInterrupt:
        cls()
        exit()
