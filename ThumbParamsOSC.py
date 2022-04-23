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
action_set_thumbparams = openvr.VRInput().getActionSetHandle('/actions/thumbparams')

inputActionHandles = []
config = json.load(open(os.path.join(os.path.join(resource_path('config.json')))))
for k in config:
    inputActionHandles.append(openvr.VRInput().getActionHandle(config[k]))

def handle_input():
    lrInputs = ""
    leftThumb = 0
    rightThumb = 0
    
    event = openvr.VREvent_t()
    has_events = True
    while has_events:
        has_events = application.pollNextEvent(event)
    action_sets = (openvr.VRActiveActionSet_t * 1)()
    action_set = action_sets[0]
    action_set.ulActionSet = action_set_thumbparams

    openvr.VRInput().updateActionState(action_sets)

    for i in inputActionHandles:
        lrInputs += str(openvr.VRInput().getDigitalActionData(i, openvr.k_ulInvalidInputValueHandle).bState)

    # 0 Not touching
    # 1 A Button
    # 2 B Button
    # 3 Trackpad
    # 4 Thumbstick
    leftThumb = lrInputs[:4].rfind("1") + 1
    rightThumb = lrInputs[4:].rfind("1") + 1

    if debugenabled:
        print("left:\t ", leftThumb)
        print("right:\t ", rightThumb)
        print("==============")
    oscClient.send_message("/avatar/parameters/LeftThumb", int(leftThumb))
    oscClient.send_message("/avatar/parameters/RightThumb", int(rightThumb))

while True:
    handle_input()
    time.sleep(0.005)