# VRCThumbParamsOSC
VRChat OSC program that makes Valve Index and Oculus Touch controller thumb positions and Trigger values accessible in Avatar V3 Parameters.

## Use

Activate OSC in VRChat:

In Action menu, got to Options>OSC>Enable
![image](https://user-images.githubusercontent.com/43730681/165360919-826cdee2-2783-485c-a980-a69cc0d2f678.png)


Just run the ```ThumbParamsOSC.exe``` and you are all set! <br/>
### You might need to restart it after first run

## Avatar Setup

If you're here with the intention to use this mod for sign language, ![read my guide on it here!](https://github.com/I5UCC/VRC-ASL_Gestures)

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

# Credit
- ![benaclejames](https://github.com/benaclejames) and ![Greendayle](https://github.com/Greendayle) for the inspiration!
