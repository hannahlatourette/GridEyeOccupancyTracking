# GridEyeOccupancyTracking
###### Master's project for Hannah LaTourette under supervision of Dr. Koushik Kar in Spring 2020

## Purpose
The intention of the code is to use the Panasonic GridEYE IR camera and development board to keep track of the number of people in a room. It builds off of the code to read the GridEYE written by Alexander Hoch, which I found [here](https://eu.industrial.panasonic.com/grideye-evalkit). My contributions are primarily found in [OccupancyTracker.py](https://github.com/hannahlatourette/GridEyeOccupancyTracking/blob/master/OccupancyTracker.py). Edits I made to the other code will be marked with *# HL ADDED*.

## Usage
To count people properly, the camera should be fixed to the side of the door frame in a place where the door won't damage it, aimed looking across the width of the door.

The program doesn't have many dependencies besides basic libraries like `numpy`. Likely the only thing one will need to install is `serial`, which can be done with a simple `pip` command:

```pip install serial```

From there, all you need to do is plug in the development board and run the code. _Make sure the board is plugged into your computer several seconds before you run the code_. Then, run the GUI application with:

```python Evalkit\ GUI\ V0.3.py```

A box should appear with simple stop and start buttons. When you click start, you should stay clear of the sensor and position it how you will when tracking occupancy. After clicking start, the device will collect 100 samples of the space to get an average room temperature, and this will be used to determine the threshold of what temperature signifies a person passing through.

Note: This application was developed with Python 2.7, but it seems that the only adjustment one would need to make is updating the format of the print statements.

## Troubleshooting
  * The biggest issue I had with the code was terminating it. This is an issue from the original code I used as a starting point. If you are unable to end your program, follow these steps:
     * Press ctrl+z to stop the program from running in the foreground   
     * Use `ps` to get a list of your running processes  
     * Identify any processes named python (if you have stopped the code a few times without closing it, there could be several instances here)   
     * Run `kill ####` for any of these numbers
     * Run `fg` - this will return them to the foreground - you should see "terminated" and any leftover GUI windows should close. Run `fg` until you are notified that no existing job exists
 * Another issue you may encounter is that the Grid-EYE device was not found. In this case, close out of the program entirely, unplug the device from your computer, plug it back in, and wait at least 30 seconds before running the program again.
 
## Current status (end of S20)
 * Program successfully detects single people passing in and out of a room through a doorway
 * Before beginning the loop, the program takes 100 samples to find the average temperature of the room and uses this to determine an appropriate threshold for person tracking
 * Model has maintained a successful count in cases of someone ducking their head into the doorway, lingering in the doorway, and 2 people walking closely behind each other
 
 ## Work to be done
 * Fixing the aforementioned termination issue would be helpful for development (it's likely some issue with tkinter)
 * Detection of two people entering a room next to each other. This could potentially be accomplished by moving the sensor from the side of the door frame to the top of the door frame, so that multiple people can be distinguished.
 * Eventually this processing should be moved on to the board's chip itself, instead of on a computer
 * After multiple people moving in one direction can be detected, a feature to detect people passing through simultaneously in opposite directions could be implemented
