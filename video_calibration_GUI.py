# -*- coding: utf-8 -*-
"""
Created on Mon 12/27/2021

@author: luh6r

Goal: collect more than 3 point for each pixel and compute the line
Including: 
    1. GUI 
        a. show the real time RGB image and ToF readings,
        b. a click button to pop out the current frame need to be marked
        c. entry line to show the pixel number
    2. RGB frame
        click to mark the pixel location
        
"""
from __future__ import print_function
from PIL import Image
from PIL import ImageTk
import tkinter as tki
import threading
import datetime
import imutils
import cv2
import os
import ctypes as ct
import RPi.GPIO as GPIO
import numpy as np
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

def getDf():
    df = os.popen("df -h /")
    i = 0
    while True:
        i = i + 1
        line = df.readline()
        if i==2:
            return(line.split()[0:6])


class PhotoBoothApp:
    mode = 4
    frame_rate = 15

    def __init__(self, vs):
        # store the video stream object and output path, then initialize
		# the most recently read frame, thread for reading frames, and
		# the thread stop event
        
        # video
        self.vs = vs
        self.frame = None
        
        # ToF
        self.tof = TOFRanging(self.mode, self.frame_rate)
        self.result = None

        # threads: 
        self.thread = None  # video
        self.thread_tof = None # ToF save
        self.thread_plot = None # ToF plot
        self.stopEvent = None # stop event
        
        #save video
        self.out = None # video output object

        #save the line's parameter A,B,C respond to the tof pixel
        self.tof_pixel_order = 0
        self.tof_pixel_points = dict()
        self.tof_pixel_line = dict()


        # initialize the root window and image panel
        self.root = tki.Tk()
        self.panel = None
        self.panel_tof = None
        
        # create a button, that when pressed, will take the current
		# frame and save it to file
        self.btn_st = ["Click to mark the pixel location", "Current Frame, please mark the pixel","..."]
        self.btn_st_idx = 0 # this can be 0,1

        # button
        self.btn = tki.Button(self.root, text=self.btn_st[self.btn_st_idx], command=self.btn_fun)
        self.btn.pack(side="bottom", fill="both", expand="yes", padx=10, pady=10)
        
        # hint to enter name
        self.Message = tki.Label(text="Please enter the pixel order of ToF here (0~15)")
        self.Message.pack(side="bottom", fill="both", expand="yes", padx=10, pady=10)
        
        # enter name
        self.entry = tki.Entry()
        self.entry.pack(side="bottom", fill="both", expand="yes", padx=10, pady=10)
        
        self.btn_save = tki.Button(self.root, text="Click to save the pixels", command=self.btn_save_fun)
        self.btn_save.pack(side="bottom", fill="both", expand="yes", padx=10, pady=10)

        # enter the seconds // 
        #self.second_entry = tki.Entry()
        #self.second_entry.pack(side="bottom", fill="both", expand="yes", padx=10, pady=10)
        
        # hint to enter time
        #self.second_Message = tki.Label(text="Please enter testing time (seconds) here")
        #self.second_Message.pack(side="bottom", fill="both", expand="yes", padx=40, pady=40)
        
        # Clock
        self.Time = tki.Label(text = "")
        self.Time.pack(side="bottom", fill="both", expand="yes", padx=40, pady=40)
        self.update_clock()
        
        
		# start a thread that constantly pools the video sensor for
		# the most recently read frame
        self.stopEvent = threading.Event()
        self.thread = threading.Thread(target=self.videoLoop, args=())
        self.thread.start()
        
        self.thread_plot = threading.Thread(target=self.ToF_plot, args=())
        self.thread_plot.start()
        
        self.thread_tof = threading.Thread(target = self.w_tof, args=())
        self.thread_tof.start()
        
		# set a callback to handle when the window is closed
        self.root.wm_title("Distance Data Collection App")
        self.root.wm_protocol("WM_DELETE_WINDOW", self.onClose)
    
    def ToF_plot(self):
        '''
        show the tof views
        show the memory left too.
        '''
        while not self.stopEvent.is_set():
            result = self.tof.result/3000*255
            resized_result = cv2.resize(result, (400,400), interpolation = cv2.INTER_AREA)
            
            font = cv2.FONT_HERSHEY_SIMPLEX
            fontScale = 1
            color = (255, 0, 0) # Blue color in BGR
            thickness = 1 # Line thickness of 2 px
            for i in range(4):
                for j in range(4):
                    org = (i*100, j*100)
                    # Using cv2.putText() method
                    resized_result = cv2.putText(resized_result, str(result[i,j]), org, font, 
                                    fontScale, color, thickness, cv2.LINE_AA)
            
            image_tof = Image.fromarray(resized_result)
            image_tof = ImageTk.PhotoImage(image_tof)
            # if the panel is not None, we need to initialize it
            if self.panel_tof is None:
                self.panel_tof = tki.Label(image=image_tof)
                self.panel_tof.image = image_tof
                self.panel_tof.pack(side="right", fill=tki.BOTH, expand=tki.YES)

            # otherwise, simply update the panel
            else:
                self.panel_tof.configure(image=image_tof)
                self.panel_tof.image = image_tof
            
            dist_root = getDf()
            
        
    def update_clock(self):
        now = time.strftime("%H:%M:%S")
        self.Time.configure(text=now)
        self.root.after(1000, self.update_clock)
    
   
    def videoLoop(self):
		# DISCLAIMER:
		# I'm not a GUI developer, nor do I even pretend to be. This
		# try/except statement is a pretty ugly hack to get around
		# a RunTime error that Tkinter throws due to threading
        try:
			# keep looping over frames until we are instructed to stop
            while not self.stopEvent.is_set():
				# grab the frame from the video stream and resize it to
				# have a maximum width of 300 pixels
                self.frame = self.vs.read()
                self.frame = imutils.resize(self.frame, width=300)
                height, width, layers = self.frame.shape
                size = (width,height)
                
                if self.btn_st_idx == 1:
                    self.out = cv2.VideoWriter(self.folderName +"/" +self.name + '.avi',cv2.VideoWriter_fourcc(*'DIVX'), 45, size)
                elif self.btn_st_idx == 2 or self.btn_st_idx == 3:
                    self.out.write(self.frame)
                else:
                    if self.out is not None:
                        try:
                            self.out.release()
                        except RuntimeError:
                            print("[INFO] can't release video writing flow")
				# OpenCV represents images in BGR order; however PIL
				# represents images in RGB order, so we need to swap
				# the channels, then convert to PIL and ImageTk format
                image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(image)
                image = ImageTk.PhotoImage(image)
		
				# if the panel is not None, we need to initialize it
                if self.panel is None:
                    self.panel = tki.Label(image=image)
                    self.panel.image = image
                    self.panel.pack(side="left", padx=10, pady=10)
		
				# otherwise, simply update the panel
                else:
                    self.panel.configure(image=image)
                    self.panel.image = image
                    
        except RuntimeError:
            print("[INFO] caught a RuntimeError")
            
    def btn_fun(self):

        if self.btn_st_idx == 0: # state 0 : enter time and name
            self.tof_pixel_order = self.entry.get()

            if self.tof_pixel_order not in self.tof_pixel_points:
                self.tof_pixel_points[self.tof_pixel_order] = []
                self.tof_pixel_line[self.tof_pixel_order] = []
            
            self.btn_st_idx = 1
            
        elif self.btn_st_idx == 1: # state 1 : click to record data
            cv2.imshow('img_show', self.frame)
            cv2.setMouseCallback('img_show', self.click_event)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            self.btn_st_idx = 0
                    
        else: # reset
            self.btn_st_idx = 0
                        
        self.btn['text'] = self.btn_st[self.btn_st_idx]
        
    def btn_save_fun(self):

        f_name = 'pixels.txt'
        with open(f_name, "a") as f:
            for i in self.tof_pixel_points:
                f.write(str(i))
                f.write(" : ")
                for pixels in self.tof_pixel_points[i]:
                    f.write("(")
                    f.write(str(pixels[0]))
                    f.write(",")
                    f.write(str(pixels[1]))
                    f.write(")")
                    f.write(" ")
                f.write("\n")

    def click_event(self, event, x, y, flags, params):
        global point_list

        if event == cv2.EVENT_LBUTTONDOWN:
            print(x, " ", y)
            self.tof_pixel_points[self.tof_pixel_order].append((x,y))
            cv2.circle(self.frame,(x,y),3,(255,0,0),-1)
            cv2.imshow('img_show',self.frame)

        if event == cv2.EVENT_RBUTTONDOWN:
            pass

        
    def onClose(self):
		# set the stop event, cleanup the camera, and allow the rest of
		# the quit process to continue
        print("[INFO] closing...")
        self.stopEvent.set()
        self.vs.stop()
        self.tof.EndToF()
        #self.out.release()
        time.sleep(0.5)
        self.root.quit()
        self.root.destroy()
        os._exit(0)
        

class TOFRanging:
    
    ranging = ct.CDLL("/home/pi/VL53L5CX_Linux_driver_1.1.0/user/ranging/range.so")
        
    def __init__(self, mode, frame_rate):
        # Power up Time of Flight sensor
        self.StartTOF()
        # Set frame rate and working mode (using C type formats for ToF driver)
        self.frame_rate = ct.c_int(frame_rate)
        self.mode = mode
        self.result = np.zeros((self.mode,self.mode))
        self.status = np.zeros((self.mode, self.mode))
        if mode == 4:
            self.Is_4x4 = ct.c_bool(True) 
            self.Mod = ct.c_int(4)
        elif mode == 8:
            self.Is_4x4 = ct.c_bool(False)
            self.Mod = ct.c_int(8)
        else:
            print("error ToF working mode")
            self.FreeGPIO()
            os._exit(0)    
        self.p_dev = None
        self.Ranging_ini()
        
    def StartTOF(self):
        # Power up TOF
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(27,GPIO.OUT)
        GPIO.output(27,1)


    def Ranging_ini(self):
        # Initial ToF and prepare for ranging
        class PResult(ct.Structure):
            _fields_ = [("result",ct.c_int16*(64)),
                        ("status",ct.c_uint8*(64))]
            
        self.ranging.ranging.restype = ct.POINTER(PResult)
        self.p_dev = self.ranging.ranging_ini(self.Is_4x4,self.frame_rate)
    
    def Ranging(self):
        # Ranging 
        p_result = self.ranging.ranging(self.p_dev,self.Mod)
        self.result = np.reshape(p_result.contents.result[:self.mode**2],(self.mode,self.mode))
        self.status = np.reshape(p_result.contents.status[:self.mode**2],(self.mode,self.mode))
    
    def StopRanging(self):
        # Stop ranging
        status = self.ranging.StopRanging(self.p_dev)

    def FreeGPIO(self):
        # Free all GPIO sets in this script
        GPIO.cleanup()

    def EndToF(self):
        # fast end
        self.StopRanging()
        self.FreeGPIO()
    
    def SaveRangeData(self, fileName):
        # save the range data in to file "fileName"
        with open(fileName, "a") as f:
            np.savetxt(f, self.result, fmt='%5d')
            f.write("\n")        
        
# from pyimagesearch.photoboothapp import PhotoBoothApp
from imutils.video import VideoStream
import argparse
import time
import RPi.GPIO as GPIO


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
# ap.add_argument("-o", "--output", required=True, help="path to output directory to store snapshots")
ap.add_argument("-p", "--picamera", type=int, default=-1, help="whether or not the Raspberry Pi camera should be used")
args = vars(ap.parse_args())
# initialize the video stream and allow the camera sensor to warmup
GPIO.setmode(GPIO.BCM)
GPIO.setup(27,GPIO.OUT)
GPIO.output(27,1)
print("VL53L5cx opened")
print("[INFO] warming up camera...")
vs = VideoStream(usePiCamera=args["picamera"] > 0).start()
time.sleep(0.5)
# start the app
pba = PhotoBoothApp(vs)
pba.root.mainloop()
        