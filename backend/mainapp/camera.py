import time

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
# init camera
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (800, 600)}))
picam2.start()

# picam2.set_controls({"AwbEnable": True, "AwbMode": 7})  # Try values: 0 (auto), 1 (incandescent), 2 (tungsten), etc.
picam2.set_controls({"AwbEnable": False, "ColourGains": (1.2, 2.0)})  # Adjust the 1.0 (red) and 2.5 (blue) values

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
