# <img src="https://github.com/I5UCC/VRCThumbParamsOSC/blob/468e25fb16f03daac756d693656c784094518efb/src/icon.ico" width="32" height="32"> ThumbParamsOSC [![Github All Releases](https://img.shields.io/github/downloads/i5ucc/VRCThumbParamsOSC/total.svg)](https://github.com/I5UCC/VRCThumbParamsOSC/releases/latest) <a href='https://ko-fi.com/i5ucc' target='_blank'><img height='35' style='border:0px;height:25px;' src='https://az743702.vo.msecnd.net/cdn/kofi3.png?v=0' border='0' alt='Buy Me a Coffee at ko-fi.com' />
OSC program that makes SteamVR controller actions accessible as Avatar Parameters.

Works for both VRChat and ChilloutVR but requires an OSC Mod when used in ChilloutVR.

Supports every controller that exposes Touch states to SteamVR. Including ***Valve-Index*** and ***Oculus(Meta)-Touch*** Controllers.

### [<img src="https://assets-global.website-files.com/6257adef93867e50d84d30e2/636e0a6ca814282eca7172c6_icon_clyde_white_RGB.svg"  width="20" height="20"> Discord Support Server](https://discord.gg/rqcWHje3hn)

# [🢃 Download Latest release](https://github.com/I5UCC/VRCThumbParamsOSC/releases/latest)

## How to use

Activate OSC in VRChat: <br/><br/>
![EnableOSC](https://user-images.githubusercontent.com/43730681/172059335-db3fd6f9-86ae-4f6a-9542-2a74f47ff826.gif)

In Action menu, got to Options>OSC>Enable <br/>

Run `Configurator.exe` to configure the program.
  
Then just run the `ThumbParamsOSC.exe` and you are all set! <br/>

## OSC Troubleshoot

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

## Available Parameters

The program reads all controller face buttons "touching" states and outputs them to two avatar parameters of "int" type.
You'll need to add these **case-sensitive** parameters to your avatar's base parameters:

- ***RightThumb***
- ***LeftThumb***

The program will set these parameters with an integer from 0-4 representing the position of each thumb.

| Value | Real Position |
| ----- | ------------- |
| 0     | Not Touching  |
| 1     | A/X Button      |
| 2     | B/Y Button      |
| 3     | Trackpad      |
| 4     | Thumbstick    |

Additionally, bool versions of the thumb positions are available, They're mapped the following:

- \[Left/Right]AButton
- \[Left/Right]BButton
- \[Left/Right]TrackPad
- \[Left/Right]ThumbStick

Another bool is also available to detect if the thumb is on *either* the A or B buttons, or Touching both *at the same time*.

- \[Left/Right]ABButtons

All button clicks are available as bool parameters, They're mapped the following:

- \[Left/Right]AButtonClick
- \[Left/Right]BButtonClick
- \[Left/Right]TrackPadClick
- \[Left/Right]ThumbStickClick

If you also need the Trigger pull values, you'll have to add two additional parameters of "float" type.

- LeftTrigger
- RightTrigger

The values range from 0.0 to 1.0 for both of these parameters, depending on how much you pull the trigger

4 Float Parameters for the thumb position on the trackpad:
- LeftTrackPad\[X/Y]
- RightTrackPad\[X/Y]

4 Float Parameters for the Thumbstick position:
- LeftThumbStick\[X/Y]
- RightThumbStick\[X/Y]

The Trackpad Parameters range from -1.0 to 1.0. you can think of it like a coordinate system, with the middle of the Trackpad being the origin. These parameters are only available on Index Controllers.

A few more bools to determine if the Left or Right stick was moved:
- LeftStickMoved
- RightStickMoved

Finally, the int ***ControllerType*** gives what controller is currently being used:
- Meta/Oculus Touch (2)
- Index (1)
- Any other controller/No Controller (0)

After adding any of those Parameter, you can use them just like other parameters in your Animation Controllers.

# Command line Arguments
You can run this by using ```ThumbParamsOSC.exe {Arguments}``` in command line.

| Option | Value |
| ----- | ------------- |
| -d, --debug     | prints values for debugging |
| -i IP, --ip IP    | set OSC IP. Default=127.0.0.1  |
| -p PORT, --port PORT    | set OSC port. Default=9000      |

# Configuration

Running `Configurator.exe` lets you customize the Parameters that you want to have sent to VRChat, and some more things:

![image](https://github.com/I5UCC/VRCThumbParamsOSC/assets/43730681/e95adf7f-d034-4045-93e3-129ca427516a)

Unchecking or checking any of the parameters and the hitting `save` will save the current settings.

# Automatic launch with SteamVR
On first launch of the program, it registers as an Overlay app on SteamVR just like other well known programs like XSOverlay or OVRAdvancedSettings and can be launched on startup:
![Screenshot 2022-12-04 184629](https://user-images.githubusercontent.com/43730681/205506892-0927ed45-69c6-480f-b4b3-bc02d89c151e.png) <br>
![Screenshot 2022-12-04 184907](https://user-images.githubusercontent.com/43730681/205506956-7c397360-e14a-4783-a2c2-e5311749e2d4.png)

After setting the option to ON it will launch the program ***without the console*** on SteamVR startup.

# Credit
- [pyopenvr](https://github.com/cmbruns/pyopenvr) thank you.
- [benaclejames](https://github.com/benaclejames) and [Greendayle](https://github.com/Greendayle) for the inspiration!

# Great Projects making use of ThumbparamsOSC:
- [VRC-ASL_Gestures](https://github.com/I5UCC/VRC-ASL_Gestures) by me :)
- [VRCImmersiveImmobilize](https://github.com/I5UCC/VRCImmersiveImmobilize) by me :)
- [AutoImmobilizeOSC](https://github.com/SouljaVR/AutoImmobilizeOSC) by [SouljaVR](https://github.com/SouljaVR)
