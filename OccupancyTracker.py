# -*- coding: utf-8 -*-
"""
Original code created Spring 2020
@author: Hannah LaTourette
"""

import serial
import sys
import struct
import numpy as np
import threading
from Queue import Queue
import glob
import time
import datetime
from GridEyeKit import GridEYEKit

class OccupancyTracker():
    '''
    OccupancyTracker is made to use with the GridEyeKit
    Assumes the Panasonic GridEYE is posted in a doorway
    The model uses basic thresholding of column avgs to
    detect a person passing into or out of a doorway to
    and tracks the total number of people in the room.
    '''
    def __init__(self):
        # list of sensors we're using
        self.num_sensors = 2
        self.sensors = list()
        # grid dimensions
        self.height = 8
        self.width =  8 * self.num_sensors
        # flags for warmth detected
        self.heat_in  = False
        self.heat_mid = False
        self.heat_out = False
        # other flags
        self.exit = False # if out flag set before in
        self.refreshed = True # seen empty grid since last person
        # ints
        self.people_count = 0
        self.start_time   = -1
        self.room_temp    = 25
        self.warm_temp    = 28

    def connect_all(self):
        already_connected = []
        for i in range(self.num_sensors):
            self.sensors.append(GridEYEKit())
            connected, already_connected = self.sensors[i].connect(already_connected)
            if not connected:
                return False # if any sensor fails, return false
        self.set_start_time()
        self.set_avg_temp()
        return True

    def close_all(self):
        for sensor in self.sensors:
            sensor.close()

    def get_all_temperatures(self):
        tarrs = []
        for sensor in self.sensors:
            tarrs.append(sensor.get_temperatures())
        return np.hstack(tarrs)

    def set_avg_temp(self,num_samples=100):
        ''' Collect num_samples of temp to set room avg '''
        print "Finding average temperature..."
        tmp = []
        for i in range(num_samples):
            tmp.append(np.mean(self.get_all_temperatures()))
        room_temp = np.mean(tmp)
        print "Collected",num_samples,"samples. Room temp:",room_temp
        self.set_std_temps(room_temp)

    def set_start_time(self):
    	self.start_time = datetime.datetime.now()
    	print "Connected at",self.start_time

    def set_std_temps(self,rtemp):
    	self.room_temp = rtemp
    	self.warm_temp = rtemp * 1.1 # 15% increase

    def person_passed(self):
    	''' if all columns are warm, a person has passed through
    		refreshed flag keeps us from re-detecting a person '''
    	return (self.heat_in and self.heat_mid and \
    		    self.heat_out and self.refreshed)

    def update_col_flags(self,in_col,mid_col,out_col):
    	''' check first, middle, and last columns for a person
    		and update column flags accordingly '''
    	if in_col > self.warm_temp:
    		print "in:",in_col,">",self.warm_temp
    		self.heat_in = True
    	if mid_col > self.warm_temp:
    		self.heat_mid = True
    	if out_col > self.warm_temp:
    		self.heat_out = True
    		# if out col is set before in is, we
    		# know a person is exiting the room:
    		if self.heat_in == False:
    			self.exit = True

    def reset_all_flags(self):
    	''' after a person passes through, reset all flags
    		to begin looking for a new person '''
    	self.heat_in   = False
    	self.heat_mid  = False
    	self.heat_out  = False
    	self.refreshed = False # this keeps us from re-detecting same person
    	self.exit      = False    	

    def update_people_count(self,tarr):
    	''' check for people on either edge of the screen
    	    and update flags and person count accordingly'''

    	# Turn raw temp array into a grid for ease of use
    	grid = []
    	col_sums = []
    	grid = np.reshape(tarr,(self.height, self.width))

    	# Find average temp of first, last, and middle columns
    	# (in = side toward inside of room we're tracking) 
    	in_col    = np.mean([grid[x][0] for x in range(self.height)])
    	mid_col   = np.mean([grid[x][self.width/2] for x in range(self.height)])
    	out_col   = np.mean([grid[x][self.width-1] for x in range(self.height)])

    	# When the person we just counted has left, set the
    	# flag so we can start looking for a new person
    	if np.mean(grid) < self.warm_temp*0.95:
    		self.refreshed = True

    	# See which columns are warm
    	self.update_col_flags(in_col, mid_col, out_col)

    	# If all column flags are high, someone has passed through
    	if self.person_passed():
    		if self.exit == False:
	    		print "Someone entered the room!"
	    		self.people_count += 1
	    	else:
	    		print "Someone exited the room!"
	    		self.people_count -= 1
	    		self.people_count = max(self.people_count, 0)
    		print self.people_count,"people remain in the room."

    		# Reset all flags
    		self.reset_all_flags() # make all flags low again
