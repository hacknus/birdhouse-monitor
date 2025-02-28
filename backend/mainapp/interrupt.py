# import RPi.GPIO as GPIO
# import time
# from threading import Thread
# from unibe_mail import Reporter
#
# Voegeli = Reporter("Vögeli")
#
# # Set up the GPIO pin for motion sensor
# MOTION_SENSOR_PIN = 17  # Change this if your sensor is connected to a different pin
#
# # Setup for GPIO
# GPIO.setmode(GPIO.BCM)  # Use Broadcom pin numbering
# GPIO.setup(MOTION_SENSOR_PIN, GPIO.IN)
#
# # This will hold the motion detected state
# motion_detected = False
#
#
# # Define the function that will handle the motion detection interrupt
# def motion_detected_callback(channel):
#     global motion_detected
#     motion_detected = True
#
#     for subscriber in subscribers:
#         Voegeli.send_mail(f"Hoi Du!\n Motion Detected! \nBest Regards, Your Vögeli", subject="Vögeli Motion Alert",
#                           recipients=subscriber)
#
#
# # Set up the interrupt to listen for motion detection
# GPIO.add_event_detect(MOTION_SENSOR_PIN, GPIO.RISING, callback=motion_detected_callback, bouncetime=300)
#
#
# # Function to keep the script running and prevent it from terminating
# def listen_for_motion():
#     try:
#         while True:
#             # Add any other logic here if needed
#             if motion_detected:
#                 # Reset motion detection flag after handling
#                 motion_detected = False
#                 time.sleep(0.1)  # Optional: Sleep to prevent high CPU usage in the loop
#             time.sleep(0.1)  # Polling every 100ms
#     except KeyboardInterrupt:
#         print("Program interrupted by user.")
#     finally:
#         # Clean up GPIO settings before exiting
#         GPIO.cleanup()
#
#
# # Start the motion detection listener in a separate thread to avoid blocking
# motion_listener_thread = Thread(target=listen_for_motion)
# motion_listener_thread.daemon = True  # Make the thread exit when the main program exits
# motion_listener_thread.start()
#
# # Keep the main program running to listen for interrupts
# try:
#     while True:
#         time.sleep(1)  # Main thread can be doing something else
# except KeyboardInterrupt:
#     print("Exiting...")
#     GPIO.cleanup()
