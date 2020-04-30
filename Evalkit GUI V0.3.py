# -*- coding: utf-8 -*-
"""
Created on Wed Jul 15 16:56:46 2015

@author: Alexander Hoch
"""

import Tkinter as tk
import tkMessageBox
import colorsys
from  GridEyeKit import GridEYEKit

# Grid Eye related numbers



class GridEYE_Viewer():

    def __init__(self,root):
        
        """ Initialize Window """
        self.tkroot = root
        self.tkroot.protocol('WM_DELETE_WINDOW', self.exitwindow) # Close serial connection and close window

        """ Initialize variables for color interpolation """
        self.HUEstart= 0.5 #initial color for min temp (0.5 = blue)
        self.HUEend = 1 #initial color for max temp (1 = red)
        self.HUEspan = self.HUEend - self.HUEstart
        
        """ Grid Eye related variables"""
        self. MULTIPLIER = 0.25 # temp output multiplier
        
        """ Initialize Loop bool"""
        self.START = False
              
        """Initialize frame tor temperature array (tarr)"""
        self.frameTarr = tk.Frame(master=self.tkroot, bg='white')
        self.frameTarr.place(x=5, y=5, width = 400, height = 400)
        
        """Initialize pixels tor temperature array (tarr)"""
        self.tarrpixels = []
        for i in range(8):
            #frameTarr.rowconfigure(i,weight=1) # self alignment
            #frameTarr.columnconfigure(i,weight=1) # self alignment
            for j in range(8):
                pix = tk.Label(master=self.frameTarr, bg='gray', text='11')
                spacerx = 1
                spacery = 1
                pixwidth = 40
                pixheight = 40
                pix.place(x=spacerx+j*(spacerx+pixwidth), y=spacery+i*(pixheight+spacery),  width = pixwidth, height = pixheight)
                print 
                self.tarrpixels.append(pix) # attache all pixels to tarrpixel list
    
        """Initialize frame tor Elements"""
        self.frameElements = tk.Frame(master=self.tkroot, bg='white')
        self.frameElements.place(x=410, y=5, width = 100, height = 400)
        

        """Initialize controll buttons"""
        self.buttonStart = tk.Button(master=self.frameElements, text='start', bg='white',
                                 command=self.start_update)
        self.buttonStart.pack()
        self.buttonStop = tk.Button(master=self.frameElements, text='stop', bg='white',
                                 command=self.stop_update)
        self.buttonStop.pack()
        
        """Initialize temperature adjustment"""
        self.lableTEMPMAX = tk.Label(master=self.frameElements, text='Max Temp (red)')
        self.lableTEMPMAX.pack()
        self.MAXTEMP = tk.Scale(self.frameElements, from_=-20, to=120, resolution =0.25)
        self.MAXTEMP.set(31)
        self.MAXTEMP.pack()
        self.lableMINTEMP = tk.Label(master=self.frameElements, text='Min Temp (blue)')
        self.lableMINTEMP.pack()
        self.MINTEMP = tk.Scale(self.frameElements, from_=-20, to=120, resolution =0.25)
        self.MINTEMP.set(27)
        self.MINTEMP.pack()
        
        self.kit = GridEYEKit()
                 
    def exitwindow(self):
        """ if windwow is clsoed, serial connection has to be closed!"""
        self.kit.close()
        self.tkroot.destroy()
        
    def stop_update(self):
        """ stop button action - stops infinite loop """
        self.START = False
        self.update_tarrpixels()


    def start_update(self):
        if self.kit.connect():
            """ start button action -start serial connection and start pixel update loop"""
            self.START = True
            """ CAUTION: Wrong com port error is not handled"""
            self.update_tarrpixels()  
        else:
            tkMessageBox.showerror("Not connected", "Could not find Grid-EYE Eval Kit - please install driver and connect")
            
        
    def get_tarr(self):
        """ unnecessary function - only converts numpy array to tuple object"""
        tarr = []
        for temp in self.kit.get_temperatures(): # only fue to use of old rutines
            for temp2 in temp:
                tarr.append(temp2)
        return tarr
        
    def update_tarrpixels(self):
        """ Loop for updating pixels with values from funcion "get_tarr" - recursive function with exit variable"""
        if self.START == True:
            tarr = self.get_tarr() # Get temerature array
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
                        print h
                        print normtemp
                        print self.HUEspan
                        print self.HUEstart
                    bgrgb = tuple(255*j for j in colorsys.hsv_to_rgb(h,1,1)) # convert to RGB colors
                    tarrpix.config(bg=('#%02x%02x%02x' % bgrgb)) # Convert to Hex String
                    i +=1  # incement tarr counter
            else:
                print "Error - temperarure array lenth wrong"
            self.frameTarr.after(10,self.update_tarrpixels) # recoursive function call all 10 ms (get_tarr will need about 100 ms to respond)



root = tk.Tk()
root.title('Grid-Eye Viewer')
root.geometry('500x450')        
Window = GridEYE_Viewer(root)
root.mainloop()
