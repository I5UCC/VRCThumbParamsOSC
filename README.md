# VRCThumbParamsOSC
OSC program that makes SteamVR controller thumb positions and Trigger values accessible in Avatar V3 Parameters. 

## Use

Activate OSC in VRChat: <br/><br/>
![EnableOSC](https://user-images.githubusercontent.com/43730681/172059335-db3fd6f9-86ae-4f6a-9542-2a74f47ff826.gif)

In Action menu, got to Options>OSC>Enable <br/>

Then just run the ```ThumbParamsOSC.exe``` and you are all set! <br/>
### You might need to restart ThumbParamsOSC.exe or even SteamVR after first run

### If you're here with the intention to use this program for american sign language, ![read my guide on it here!](https://github.com/I5UCC/VRC-ASL_Gestures) and run this with it if needed. You dont really need to read the rest of how it functions here if you dont intend to make your own!

## Avatar Setup

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

If you also need the Triggers to be set, you'll have to add two additional parameters of "float" type.

- ***LeftTrigger***
- ***RightTrigger***

The values range from 0.0 to 1.0 for both of these parameters, depending on how much you pull the trigger.

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

| Option | Value |
| ----- | ------------- |
| IP | OSC IP |
| Port | OSC Port |

Don't Edit the folowing, if you don't know what you are doing:

| Option | Value |
| ----- | ------------- |
| BindingsFolder | Relative path to folder that holds SteamVRBindings  |
| ActionManifestFile | Name of the Manifest file |
| ActionSetHandle | This applications ActionSetHandle |
| ButtonActions | Actions for SteamVR |
| TriggerActions | Actions for SteamVR |
| VRCParameters | Names for VRChat parameters |

# Credit
- ![benaclejames](https://github.com/benaclejames) and ![Greendayle](https://github.com/Greendayle) for the inspiration!
