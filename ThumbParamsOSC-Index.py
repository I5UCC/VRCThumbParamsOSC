import json
import openvr
import sys
import os
import time
from pythonosc import udp_client

debugenabled = False
try:
    debugenabled = True if sys.argv[1] == "--debug" else False
except IndexError:
    pass

oscClient = udp_client.SimpleUDPClient("127.0.0.1", 9000)

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

application = openvr.init(openvr.VRApplication_Utility)
action_path = os.path.join(resource_path('bindings'), 'knuckles_thumbparams_actions.json')
openvr.VRInput().setActionManifestPath(action_path)
actionSet_thumbparams = openvr.VRInput().getActionSetHandle('/actions/thumbparams')

inputActionHandles = []
config = json.load(open(os.path.join(os.path.join(resource_path('config.json')))))
for k in config:
    inputActionHandles.append(openvr.VRInput().getActionHandle(config[k]))



def handle_input():
    event = openvr.VREvent_t()
    has_events = True
    while has_events:
        has_events = application.pollNextEvent(event)
    actionSets = (openvr.VRActiveActionSet_t * 1)()
    actionSet = actionSets[0]
    actionSet.ulActionSet = actionSet_thumbparams
    openvr.VRInput().updateActionState(actionSets)

    lrInputs = ""
    for i in inputActionHandles:
        lrInputs += str(openvr.VRInput().getDigitalActionData(i, openvr.k_ulInvalidInputValueHandle).bState)

    leftThumb = lrInputs[:4].rfind("1") + 1
    rightThumb = lrInputs[4:].rfind("1") + 1

    if debugenabled:
        print("Inputs:", lrInputs )
        print("left:\t", leftThumb)
        print("right:\t", rightThumb)
        print("=================")

    oscClient.send_message("/avatar/parameters/LeftThumb", int(leftThumb))
    oscClient.send_message("/avatar/parameters/RightThumb", int(rightThumb))

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
        exit()