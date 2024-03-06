# <img src="https://github.com/I5UCC/VRCThumbParamsOSC/blob/468e25fb16f03daac756d693656c784094518efb/src/icon.ico" width="32" height="32"> ThumbParamsOSC [![Github All Releases](https://img.shields.io/github/downloads/i5ucc/VRCThumbParamsOSC/total.svg)](https://github.com/I5UCC/VRCThumbParamsOSC/releases/latest) <a href='https://ko-fi.com/i5ucc' target='_blank'><img height='35' style='border:0px;height:25px;' src='https://az743702.vo.msecnd.net/cdn/kofi3.png?v=0' border='0' alt='Buy Me a Coffee at ko-fi.com' />

OSC program that makes SteamVR controller actions, Tracker button actions and XInput actions accessible as Avatar Parameters.

Currently supports ***Valve-Index***, ***Oculus(Meta)-Touch***, SteamVR Trackers and XInput Controllers.

### [<img src="https://assets-global.website-files.com/6257adef93867e50d84d30e2/636e0a6ca814282eca7172c6_icon_clyde_white_RGB.svg"  width="20" height="20"> Discord Support Server](https://discord.gg/rqcWHje3hn)

### [🢃 Download Latest release](https://github.com/I5UCC/VRCThumbParamsOSC/releases/latest)

# Available Parameters

Following sections go over all available parameters.
All parameters are **case-sensitive**.

## SteamVR Controller Parameters

| Parameter | Type |
|-----------|------|
| ControllerType | int |
| RightThumb | int |
| LeftThumb | int |
| LeftAButton | bool |
| LeftBButton | bool |
| LeftABButtons | bool |
| LeftTrackPad | bool |
| LeftThumbStick | bool |
| RightAButton | bool |
| RightBButton | bool |
| RightABButtons | bool |
| RightTrackPad | bool |
| RightThumbStick | bool |
| LeftAButtonClick | bool |
| LeftBButtonClick | bool |
| LeftTrackPadClick | bool |
| LeftThumbStickClick | bool |
| RightAButtonClick | bool |
| RightBButtonClick | bool |
| RightTrackPadClick | bool |
| RightThumbStickClick | bool |
| LeftGrab | bool |
| RightGrab | bool |
| LeftTrigger | float |
| RightTrigger | float |
| LeftGrabForce | float |
| RightGrabForce | float |
| RightTrackpadForce | float |
| LeftTrackpadForce | float |
| LeftStickMoved | bool |
| RightStickMoved | bool |
| LeftTrackPadY | float |
| RightTrackPadY | float |

## Tracker Parameters

| Parameter | Type |
|-----------|------|
| LeftFootTracker | bool |
| RightFootTracker | bool |
| WaistTracker | bool |
| ChestTracker | bool |
| LeftElbowTracker | bool |
| RightElbowTracker | bool |
| LeftKneeTracker | bool |
| RightKneeTracker | bool |

## XInput Parameters

| Parameter | Type |
|-----------|------|
| XInputAButton | bool |
| XInputBButton | bool |
| XInputXButton | bool |
| XInputYButton | bool |
| XInputLeftThumbstick | bool |
| XInputRightThumbstick | bool |
| XInputLeftBumper | bool |
| XInputRightBumper | bool |
| XInputBackButton | bool |
| XInputStartButton | bool |
| XInputLeftDPad | bool |
| XInputRightDPad | bool |
| XInputUpDPad | bool |
| XInputDownDPad | bool |
| XInputLeftTrigger | float |
| XInputRightTrigger | float |
| XInputLeftStickMoved | bool |
| XInputRightStickMoved | bool |
| XInputDPadMoved | bool |

## Special Parameters

The two int parameters ***RightThumb*** and ***LeftThumb*** represent the position of each thumb with the numbers from 0 to 4:

| Value | Real Position |
| ----- | ------------- |
| 0     | Not Touching  |
| 1     | A/X Button      |
| 2     | B/Y Button      |
| 3     | Trackpad      |
| 4     | Thumbstick    |

The int ***ControllerType*** gives what controller is currently being used:

| Controller | Value |
| ----- | ------------- |
| Meta/Oculus Touch | 2 |
| Index | 1 |
| XInput Controller | 10 |
| XInput+Meta | 12 |
| XInput+Index | 11 |
| Any other controller/No Controller | 0 |

***\[Left/Right]ABButtons*** detects if the thumb is on *either* the A or B buttons, or Touching both *at the same time*.

Tracker Power button parameters require Tracker roles to be set up in SteamVR: <br>
Go to `SteamVR-Settings > Manage Trackers` and set up tracking roles for each tracker respectively:
![268513445-16f47092-6f8b-4de6-9d5d-118fc9135c29](https://github.com/I5UCC/VRCThumbParamsOSC/assets/43730681/d2f771d8-dec4-46a0-9a55-6f02ce449eb1)

# How to use

Activate OSC in VRChat: <br/><br/>
![EnableOSC](https://user-images.githubusercontent.com/43730681/172059335-db3fd6f9-86ae-4f6a-9542-2a74f47ff826.gif)

In Action menu, got to Options>OSC>Enable <br/>

Run `Configurator.exe` to configure the program.
  
Then just run the `ThumbParamsOSC.exe` and you are all set! <br/>

# OSC Troubleshoot

If you have problems with this program, try this to fix it:
- Automatic way:
  - Close VRChat.
  - Run `Configurator.exe` and click on the Button "Reset OSC Config"
  - Startup VRChat again and it should work.
- Manual way:
  - Close VRChat.
  - Open 'Run' in Windows (Windows Key + R)
  - Type in `%APPDATA%\..\LocalLow\VRChat\VRChat\OSC`
  - Delete the folders that start with 'usr_*'.
  - Startup VRChat again and it should work.

# Decreasing OSC Traffic
ThumbparamsOSC consistently sends the current state of each parameter, with a lot of parameters the OSC traffic can increase significantly. <br>
To mitigate this there are a two things you can do:
- Disable all parameters that you do not need.
- Switch to a different mode then "Always Send"
You can read on how to do that in [#Configuration](https://github.com/I5UCC/VRCThumbParamsOSC?tab=readme-ov-file#configuration)

# Configuration

Running `Configurator.exe` lets you customize the Parameters that you want to have sent to VRChat, and some more things:

![grafik](https://github.com/I5UCC/VRCThumbParamsOSC/assets/43730681/bcac43cf-539f-4a50-b2a7-03ee62a83892)

Unchecking or checking any of the parameters and the hitting `save` will save the current settings. <br>
You can use the buttons below to do quick unticking or ticking of groups of parameters <br>
- `Floating Time` allows values "float" on the last value registered, it is measured in seconds. <br>
  - If `Floating Time` is set to -1 for boolean values, they will act like a toggle instead of always updating to the current state.
- Tick the `Unsigned` Box for any supported parameter to map the float value to [0, 1] instead of [-1, 1]
- `Mode` has 3 different values: 
  - "Send On Change" (Default) As the name might suggest, it sends a parameter only when it has changed from its previous value.
  - "Send On Positive" It sends a Parameter when it changes, but also continuosly sends Positive values every Poll.
  - "Always Send" This is like the old behaviour, just sends the parameters current state every Poll.
  - You can use the three buttons below to quickly switch between modes for every parameter

# Automatic launch with SteamVR
On first launch of the program, it registers as an Overlay app on SteamVR just like other well known programs like XSOverlay or OVRAdvancedSettings and can be launched on startup:
![Screenshot 2022-12-04 184629](https://user-images.githubusercontent.com/43730681/205506892-0927ed45-69c6-480f-b4b3-bc02d89c151e.png) <br>
![Screenshot 2022-12-04 184907](https://user-images.githubusercontent.com/43730681/205506956-7c397360-e14a-4783-a2c2-e5311749e2d4.png)

After setting the option to ON it will launch the program ***without the console*** on SteamVR startup.

# Command line Arguments
You can run this by using ```ThumbParamsOSC.exe {Arguments}``` in command line.

| Option | Value |
| ----- | ------------- |
| -d, --debug     | prints values for debugging |
| -i IP, --ip IP    | set OSC IP. Default=127.0.0.1  |
| -p PORT, --port PORT    | set OSC port. Default=9000      |

# Credit
- [pyopenvr](https://github.com/cmbruns/pyopenvr) thank you.
- [benaclejames](https://github.com/benaclejames) and [Greendayle](https://github.com/Greendayle) for the inspiration!

# Great Projects making use of ThumbparamsOSC:
- [VRC-ASL_Gestures](https://github.com/I5UCC/VRC-ASL_Gestures) by me :)
- [VRCImmersiveImmobilize](https://github.com/I5UCC/VRCImmersiveImmobilize) by me :)
- [AutoImmobilizeOSC](https://github.com/SouljaVR/AutoImmobilizeOSC) by [SouljaVR](https://github.com/SouljaVR)
- [Drone-OSC-Controller](https://github.com/qbitzvr/Drone-OSC-Controller) by [Qbitz](https://github.com/qbitzvr)
