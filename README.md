# <img src="https://github.com/I5UCC/VRCThumbParamsOSC/blob/468e25fb16f03daac756d693656c784094518efb/src/icon.ico" width="32" height="32"> ThumbParamsOSC [![Github All Releases](https://img.shields.io/github/downloads/i5ucc/VRCThumbParamsOSC/total.svg)](https://github.com/I5UCC/VRCThumbParamsOSC/releases/latest)
OSC program that makes SteamVR controller thumb positions (and some more useful things) accessible as Avatar Parameters.

Works for both VRChat and ChilloutVR but requires an OSC Mod when used in ChilloutVR.

Supports every controller that exposes Touch states to SteamVR. Including ***Valve-Index*** and ***Oculus(Meta)-Touch*** Controllers.

# [Download here](https://github.com/I5UCC/VRCThumbParamsOSC/releases/download/v.0.3.2/ThumbParamsOSC_Windows_v0.3.2.zip)

## How to use

Activate OSC in VRChat: <br/><br/>
![EnableOSC](https://user-images.githubusercontent.com/43730681/172059335-db3fd6f9-86ae-4f6a-9542-2a74f47ff826.gif)

In Action menu, got to Options>OSC>Enable <br/>

Then just run the ```ThumbParamsOSC.exe``` and you are all set! <br/>

## OSC Troubleshoot

If you have problems with this program, try this to fix it:
- Close VRChat.
- Open 'Run' in Windows (Windows Key + R)
- Type in `%APPDATA%\..\LocalLow\VRChat\VRChat`
- Delete the OSC folder.
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

If you also need the Trigger pull values, you'll have to add two additional parameters of "float" type.

- LeftTrigger
- RightTrigger

The values range from 0.0 to 1.0 for both of these parameters, depending on how much you pull the trigger

A few more bools to determine if the Left or Right stick was moved:
- LeftStickMoved
- RightStickMoved

Two more bools to determine if the Right stick is moved all the way up or down(Generally rarely used in many games)
- RightStickUp
- RightStickDown

Finally, the int ***ControllerType*** gives what controller is currently being used:
- Meta/Oculus Touch (2)
- Index (1)
- Any other controller/No Controller (0)

After that, you can use them just like other parameters in your Animation Controllers.

# Command line Arguments
You can run this by using ```ThumbParamsOSC.exe {Arguments}``` in command line.

| Option | Value |
| ----- | ------------- |
| -d, --debug     | prints values for debugging |
| -i IP, --ip IP    | set OSC IP. Default=127.0.0.1  |
| -p PORT, --port PORT    | set OSC port. Default=9000      |

# Configuration File

Editing the ***config.json*** file:

| Option | Value | Default |
| ----- | ------------- | ---- |
| IP | OSC IP | "127.0.0.1" |
| Port | OSC Port | 9000 |
| PollingRate | Rate that information gets send in Hz. | 25 |
| StickMoveTolerance | How much the stick needs to be moved to trigger LeftStickMoved and RightStickMoved in Percent. | 5 |
| SendInts | Whether to send Integers for the Thumb Positions or not. | true |
| SendFloats | Whether to send Floats for the Thumb Positions or not. | true |
| SendBools | Whether to send additional Bools for the Thumb Position or not. | true |
| ParametersInt | All the Int Parameters being sent. true or false determines if the paremeter is being sent. | true (on all of them) |
| ParametersFloat | All the Float Parameters being sent. true or false determines if the paremeter is being sent. | true (on all of them) |
| ParametersBool | All the Bool Parameters being sent. true or false determines if the paremeter is being sent. | true (on all of them) |

# Turning specific Parameters off/on
You can turn off specific Parameters by setting the value to ***false*** from ***true*** and vice versa
![image](https://user-images.githubusercontent.com/43730681/205451088-788e7845-ee1e-4047-9373-e36412394495.png)
 <br>Or you can turn off the entire sections for bools, int and float <br>
![image](https://user-images.githubusercontent.com/43730681/205451147-05681714-ad29-49e0-883a-213b5a4c95bc.png)

# Automatic launch with SteamVR
On first launch of the program, it registers as an Overlay app on SteamVR just like other well known programs like XSOverlay or OVRAdvancedSettings and can be launched on startup:
![Screenshot 2022-12-04 184629](https://user-images.githubusercontent.com/43730681/205506892-0927ed45-69c6-480f-b4b3-bc02d89c151e.png) <br>
![Screenshot 2022-12-04 184907](https://user-images.githubusercontent.com/43730681/205506956-7c397360-e14a-4783-a2c2-e5311749e2d4.png)

After setting the option to ON it will launch the program ***without the console*** on SteamVR startup.

# Credit
- [pyopenvr](https://github.com/cmbruns/pyopenvr) thank you.
- [benaclejames](https://github.com/benaclejames) and ![Greendayle](https://github.com/Greendayle) for the inspiration!

# Great Projects making use of ThumbparamsOSC:
- [VRC-ASL_Gestures](https://github.com/I5UCC/VRC-ASL_Gestures) by me :)
- [AutoImmobilizeOSC](https://github.com/SouljaVR/AutoImmobilizeOSC) by [SouljaVR](https://github.com/SouljaVR)

<a href='https://ko-fi.com/i5ucc' target='_blank'><img height='35' style='border:0px;height:46px;' src='https://az743702.vo.msecnd.net/cdn/kofi3.png?v=0' border='0' alt='Buy Me a Coffee at ko-fi.com' />
