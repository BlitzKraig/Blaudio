import serial
import threading
import time
from collections import deque
import numpy as np
from PyQt6.QtCore import QTimer

class SerialReader:
    def __init__(self, port, callback, baudrate=9600, callback_interval=0.05, smoothing_window=10, old_range=(0, 1023), new_range=(0, 100), retry_interval=5):
        self.old_min, self.old_max = old_range
        self.new_min, self.new_max = new_range
        self.port = port
        self.baudrate = baudrate
        self.retry_interval = retry_interval
        self.callback = callback
        self.callback_interval = callback_interval
        self.knobs = {}
        self.knob_buffers = {}
        self.smoothing_window = smoothing_window
        self.last_callback_time = time.time()
        
        self.is_connected = False

        self.timer = QTimer()
        self.timer.timeout.connect(self.try_connect)
        self.try_connect()
        self.timer.start(retry_interval * 1000)
        

    def try_connect(self):
        if self.is_connected:
            return
        print("Trying to connect to the serial port...")
        try:
            self.ser = serial.Serial(self.port, self.baudrate)
            self.thread = threading.Thread(target=self.read_from_port)
            self.thread.daemon = True
            self.thread.start()
            # self.timer.stop()  # Stop the timer once connected ~ Not stopping, as we're using this to keep us connected now
            print("Connected to the serial port")
            self.is_connected = True
        except serial.SerialException:
            print("Failed to connect to the serial port. Retrying in {} seconds...".format(self.retry_interval))
            self.is_connected = False
            
    def read_from_port(self):
        
        while True:
            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8').strip()
                    values = line.split('|')
                    for i, value in enumerate(values):
                        if i not in self.knob_buffers:
                            self.knob_buffers[i] = deque(maxlen=self.smoothing_window)
                        self.knob_buffers[i].append(int(value))
                        old_avg = np.mean(self.knob_buffers[i])
                        new_avg = (old_avg - self.old_min) / (self.old_max - self.old_min) * (self.new_max - self.new_min) + self.new_min
                        self.knobs[i] = int(np.rint(new_avg))  # round the average to the nearest integer
                    
                    current_time = time.time()
                    if current_time - self.last_callback_time > self.callback_interval:
                        self.callback(self.knobs)
                        self.last_callback_time = current_time
            except serial.SerialException:
                print("SerialException occurred. Stopping reader.")
                self.is_connected = False
                break