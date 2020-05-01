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

class OccupancyTracker():
'''
OccupancyTracker is made to use with the GridEyeKit
Assumes the Panasonic GridEYE is posted in a doorway
The model uses basic thresholding of column avgs to
detect a person passing into or out of a doorway to
and tracks the total number of people in the room.
'''
    def __init__(self):
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
        self.room_temp    = 0
        self.warm_temp    = 0

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
    	grid = np.reshape(tarr,(8,8))

    	# Find average temp of first, last, and middle columns
    	# (in = side toward inside of room we're tracking) 
    	in_col    = np.mean([grid[x][0] for x in range(8)])
    	mid_col   = np.mean([grid[x][4] for x in range(8)])
    	out_col   = np.mean([grid[x][7] for x in range(8)])

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
