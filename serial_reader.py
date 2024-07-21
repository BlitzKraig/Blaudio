import serial
import threading
import time
from collections import deque
import numpy as np
from PyQt6.QtCore import QTimer

MINIMUM_HARDWARE_VERSION = 1

class SerialReader:
    def __init__(self, port, callback, message_callback, baudrate=9600, callback_interval=0.02, smoothing_window=10, old_range=(0, 1023), new_range=(0, 100), retry_interval=5):
        self.old_min, self.old_max = old_range
        self.new_min, self.new_max = new_range
        self.port = port
        self.baudrate = baudrate
        self.retry_interval = retry_interval
        self.callback = callback
        self.message_callback = message_callback
        self.callback_interval = callback_interval
        self.buttons = {}
        self.knobs = {}
        self.knob_buffers = {}
        self.smoothing_window = smoothing_window
        self.last_callback_time = time.time()
        
        self.is_connected = False
        
        self.heartbeat_message = "BLAUDIO_HEARTBEAT\n"

        self.timer = QTimer()
        self.timer.timeout.connect(self.try_connect)
        self.try_connect()
        self.timer.start(retry_interval * 1000)
        
    def send_heartbeat(self):
        try:
            self.ser.write(self.heartbeat_message.encode())
            print("Heartbeat sent.")
        except serial.SerialException:
            print("Failed to send heartbeat.")
            
    def try_connect(self):
        if self.is_connected:
            self.send_heartbeat()
            return
        print("Trying to connect to {}".format(self.port))
        try:
            # Try to close the serial port
            try:
                self.ser.close()
            except:
                pass
            self.ser = serial.Serial(self.port, self.baudrate)
            self.thread = threading.Thread(target=self.read_from_port)
            self.thread.daemon = True
            self.thread.start()
            # self.timer.stop()  # Stop the timer once connected ~ Not stopping, as we're using this to keep us connected now
            print("Connected to {}".format(self.port))
            self.is_connected = True
        except serial.SerialException:
            print("Failed to connect to the serial port. Retrying in {} seconds...".format(self.retry_interval))
            self.is_connected = False
            
    def read_from_port(self):
        
        while True:
            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8').strip()
                    # Example line: VER1#BUTTON1|2|3#KNOB1|2#
                    try:
                        version_line = int(line.split('VER')[1].split('#')[0])
                        if(version_line < MINIMUM_HARDWARE_VERSION):
                            message = "Incompatible HW. Current: {}. Required: {}.".format(version_line, MINIMUM_HARDWARE_VERSION)
                            print(message)
                            self.message_callback(message)
                            self.is_connected = False
                            break
                        
                        knob_line = line.split('KNOB')[1].split('#')[0]
                        knob_values = knob_line.split('|')
                        for i, value in enumerate(knob_values):
                            if i not in self.knob_buffers:
                                self.knob_buffers[i] = deque(maxlen=self.smoothing_window)
                            self.knob_buffers[i].append(int(value))
                            old_avg = np.mean(self.knob_buffers[i])
                            new_avg = (old_avg - self.old_min) / (self.old_max - self.old_min) * (self.new_max - self.new_min) + self.new_min
                            self.knobs[i] = int(np.rint(new_avg))  # round the average to the nearest integer
                            
                        button_line = line.split('BTN')[1].split("#")[0]
                        button_values = button_line.split('|')
                        for i, value in enumerate(button_values):
                            self.buttons[i] = int(value)
                    except IndexError as e:
                        print("IndexError occurred. Skipping line.")
                        print(e)
                        pass
                    
                    current_time = time.time()
                    if current_time - self.last_callback_time > self.callback_interval:
                        self.callback(self.knobs, self.buttons)
                        self.last_callback_time = current_time
            except serial.SerialException:
                print("SerialException occurred. Stopping reader.")
                self.is_connected = False
                break
            except Exception as e:
                print("An error occurred: {}".format(e))
                self.is_connected = False
                break