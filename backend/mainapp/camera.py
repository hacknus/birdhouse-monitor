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

ir_led_state = False

def turn_ir_on():
    global ir_led_state
    ir_led_state = True
    GPIO.output(IR_LED_PIN, GPIO.HIGH)

def turn_ir_off():
    global ir_led_state
    GPIO.output(IR_LED_PIN, GPIO.LOW)
    ir_led_state = False

def get_ir_led_state():
    global ir_led_state
    return ir_led_state
