import json

with open('config.json') as file:
    data = json.load(file)

controller_params = list()
xinput_params = list()
tracker_params = list()

for action in data["actions"]:
    param = action["osc_parameter"]
    t = action["type"]
    value = None
    if t == "vector2":
        for i in range(len(param)):
            if i == 2:
                value = (param[i], "bool")
            else:
                value = (param[i], "float")
    elif t == "vector1":
        value = (param, "float")
    else:
        value = (param, "bool")
    
    if "Tracker" in param:
        tracker_params.append(value)
    else:
        controller_params.append(value)
        

for action in data["xinput_actions"]:
    param = action["osc_parameter"]
    t = action["type"]
    value = None
    if t == "vector2":
        for i in range(len(param)):
            if i == 2:
                value = (param[i], "bool")
            else:
                value = (param[i], "float")
    elif t == "vector1":
        value = (param, "float")
    else:
        value = (param, "bool")
    
    xinput_params.append(value)


print("##SteamVR Controller Parameters")
print("| Parameter | Type |")
print("|-----------|------|")
for param, t in controller_params:
    print(f"| {param} | {t} |")

print("\n## Tracker Parameters")
print("| Parameter | Type |")
print("|-----------|------|")
for param, t in tracker_params:
    print(f"| {param} | {t} |")

print("\n## XInput Parameters")    
print("| Parameter | Type |")
print("|-----------|------|")
for param, t in xinput_params:
    print(f"| {param} | {t} |")