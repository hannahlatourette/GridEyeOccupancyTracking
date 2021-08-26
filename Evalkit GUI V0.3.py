# -*- coding: utf-8 -*-
"""
Created on Wed Jul 15 16:56:46 2015

@author: Alexander Hoch

"""
import tkinter as tk
import tkinter.font
import tkinter.messagebox
import colorsys
import sys
from  GridEyeKit import GridEYEKit
import OccupancyTracker as ot

import numpy as np
np.set_printoptions(linewidth=400)

import smtplib
from email.message import EmailMessage


class GridEYE_Viewer():

    def __init__(self,root,num_sensors=1,calibrate=False,capacity=1,user_email=""):
        self.max_capacity = capacity
        self.user_email = user_email
        
        """ Initialize Window """
        self.tkroot = root
        self.tkroot.protocol('WM_DELETE_WINDOW', self.exitwindow) # Close serial connection and close window

        """ Initialize variables for color interpolation """
        self.HUEstart= 0.5 #initial color for min temp (0.5 = blue)
        self.HUEend = 1 #initial color for max temp (1 = red)
        self.HUEspan = self.HUEend - self.HUEstart

        # self.kit = GridEYEKit()
        self.tracker = ot.OccupancyTracker(num_sensors, calibrate)
        
        """ Grid Eye related variables"""
        self. MULTIPLIER = 0.25 # temp output multiplier
        
        """ Initialize Loop bool"""
        self.START = False
              
        """Initialize frame tor temperature array (tarr)"""
        self.frameTarr = tk.Frame(master=self.tkroot, bg='white')
        self.frameTarr.place(x=5, y=5, width = 41 * self.tracker.width + 1, height = 329)
        
        """Initialize pixels tor temperature array (tarr)"""
        self.tarrpixels = []
        self.tarrpixels_init()
    
        """Initialize frame tor Elements"""
        self.frameElements = tk.Frame(master=self.tkroot)
        self.frameElements.place(x=(328 * self.tracker.num_sensors)+25, y=10, width = 70, height = 50) # HL make dynamic

        self.frameElementsR = tk.Frame(master=self.tkroot)
        self.frameElementsR.place(x=(328 * self.tracker.num_sensors)+25+70, y=10, width = 70, height = 50)

        self.frameInfoText = tk.Frame(master=self.tkroot)
        self.frameInfoText.place(x=(328 * self.tracker.num_sensors)+25, y=60, width = 140, height = 250)
        
        """Initialize controll buttons"""
        self.buttonStart = tk.Button(master=self.frameElements, text='start', bg='white',
                                 command=self.start_update)
        self.buttonStart.pack()
        self.buttonStop = tk.Button(master=self.frameElementsR, text='stop', bg='white',
                                 command=self.stop_update)
        self.buttonStop.pack()

        """Initialize temperature adjustment"""
        self.lableTEMPMAX = tk.Label(master=self.frameInfoText, pady=5, text='Max (red)')
        self.lableTEMPMAX.pack()
        self.MAXTEMP = tk.Scale(self.frameInfoText, from_=-20, to=120, resolution =0.25)
        self.MAXTEMP.set(31)
        self.MAXTEMP.pack()
        self.lableMINTEMP = tk.Label(master=self.frameInfoText, pady=5, text='Min (blue)')
        self.lableMINTEMP.pack()
        self.MINTEMP = tk.Scale(self.frameInfoText, from_=-20, to=120, resolution =0.25)
        self.MINTEMP.set(25)
        self.MINTEMP.pack()

        ''' DASHBOARD COMPONENTS '''
        helv36 = tkinter.font.Font(family="system",size=13)
        # room temperature indicator
        self.room_temp_txt = tk.StringVar()
        self.labelROOMTEMP = tk.Label(master=self.tkroot, textvariable=self.room_temp_txt, font=helv36)
        self.labelROOMTEMP.place(relx=0.6, rely=1.0, anchor='s')
        # current occupancy indicator
        self.occupancy_txt = tk.StringVar()
        self.labelOCCUPANCY = tk.Label(master=self.tkroot, textvariable=self.occupancy_txt, font=helv36)
        self.labelOCCUPANCY.place(relx=1.0, rely=1.0, anchor='se')
        # latest update indicator
        self.update_txt = tk.StringVar()
        self.labelUPDATE = tk.Label(master=self.tkroot, textvariable=self.update_txt, font=helv36)
        self.labelUPDATE.place(relx=0.0, rely=1.0, anchor='sw')

        """Manual Occupancy Reset Button"""
        def reset_occupancy():
            self.tracker.people_count = 0
            self.tracker.update_text['occupancy'] = f"Occupancy: {self.tracker.people_count}"
            self.occupancy_txt.set(self.tracker.update_text['occupancy'])

        occupancy_reset = tk.Button(master=self.tkroot, text="Reset Occupancy", command=reset_occupancy)
        occupancy_reset.place(x=360, y=360)

        """Email message for push notifications"""
        self.max_capacity_reached = EmailMessage()
        self.max_capacity_reached['Subject'] = "Max Capacity"
        self.max_capacity_reached['From'] = "Occupancy Tracker"
        self.max_capacity_reached['To'] = self.user_email
        self.max_capacity_reached.set_content("You have reached the maximum capacity of this room")

        self.server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        self.server.login("occupancyproject2021@gmail.com", "0ccup@ncy10")
    
        """Maximum Capacity Popup Warning and Push Notifications (Email)"""
        if self.tracker.people_count >= self.max_capacity and self.max_capacity != 0:
            tkinter.messagebox.showwarning("Maximum Capacity", "You have reached the maximum capacity of this room")
            self.server.send_message(self.max_capacity_reached)

    def tarrpixels_init(self):
        if len(self.tarrpixels): # remove any old pixels
            self.frameTarr.place(x=5, y=5, width = 41 * self.tracker.width + 1, height = 329)
            for pix in self.tarrpixels:
                pix.destroy()
        self.tarrpixels = []
        for i in range(self.tracker.height):
            for j in range(self.tracker.width):
                pix = tk.Label(master=self.frameTarr, bg='gray', text='x')
                spacerx = 1
                spacery = 1
                pixwidth = 40
                pixheight = 40
                pix.place(x=spacerx+j*(spacerx+pixwidth), y=spacery+i*(pixheight+spacery),  width = pixwidth, height = pixheight)
                print()
                self.tarrpixels.append(pix) # attached all pixels to tarrpixel list

    def exitwindow(self):
        """ if window is clsoed, serial connection has to be closed!"""
        self.tracker.close_all()
        self.tkroot.destroy()
        
    def stop_update(self):
        """ stop button action - stops infinite loop """
        self.START = False
        self.update_tarrpixels()

    def start_update(self):
        self.tracker.update_text['update'] = "Attempting to connect to sensors...."
        self.update_txt.set(self.tracker.update_text['update'])
        if self.tracker.setup():
            if self.tracker.calibrate:
                self.tarrpixels_init() # recreate tarrpixels to reflect calibrated width
            """ start button action -start serial connection and start pixel update loop"""
            self.room_temp_txt.set(self.tracker.update_text['avg'])
            self.occupancy_txt.set(self.tracker.update_text['occupancy'])
            self.update_txt.set(self.tracker.update_text['update'])
            self.MAXTEMP.set(self.tracker.warm_temp)
            self.START = True
            """ CAUTION: Wrong com port error is not handled"""
            self.update_tarrpixels()
        else:
            tkinter.messagebox.showerror("Not connected", "Could not find Grid-EYE Eval Kit - please install driver and connect")
        
    def get_tarr(self):
        """ unnecessary function - only converts numpy array to tuple object"""
        tarr = []
        for temp in self.tracker.get_all_temperatures(): # only fue to use of old rutines
            for temp2 in temp:
                tarr.append(temp2)
        return tarr
        
    def update_tarrpixels(self):
        """ Loop for updating pixels with values from funcion "get_tarr" - recursive function with exit variable"""
        if self.START == True:
            tarr = self.get_tarr() # Get temerature array
            self.tracker.update_people_count(tarr) # HL ADDED
            self.update_txt.set(self.tracker.update_text['update'])
            self.occupancy_txt.set(self.tracker.update_text['occupancy'])
            i = 0 # counter for tarr
            if len(tarr) == len(self.tarrpixels): # check if problem with readout
                for tarrpix in self.tarrpixels:
                    tarrpix.config(text=tarr[i]) # Update Pixel text
                    if tarr[i] < self.MINTEMP.get(): # For colors, set borders to min/max temp
                        normtemp = 0
                    elif tarr[i] > self.MAXTEMP.get(): # For colors, set borders to min/max temp
                        normtemp = 1
                    else:
                        TempSpan = self.MAXTEMP.get() - self.MINTEMP.get()
                        if TempSpan <= 0:   # avoid division by 0 and negative values
                            TempSpan = 1
                        normtemp = (float(tarr[i])-self.MINTEMP.get())/TempSpan #Normalize temperature 0...1
                    h = normtemp*self.HUEspan+self.HUEstart # Convert to HSV colors (only hue used)
                    if h>1:
                        print(h)
                        print(normtemp)
                        print(self.HUEspan)
                        print(self.HUEstart)
                    bgrgb = tuple(int(255*j) for j in colorsys.hsv_to_rgb(h,1,1)) # convert to RGB colors
                    tarrpix.config(bg=('#%02x%02x%02x' % bgrgb)) # Convert to Hex String
                    i +=1  # increment tarr counter
            else:
                print("Error - temperature array length wrong")
            self.frameTarr.after(10,self.update_tarrpixels) # recursive function call all 10 ms (get_tarr will need about 100 ms to respond)

def get_geometry_str(num_sensors):
    width = (320 * num_sensors) + 200
    return str(width) + 'x450'

global num_sensors, capacity, user_email
num_sensors = 1
capacity = 0
user_email = ""

"""If entering number of sensors from terminal"""
calibrate = False
if len(sys.argv) > 1:
    num_sensors = int(sys.argv[1])
if len(sys.argv) > 2:
    calibrate = True

"""Starting GUI"""
def start(num_sensors, capacity, user_email=""):
    if num_sensors > 2:
        calibrate = True
    else:
        calibrate = False
    
    print(capacity)

    global root
    root = tk.Tk()
    root.title('Grid-Eye Occupancy Tracker')
    root.geometry(get_geometry_str(num_sensors))        
    Window = GridEYE_Viewer(root, num_sensors, calibrate, int(capacity), user_email)
    settings = tk.Button(master=root, text="Change Settings", command=input_settings)
    settings.place(x=5, y=360)
    root.mainloop()

"""Restarting GUI"""
def restart(num_sensors, capacity, user_email):
    root.destroy()
    start(num_sensors, capacity, user_email)

"""Input number of sensors, maximum capacity, and user email"""
def input_settings():
    settings_popup = tk.Toplevel()

    input_prompt = tk.Label(master=settings_popup, text="Enter the number of sensors")
    input_prompt.grid(row=0, column=0)
    num_sensors_input = tk.Entry(master=settings_popup)
    num_sensors_input.grid(row=1, column=0)

    capacity_prompt = tk.Label(master=settings_popup, text="Enter the maximum capacity")
    capacity_prompt.grid(row=2, column=0)
    capacity_input = tk.Entry(master=settings_popup)
    capacity_input.grid(row=3, column=0)
    
    email_prompt = tk.Label(master=settings_popup, text="Enter your email")
    email_prompt.grid(row=4, column=0)
    email_input = tk.Entry(master=settings_popup)
    email_input.grid(row=5, column=0)

    confirm = tk.Button(master=settings_popup, text="Confirm", command=lambda: restart(int(num_sensors_input.get()), int(capacity_input.get()), email_input.get()))
    confirm.grid(row=6, column=0)

start(num_sensors, capacity)