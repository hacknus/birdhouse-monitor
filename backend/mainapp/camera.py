import logging
import time

import libcamera
import numpy as np
from picamera2 import Picamera2
import RPi.GPIO as GPIO

from .ignore_motion import ignore_motion_for

# Toggle IR LED (ON or OFF)

# Setup GPIO mode
GPIO.setmode(GPIO.BCM)

# Set the GPIO pin that controls the IR LED
IR_LED_PIN = 17  # Change this pin number to match your setup
GPIO.setup(IR_LED_PIN, GPIO.OUT)
ignore_motion_for(10)
GPIO.output(IR_LED_PIN, GPIO.LOW)

# Set tuning for ov5647_noir
tuning = Picamera2.load_tuning_file("ov5647_noir.json")
algo = Picamera2.find_tuning_algo(tuning, "rpi.agc")
if "channels" in algo:
    algo["channels"][0]["exposure_modes"]["normal"] = {"shutter": [100, 66666], "gain": [1.0, 8.0]}
else:
    algo["exposure_modes"]["normal"] = {"shutter": [100, 66666], "gain": [1.0, 8.0]}

picam2 = Picamera2(tuning=tuning)

print(picam2.camera)
picam2.configure(picam2.create_preview_configuration(main={"format": 'RGB888', "size": (800, 600)}))
print(picam2.camera)
picam2.start()
print(picam2.camera)

ir_led_state = False

def turn_ir_on():
    global ir_led_state
    ir_led_state = True
    GPIO.output(IR_LED_PIN, GPIO.HIGH)

def turn_ir_off():
    ignore_motion_for(10)
    global ir_led_state
    ir_led_state = False
    GPIO.output(IR_LED_PIN, GPIO.LOW)


def get_ir_led_state():
    global ir_led_state
    time.sleep(0.1)
    return ir_led_state
