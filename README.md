# VRCThumbParamsOSC
VRChat OSC program that makes controller thumb positions accessible in Avatar V3 Parameters (For now only Index Controllers) 

This program just opens a console application with no output, it doesn't really need any UI but I might add something soon.

## Use

Just run the ***ThumbParamsOSC.exe*** and you are all set! <br/>
If you want to see the output in real time, launch the program with ```--debug``` and it will create an output with every poll.

## Avatar Setup

If you're here with the intention to use this mod for sign language, ![read my guide on it here!](https://github.com/I5UCC/VRC-ASL_Gestures)

The program simply reads all Index controller face buttons "touching" states and outputs them to two avatar params of "int" type.
You'll need to add these **case-sensitive** parameters to your avatar's base parameters:

- ***RightThumb***
- ***LeftThumb***

The program will set these parameters with an integer from 0-4 representing the position of each thumb.

| Value | Real Position |
| ----- | ------------- |
| 0     | Not Touching  |
| 1     | A Button      |
| 2     | B Button      |
| 3     | Trackpad      |
| 4     | Thumbstick    |

After that, you can use them just like other parameters in your Animation Controllers

# Credit
- ![benaclejames](https://github.com/benaclejames) and ![Greendayle](https://github.com/Greendayle) for the inspiration!
