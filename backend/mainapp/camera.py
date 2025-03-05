from picamera2 import Picamera2
import RPi.GPIO as GPIO
# Toggle IR LED (ON or OFF)

# Setup GPIO mode
GPIO.setmode(GPIO.BCM)

# Set the GPIO pin that controls the IR LED
IR_LED_PIN = 17  # Change this pin number to match your setup
GPIO.setup(IR_LED_PIN, GPIO.OUT)

# init camera
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (800, 600)}))
picam2.start()

def turn_ir_on():
    GPIO.output(IR_LED_PIN, GPIO.HIGH)

def turn_ir_off():
    GPIO.output(IR_LED_PIN, GPIO.LOW)

def get_ir_led_state():
    GPIO.input(IR_LED_PIN)
