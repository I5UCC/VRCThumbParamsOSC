import json
import openvr
import sys
import os
import time
import ctypes
from pythonosc import udp_client

def move (y, x):
    print("\033[%d;%dH" % (y, x))

def cls():
    os.system('cls' if os.name=='nt' else 'clear')

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

cls()
ctypes.windll.kernel32.SetConsoleTitleW("ThumbParamsOSC")
debugenabled = False
try:
    debugenabled = True if sys.argv[1] == "--debug" else False
except IndexError:
    pass

# Set up UDP OSC client
oscClient = udp_client.SimpleUDPClient("127.0.0.1", 9000)

# Init OpenVR and Actionsets
application = openvr.init(openvr.VRApplication_Utility)
action_path = os.path.join(resource_path('bindings'), 'thumbparams_actions.json')
openvr.VRInput().setActionManifestPath(action_path)
actionSet_thumbparams = openvr.VRInput().getActionSetHandle('/actions/thumbparams')

# Set up OpenVR Action Handles
buttonActionHandles = []
config = json.load(open(os.path.join(os.path.join(resource_path('config.json')))))
for k in config["Buttons"]:
    buttonActionHandles.append(openvr.VRInput().getActionHandle(config["Buttons"][k]))

leftTrigger = openvr.VRInput().getActionHandle(config["Trigger"]["lefttrigger"])
rightTrigger = openvr.VRInput().getActionHandle(config["Trigger"]["righttrigger"])

def handle_input():
    # Set up OpenVR events and Action sets
    event = openvr.VREvent_t()
    has_events = True
    while has_events:
        has_events = application.pollNextEvent(event)
    actionSets = (openvr.VRActiveActionSet_t * 1)()
    actionSet = actionSets[0]
    actionSet.ulActionSet = actionSet_thumbparams
    openvr.VRInput().updateActionState(actionSets)

    # Get data for all button actions
    lrInputs = ""
    for i in buttonActionHandles:
        lrInputs += str(openvr.VRInput().getDigitalActionData(i, openvr.k_ulInvalidInputValueHandle).bState)

    # Get values for leftThumb and rightThumb (0-4)
    leftThumb = lrInputs[:4].rfind("1") + 1
    rightThumb = lrInputs[4:].rfind("1") + 1
    
    leftTriggerValue =  openvr.VRInput().getAnalogActionData(leftTrigger, openvr.k_ulInvalidInputValueHandle).x
    rightTriggerValue =  openvr.VRInput().getAnalogActionData(rightTrigger, openvr.k_ulInvalidInputValueHandle).x
    
    # Send data via OSC
    oscClient.send_message(config["VRCParameters"]["LeftTrigger"], float(leftTriggerValue))
    oscClient.send_message(config["VRCParameters"]["RightTrigger"], float(rightTriggerValue))
    oscClient.send_message(config["VRCParameters"]["LeftThumb"], int(leftThumb))
    oscClient.send_message(config["VRCParameters"]["RightThumb"], int(rightThumb))

    # debug output
    if debugenabled:
        move(6,0)
        print("DEBUG OUTPUT:")
        print("=================")
        print("Inputs:\t", lrInputs)
        print("left:\t", leftThumb)
        print("right:\t", rightThumb)
        print("Tright:\t", f'{rightTriggerValue:.3f}')
        print("Tleft:\t", f'{leftTriggerValue:.3f}')

print("============================")
print("VRCThumbParamsOSC running...")
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