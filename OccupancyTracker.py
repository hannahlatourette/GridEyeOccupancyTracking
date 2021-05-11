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
from queue import Queue
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
    def __init__(self, num_sensors=1, calibrate=False):
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
        # flag for calibration
        self.calibrate = calibrate
        self.overlaps  = []

    def setup(self):
        if self.connect_all():
            self.set_avg_temp()
            self.set_update_text()
            if self.calibrate and self.num_sensors > 1:
                self.calibrate_sensors()
            return True
        return False

    def connect_all(self):
        already_connected = []
        for i in range(self.num_sensors):
            self.sensors.append(GridEYEKit())
            connected, already_connected = self.sensors[i].connect(already_connected)
            if not connected:
                return False # if any sensor fails, return false
        self.update_text['update'] = "Connected at {}".format(datetime.datetime.now().strftime("%X"))
        return True

    def calibrate_sensors(self):
        # CURRENTLY USES HARDCODED COLUMN OVERLAP VALUES
        # TODO: Automatically detect overlaps (work on branch)
        self.overlaps = [(5,8), (6,9), (7,10)]
        self.width -= len(self.overlaps)
        self.update_text['update'] = "Calibration complete. {} columns overlap.".format(len(self.overlaps))

    def handle_overlaps(self, tarrs):
        for first, second in self.overlaps:
            second_vals = tarrs[:, second-16]
            tarrs = np.delete(tarrs, second-16, axis=1)
            tarrs[:, first] = ( tarrs[:, first] + second_vals ) / 2
        return tarrs

    def close_all(self):
        for sensor in self.sensors:
            sensor.ser.close()

    def get_all_temperatures(self):
        tarrs = []
        for sensor in self.sensors:
            tarrs.append(sensor.get_temperatures())
        tarrs = np.hstack(tarrs)
        if self.calibrate and len(self.overlaps):
            tarrs = self.handle_overlaps(tarrs)
        return tarrs

    def set_avg_temp(self,num_samples=20):
        ''' Collect num_samples of temp to set room avg '''
        print("Finding average temperature...")
        tmp = []
        for i in range(num_samples):
            tmp.append(np.mean(self.get_all_temperatures()))
        room_temp = np.mean(tmp)
        self.update_text['update'] = "Collected {} samples. Room temp: {}".format(num_samples, room_temp)
        self.set_std_temps(room_temp)

    def set_std_temps(self,rtemp):
    	self.room_temp = rtemp
    	self.warm_temp = rtemp * 1.15 # 15% temp increase signals that a person is present

    def set_update_text(self):
        if self.num_sensors > 1: # only show room temp if we have a wide enough frame
            self.update_text['avg'] = "Room temperature: {:.1f} °C".format(self.room_temp)
        self.update_text['occupancy'] = "Occupancy: {:.0f}".format(self.people_count)
        self.update_text['in'] = "In frame: {:.0f}".format(self.people_count)

    def person_passed(self):
        ''' if all columns are warm, a person has passed through
            refreshed flag keeps us from re-detecting a person '''
        person_passed = [True if (self.heat_in[x] and self.heat_mid[x] and self.heat_out[x]) else False for x in range(self.width) ]
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

        self.exit = [True if (self.heat_out[x] and not self.heat_in[x]) else self.exit[x] for x in range(self.width) ]

    def reset_all_flags(self):
        ''' after a person passes through, reset all flags
        to begin looking for a new person '''
        self.heat_in   = [False]*self.width
        self.heat_mid  = [False]*self.width
        self.heat_out  = [False]*self.width
        self.refreshed = [False]*self.width # keeps us from re-detecting same person
        self.exit      = [False]*self.width

    def clear_cluster(self, col):
        l_coord = r_coord = col
        # find the bounds of the cluster by looking through all heat flags
        for arr in [self.heat_in, self.heat_mid, self.heat_out]:
            left_warm = right_warm = True
            l_tmp = r_tmp = col
            arr[col] = False
            while left_warm or right_warm:
                if l_tmp < 1:
                    left_warm = False # can't move farther to left
                if left_warm:
                    if arr[l_tmp-1]:
                        l_tmp -= 1
                        # arr[l_tmp-1] = False
                    else:
                        left_warm = False
                if r_tmp > len(arr)-2:
                    right_warm = False # can't move farther to right
                if right_warm:
                    if arr[r_tmp+1]:
                        r_tmp += 1
                        # arr[r_tmp+1] = False
                    else:
                        right_warm = False
            # if this flag has widest cluster bounds we've seen, update them
            if l_tmp < l_coord:
                l_coord = l_tmp
            if r_tmp > r_coord:
                r_coord = r_tmp
        # clear out all flags within the bounds we found
        for i in range(l_coord, r_coord+1):
            self.reset_flag_col(i)

    def reset_flag_col(self, col):

        # for x in range(col-1, col+2): # clear out entire cluster
        self.heat_in[col]   = False
        self.heat_mid[col]  = False
        self.heat_out[col]  = False
        self.refreshed[col] = False # keeps us from re-detecting same person
        self.exit[col]      = False

    def set_refresh_flag(self, tarr):
        self.refreshed = [True if temp < self.warm_temp else False for temp in np.mean(tarr, axis=0)]

    def find_clusters(self, tarr):
        clusters = [False]*self.width
        clusters[0] = True if (tarr[0] > tarr[1]) and (tarr[0]>self.warm_temp) else False
        clusters[-1] = True if (tarr[-1] > tarr[-2]) and (tarr[-1]>self.warm_temp) else False
        for x in range(1, len(tarr)-1):
            if (tarr[x] > self.warm_temp) and (tarr[x] > tarr[x-1]) and (tarr[x] > tarr[x+1]):
                clusters[x] = True
        return clusters

    def update_people_count(self, tarr):
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
        # flag so we can starprint(t looking for a new person
        self.set_refresh_flag(grid)

        # See which columns are warm
        self.update_heat_flags(in_row, mid_row, out_row)

        # If all column flags are high, someone has passed through
        person_passed = self.person_passed()
        for x in range(self.width):
            if person_passed[x]:
                if self.exit[x]:
                    print("Someone exited the room!")
                    self.people_count -= 1
                    self.update_text['update'] = "{}: A person exited the room.".format(datetime.datetime.now().strftime("%X"))
                    self.people_count = max(self.people_count, 0)
                else:
                    print("Someone entered the room!")
                    self.update_text['update'] = "{}: A person entered the room.".format(datetime.datetime.now().strftime("%X"))
                    self.people_count += 1
                print(self.people_count,"people remain in the room.")
                self.update_text['occupancy'] = "Occupancy: {}".format(self.people_count)
                # Reset all flags
                self.clear_cluster(x) # make all flags low again