import json
from turtle import left
import openvr
import sys
import os
import time
import tkinter as tk
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
    global leftThumb
    global rightThumb
    global lrInputs 
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

    root.after(5,handle_input)

root = tk.Tk()
canvas = tk.Canvas(root, width=470, height=220, borderwidth=0, highlightthickness=0)
canvas.grid()

def _create_circle(self, x, y, r, **kwargs):
    return self.create_oval(x-r, y-r, x+r, y+r, **kwargs)
tk.Canvas.create_circle = _create_circle

sleft = canvas.create_circle(40, 60, 30, fill="#BBB", outline="#DDD", width=4)
canvas.create_text(40, 60, text="S", font=('Arial','20','bold'))

tleft = canvas.create_circle(100, 140, 50, fill="#BBB", outline="#DDD", width=4)
canvas.create_text(100, 140, text="T", font=('Arial','20','bold'))

bleft = canvas.create_circle(190, 80, 20, fill="#BBB", outline="#DDD", width=4)
canvas.create_text(190, 80, text="B", font=('Arial','15','bold'))

aleft = canvas.create_circle(190, 140, 20, fill="#BBB", outline="#DDD", width=4)
canvas.create_text(190, 140, text="A", font=('Arial','15','bold'))


sright = canvas.create_circle(430, 60, 30, fill="#BBB", outline="#DDD", width=4)
canvas.create_text(430, 60, text="S", font=('Arial','20','bold'))

tright = canvas.create_circle(350, 140, 50, fill="#BBB", outline="#DDD", width=4)
canvas.create_text(350, 140, text="T", font=('Arial','20','bold'))

bright = canvas.create_circle(260, 80, 20, fill="#BBB", outline="#DDD", width=4)
canvas.create_text(260, 80, text="B", font=('Arial','15','bold'))

aright = canvas.create_circle(260, 140, 20, fill="#BBB", outline="#DDD", width=4)
canvas.create_text(260, 140, text="A", font=('Arial','15','bold'))

def updatecanvas():
    global leftThumb
    global rightThumb

    canvas.itemconfig(sleft, outline="#DDD")
    canvas.itemconfig(tleft, outline="#DDD")
    canvas.itemconfig(bleft, outline="#DDD")
    canvas.itemconfig(aleft, outline="#DDD")
    canvas.itemconfig(aright, outline="#DDD")
    canvas.itemconfig(bright, outline="#DDD")
    canvas.itemconfig(tright, outline="#DDD")
    canvas.itemconfig(sright, outline="#DDD")

    if leftThumb == 1:
        canvas.itemconfig(aleft, outline="#ff8800")
    elif leftThumb == 2:
        canvas.itemconfig(bleft, outline="#ff8800")
    elif leftThumb == 3:
        canvas.itemconfig(tleft, outline="#ff8800")
    elif leftThumb == 4:
        canvas.itemconfig(sleft, outline="#ff8800")
    
    if rightThumb == 1:
        canvas.itemconfig(aright, outline="#ff8800")
    elif rightThumb == 2:
        canvas.itemconfig(bright, outline="#ff8800")
    elif rightThumb == 3:
        canvas.itemconfig(tright, outline="#ff8800")
    elif rightThumb == 4:
        canvas.itemconfig(sright, outline="#ff8800")
    
    root.after(5,updatecanvas)

root.title("VRCThumbParamsOSC")
root.resizable(False, False)
root.after(5,handle_input)
root.after(5,updatecanvas)
root.mainloop()