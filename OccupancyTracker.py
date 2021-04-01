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
    def __init__(self, num_sensors=1):
        # list of sensors we're using
        self.num_sensors = num_sensors
        self.sensors = list()
        # grid dimensions
        self.height = 8
        self.width =  8 * self.num_sensors
        # flags for warmth detected (by row)
        self.heat_in  = [False]*self.width
        self.heat_mid = [False]*self.width
        self.heat_out = [False]*self.width
        # other flags
        self.exit = [False]*self.width # if out flag set before in
        self.refreshed = [True]*self.width # seen empty grid since last person
        # ints
        self.people_count = 0
        self.start_time   = -1
        self.room_temp    = 25
        self.warm_temp    = 28
        # update strings for GUI
        self.update_text = {'avg':'', 'occupancy':'', 'update':''}
        # self.update = "Room temperature: 23.5C\n\nThreshold temp: 26.5C\n\nOccupancy: 5"

    def connect_all(self):
        already_connected = []
        for i in range(self.num_sensors):
            self.sensors.append(GridEYEKit())
            connected, already_connected = self.sensors[i].connect(already_connected)
            if not connected:
                return False # if any sensor fails, return false
        # self.set_start_time()
        self.update_text['update'] = "Connected at {}".format(datetime.datetime.now().strftime("%X"))
        print "Connected at",self.start_time
        self.set_avg_temp()
        self.set_update_text()
        return True

    def close_all(self):
        for sensor in self.sensors:
            sensor.ser.close()

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

    # def set_start_time(self):
    # 	self.start_time = datetime.datetime.now()
    #     self.update_text['update'] = "Connected at {}".format(self.start_time.strftime("%X"))
    # 	print "Connected at",self.start_time

    def set_std_temps(self,rtemp):
    	self.room_temp = rtemp
    	self.warm_temp = rtemp * 1.2 # 20% increase signals person is present

    def set_update_text(self):
        if self.num_sensors > 1: # only show room temp if we have a wide enough frame
            self.update_text['avg'] = "Room temperature: {:.1f} °C".format(self.room_temp)
        self.update_text['occupancy'] = "Occupancy: {:.0f}".format(self.people_count)
        self.update_text['in'] = "In frame: {:.0f}".format(self.people_count)

    def person_passed(self):
    	''' if all columns are warm, a person has passed through
    		refreshed flag keeps us from re-detecting a person '''
        person_passed = [True if (self.heat_in[x] and self.heat_mid[x] \
                              and self.heat_out[x]) else False for x in range(self.width) ]
        return person_passed

    def update_heat_flags(self,in_row,mid_row,out_row):
    	''' check top, middle, and bottom row for a person
    		and update heat flags accordingly '''

        # set heat flag arrays true wherever we detect a person
        tmp = self.find_clusters(in_row)
        self.heat_in = [self.heat_in[x] or tmp[x] for x in range(self.width)]
        tmp = self.find_clusters(mid_row)
        self.heat_mid = [self.heat_mid[x] or tmp[x] for x in range(self.width)]
        tmp = self.find_clusters(out_row)
        self.heat_out = [self.heat_out[x] or tmp[x] for x in range(self.width)]

        self.exit = [True if (self.heat_out[x] and not self.heat_in[x]) else False for x in range(self.width) ]

    def reset_all_flags(self):
    	''' after a person passes through, reset all flags
    		to begin looking for a new person '''
    	self.heat_in   = [False]*self.width
    	self.heat_mid  = [False]*self.width
    	self.heat_out  = [False]*self.width
    	self.refreshed = [False]*self.width # keeps us from re-detecting same person
    	self.exit      = [False]*self.width

    def reset_flags(self, col):
        self.heat_in[col]   = False
        self.heat_mid[col]  = False
        self.heat_out[col]  = False
        self.refreshed[col] = False # keeps us from re-detecting same person
        self.exit[col]      = False

    def set_refresh_flag(self, tarr):
        self.refreshed = [True if temp < self.warm_temp*0.9 else False for temp in np.mean(tarr, axis=0)]

    def find_clusters(self, tarr):
        clusters = [False]*self.width
        clusters[0] = True if (tarr[0] > tarr[1]) and (tarr[0]>self.warm_temp) else False
        clusters[-1] = True if (tarr[-1] > tarr[-2]) and (tarr[-1]>self.warm_temp) else False
        for x in range(1, len(tarr)-1):
            if (tarr[x] > self.warm_temp) and (tarr[x] > tarr[x-1]) and (tarr[x] > tarr[x+1]):
                clusters[x] = True
        return clusters

    def update_people_count(self, tarr):
    	''' check for people on either edge of the screen
    	    and update flags and person count accordingly'''

    	# Turn raw temp array into a grid for ease of use
        grid = []
        col_sums = []
        grid = np.reshape(tarr,(self.height, self.width))

    	# Grab threshold rows so we can check for heat
    	# (in = side toward inside of room we're tracking) 
        in_row = grid[0]
        mid_row = grid[4]
        out_row = grid[7]

    	# When the person we just counted has left, set the
    	# flag so we can start looking for a new person
        self.set_refresh_flag(grid)

    	# See which columns are warm
    	self.update_heat_flags(in_row, mid_row, out_row)

    	# If all column flags are high, someone has passed through
        person_passed = self.person_passed()
        for x in range(self.width):
            if person_passed[x]:
                print(person_passed)
                print(person_passed[x])
                if self.exit[x] == False:
                    print("Someone entered the room!")
                    self.update_text['update'] = "{}: A person entered the room.".format(datetime.datetime.now().strftime("%X"))
                    self.people_count += 1
                else:
                    print "Someone exited the room!"
                    self.people_count -= 1
                    self.update_text['update'] = "Someone left the room at {}!".format(datetime.datetime.now().strftime("%X"))
                    self.people_count = max(self.people_count, 0)
                print self.people_count,"people remain in the room."
                self.update_text['occupancy'] = "Occupancy: {}".format(self.people_count)
    		# Reset all flags
    		self.reset_flags(x) # make all flags low again
