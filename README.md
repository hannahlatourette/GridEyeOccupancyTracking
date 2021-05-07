# GridEyeOccupancyTracking
###### Master's project for Hannah LaTourette under supervision of Dr. Koushik Kar in Spring 2020

## Purpose
The intention of the code is to use [Panasonic GridEYE IR camera development boards](https://na.industrial.panasonic.com/products/sensors/evaluation-kits/lineup/grid-eyer-amg8834eval-evaluation-kit) to keep track of the number of people in a room. It builds off of the code to read the GridEYE written by Alexander Hoch, which I found [here](https://eu.industrial.panasonic.com/grideye-evalkit). My contributions are primarily found in [OccupancyTracker.py](https://github.com/hannahlatourette/GridEyeOccupancyTracking/blob/master/OccupancyTracker.py). Edits I made to the other code will be marked with *# HL ADDED*.

## Setup
To count people properly, the cameras should be fixed to the on top of the doorway in a place where they won't be damaged. All sensors should be placed equidistant from each other, looking downward with the same orientation. The ideal distance between sensors depends on the height of the doorway. For a standard 80-inch door, one sensor can adequately cover 46 inches to either side of it (92 inches across total). Overlapping has been accounted for in the case that there is not adequate space to spread sensors that far apart.

The program doesn't have many dependencies besides basic libraries like `numpy`. Likely the only thing one will need to install is `serial`, which can be done with a simple `pip` command:

```pip install serial```

Note that the application was developed in Python 2.7 and should be run in a 2.7 environment.

## Usage

From there, all you need to do is plug in the development board and run the code. _Make sure the board is plugged into your computer several seconds before you run the code_. Then, run the GUI application with:

```python Evalkit\ GUI\ V0.3.py <num_sensors> <-calibrate>```

Note: `num_sensors` is an optional argument which defaults to 1; `-calibrate` is an optional argument which will detect overlapping in the views of multiple sensors. (This flag will have no affect if run with `num_sensors=1`.)

A box should appear with simple stop and start buttons. When you click start, you should stay clear of the sensor and position it how you will when tracking occupancy. After clicking start, the device will collect 100 samples of the space to get an average room temperature, and this will be used to determine the threshold of what temperature signifies a person passing through. If the `-calibrate` flag was used and `num_sensors>1`, the calibration process will begin after the room temperature has been measured.

## Troubleshooting
 * _Grid-EYE device was not found._ This occurs when the program was run too quickly after connecting the sensors to the computer. In this case, close out of the program entirely, unplug the device from your computer, plug it back in, and wait at least 30 seconds before running the program again.

 * _Multiple read/COM port error._ Sometimes an incorrect termination of the serial connections to one or more of the sensors will make it impossible for us to reconnect to them. This should never happen while the program is running: it is only an issue in debugging when first running the program.. In this case, unplug all sensors, wait 30 seconds, and reconnect. 

 * _Program will not terminate._ This error existed in the original code which this project builds off. It should now be resolved; this information is included mostly as a precaution. If you are unable to end your program, follow these steps:
     * Press ctrl+z to stop the program from running in the foreground   
     * Use `ps` to get a list of your running processes  
     * Identify any processes named `python` (if you have stopped the code a few times without closing it, there could be several instances here) and note the PID  
     * Run `kill ####` for any of these numbers
     * Run `fg` - this will return them to the foreground - you should see "terminated" and any leftover GUI windows should close. Run `fg` until you are notified that no existing job exists

## Current status (end of S21)
 * Model has maintained a successful count of people in a room in cases of:
     * A person ducking their head into the doorway, lingering in the doorway, and 2 people walking closely behind each other
     * A person lingering in the doorway then either coming or going
     * A person walking parallel to the doorway
     * People walking closely behind each other
     * People walking closely side by side
     * People entering while other exit simultaneously
 * Before beginning the loop, the program takes 100 samples to find the average temperature of the room and uses this to determine an appropriate threshold for person tracking
 * Model can successfully incorporate data from multiple sensors
 * GUI dynamically changes to show grids scaled according to the number of sensors connected, and according to the amount of overlapping detected
 * GUI includes a dashboard which shows live updates as well as the current occupancy count
 * Termination issue mentioned in Troubleshooting above has been resolved.
 
 ## Work to be done
 * Utilize the development boards' included [PAN1740 Series Bluetooth module](https://na.industrial.panasonic.com/products/wireless-connectivity/bluetooth/lineup/bluetooth-low-energy/series/90874) to transmit wirelessly
 * Eventually this data processing should be moved on to the board's chip itself, instead of on a computer
 * Some GUI updates would be helpful, including:
     * Calibrate button which allows for re-calibration while the software is running
     * Manual reset button for occupancy count
     * Set up notifications (text or email) in the event that occupancy exceeds a certain number (or similar case)

