import socket
import struct
import RPi.GPIO as GPIO

from ignore_motion import ignore_motion_for

import csv
import datetime
import os
import threading

from gpiozero import MotionSensor

import time
import board
import adafruit_sht4x

# replace this with custom email-interface
from unibe_mail import Reporter
import cv2

from encoding import encode_email
from ignore_motion import are_we_still_blocked

# Import your Django model
from camera import camera_stream, turn_ir_on, turn_ir_off, get_ir_led_state

# I2C sensor setup
i2c = board.I2C()
sensor = adafruit_sht4x.SHT4x(i2c)

# GPIO Motion Sensor Setup
MOTION_PIN = 4
pir = MotionSensor(MOTION_PIN, threshold=0.8, queue_len=10)

# email callback

# replace this with custom email-interface
Voegeli = Reporter("Voegeli")


# Function to read temperature and humidity
def read_temperature_humidity():
    temperature = round(sensor.temperature, 2)
    humidity = round(sensor.relative_humidity, 2)
    return temperature, humidity


class CameraServer:
    def __init__(self, stream_ip='0.0.0.0', stream_port=5005, tcp_port=6006, ir_led_pin=17):
        self.stream_ip = stream_ip
        self.stream_port = stream_port
        self.tcp_port = tcp_port
        self.ir_led_pin = ir_led_pin

        self.tcp_socket = None
        self.tcp_conn = None
        self.tcp_lock = threading.Lock()

        # Path to the CSV file where emails are stored
        self.subscriber_file_path = 'newsletter_subscribers.csv'

        pir.when_motion = self.motion_detected_callback
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.ir_led_pin, GPIO.OUT)
        GPIO.output(self.ir_led_pin, GPIO.LOW)
        ignore_motion_for(10)

    def motion_detected_callback(self):

        # Check if motion detection should be ignored
        if are_we_still_blocked():
            print("Motion detection temporarily ignored.")
            return
        if get_ir_led_state():
            print("Motion detection ignored because IR LED is on.")
            return

        temperature, humidity = read_temperature_humidity()
        self.send_tcp_message(f"MOTION INTERRUPT! TEMP_HUM: {temperature}, {humidity}")

        current_time = time.time()

        # Send an email only if at least a day has passed
        file_path = "last_email_sent.txt"

        # Read the existing timestamp or initialize it
        try:
            with open(file_path, "r+") as f:
                content = f.readline().strip()
                last_email_time = int(content) if content else 0  # Convert to int, default to 0 if empty
                if current_time - last_email_time >= 86400:
                    try:
                        csv_file = 'newsletter_subscribers.csv'
                        with open(csv_file, mode='r') as file:
                            reader = csv.reader(file)
                            subscribers = list(reader)
                            for subscriber in subscribers:
                                email = subscriber[0]
                                encoded_email = encode_email(email)

                                base_url = "https://linusleo.synology.me/voegeli"
                                unsubscribe_link = f"{base_url}/unsubscribe/{encoded_email}/"
                                email_body = (
                                    "Hoi Du!<br>"
                                    "I just came back and entered my birdhouse!<br>"
                                    f"Check me out at {base_url}<br>"
                                    "Best Regards, Your Vögeli<br><br>"
                                    f'<a href="{unsubscribe_link}">Unsubscribe</a>'
                                )

                                Voegeli.send_mail(
                                    email_body,
                                    subject="Vögeli Motion Alert",
                                    recipients=email,
                                    is_html=True,
                                )
                    except FileNotFoundError:
                        pass  # File does not exist yet, no subscribers
                    # Overwrite with the new timestamp
                    f.seek(0)  # Move to the beginning of the file
                    new_timestamp = int(current_time)
                    f.write(str(new_timestamp))
                    f.truncate()  # Remove any leftover content after the new write
        except FileNotFoundError:
            # If the file doesn't exist, create it and write the timestamp
            with open(file_path, "w") as f:
                new_timestamp = int(current_time)
                last_email_time = 0
                f.write(str(new_timestamp))

        print("Motion detected! Data stored.")

    def start(self):
        video_thread = threading.Thread(target=self.stream_video, daemon=True)
        tcp_thread = threading.Thread(target=self.tcp_server, daemon=True)

        video_thread.start()
        tcp_thread.start()

        print("[INFO] Server running. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[INFO] Shutting down.")
        finally:
            GPIO.cleanup()
            if self.tcp_conn:
                self.tcp_conn.close()

    def stream_video(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((self.stream_ip, self.stream_port))
        sock.listen(1)

        time.sleep(2)  # Warm-up camera
        while True:
            print("Waiting for client to connect...")
            client_socket, client_address = sock.accept()
            print(f"Client connected: {client_address}")
            with client_socket:
                while True:

                    # Capture the frame (600x800 pixels, 3 bytes per pixel)
                    jpeg_data = camera_stream.get_jpeg()
                    if jpeg_data is None:
                        print("... skipped a frame!")
                        time.sleep(0.05)
                        continue
    
                    try:
                        client_socket.sendall(struct.pack("L", len(jpeg_data)))
                        client_socket.sendall(jpeg_data)
                    except Exception as e:
                        print(f"Error sending data: {e}")
                        break  # Stop streaming if the cli

                    time.sleep(0.01)  # Small delay between frames to avoid overwhelming the network

    # Read the current list of emails from the CSV file
    def read_email_list(self):
        try:
            with open(self.subscriber_file_path, mode='r') as file:
                reader = csv.reader(file)
                return [row[0] for row in reader]
        except FileNotFoundError:
            return []

    # Write the email list back to the CSV file
    def write_email_list(self, email_list):
        with open(self.subscriber_file_path, mode='w') as file:
            writer = csv.writer(file)
            for email in email_list:
                writer.writerow([email])

    def handle_command(self, command):
        command = command.strip()
        print(f"[CMD] Received: {command}")
        if command == "IR_ON":
            turn_ir_on()
        elif command == "IR_OFF":
            turn_ir_off()
        elif command == "GET_IR":
            state = get_ir_led_state()
            self.send_tcp_message(f"IR LED is {'ON' if state else 'OFF'}")
        elif command == "GET_SENSOR_DATA":
            temperature, humidity = read_temperature_humidity()
            self.send_tcp_message(f"TEMP_HUM: {temperature}, {humidity}")
        elif "ADD_EMAIL" in command:
            email = command.split(":")[1].strip()
            email_list = self.read_email_list()

            # Check if the email is valid
            if email and email not in email_list:
                email_list.append(email)
                self.write_email_list(email_list)

                # Success message
                self.send_tcp_message(f"ok, email added: {email}")
            else:
                # Error message if email is empty or already exists
                self.send_tcp_message(f"error, adding email: {email}")
        elif "REMOVE_EMAIL" in command:
            email = command.split(":")[1].strip()
            email_list = self.read_email_list()

            if email in email_list:
                email_list.remove(email)
                self.write_email_list(email_list)
                self.send_tcp_message(f"ok, removed added: {email}")
            else:
                self.send_tcp_message(f"error, removing email: {email}")
        elif "GET_SUBSCRIBER_COUNT" in command:
            # Read the current subscribers from the CSV file
            subscriber_count = 0
            try:
                with open(self.subscriber_file_path, mode='r') as file:
                    reader = csv.reader(file)
                    subscribers = list(reader)
                    subscriber_count = len(subscribers)
            except FileNotFoundError:
                pass  # File does not exist yet, no subscribers
            self.send_tcp_message(f"ok, subscriber count:{subscriber_count}")
        else:
            self.send_tcp_message(f"[CMD] Unknown command: {command}")
            print(f"[CMD] Unknown command: {command}")

    def send_tcp_message(self, message):
        if self.tcp_conn:
            try:
                with self.tcp_lock:
                    self.tcp_conn.sendall(message.encode('utf-8'))
                    print(f"[TCP] Sent: {message}")
            except Exception as e:
                print(f"[TCP] Send failed: {e}")

    def tcp_server(self):
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.bind(('0.0.0.0', self.tcp_port))
        self.tcp_socket.listen(1)
        print(f"[TCP] Listening on port {self.tcp_port}...")

        while True:
            self.tcp_conn, addr = self.tcp_socket.accept()
            print(f"[TCP] Connection from {addr}")
            with self.tcp_conn:
                while True:
                    try:
                        data = self.tcp_conn.recv(1024)
                        if not data:
                            break
                        command = data.decode('utf-8')
                        self.handle_command(command)
                    except Exception as e:
                        print(f"[TCP] Error: {e}")
                        break
            self.tcp_conn = None


if __name__ == '__main__':
    server = CameraServer()
    server.start()
