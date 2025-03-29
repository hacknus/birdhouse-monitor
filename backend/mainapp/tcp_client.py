# utils/tcp_client.py
import socket
import threading
import time
import queue
import datetime
import os
import cv2
import numpy as np
from django.conf import settings
from django.db.utils import OperationalError
import sqlite3


class TCPClient:
    def __init__(self, ip_file='mainapp/raspberry_pi_ip.txt', port=6006, udp_client=None):
        self.ip_file = ip_file
        self.port = port
        self.socket = None
        self.connected = False
        self.lock = threading.Lock()
        self.running = False
        self.receive_callback = None
        self.thread = None
        self.reply_queue = None
        self.udp_client = udp_client  # <-- pass your UDP client here
        self.interrupt_event = threading.Event()

    def read_ip_from_file(self):
        try:
            with open(self.ip_file, 'r') as file:
                return file.readline().strip()
        except Exception as e:
            print(f"[TCPClient] Error reading IP file: {e}")
            return None

    def connect_loop(self):
        self.running = True

        # Start sensor polling thread
        threading.Thread(target=self.sensor_polling_loop, daemon=True).start()

        while self.running:
            ip_address = self.read_ip_from_file()
            if not ip_address:
                time.sleep(2)
                continue

            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(5)
                    sock.connect((ip_address, self.port))
                    with self.lock:
                        self.socket = sock
                        self.connected = True

                    while self.running:
                        try:
                            data = sock.recv(1024)
                            if not data:
                                break
                            message = data.decode('utf-8')
                            self.receive_callback_internal(message)
                        except socket.error:
                            break

            except (socket.timeout, socket.error) as e:
                print(f"[TCPClient] Connection failed: {e}")

            with self.lock:
                self.socket = None
                self.connected = False
            time.sleep(2)

    def start(self):
        if not self.thread or not self.thread.is_alive():
            self.thread = threading.Thread(target=self.connect_loop, daemon=True)
            self.thread.start()

    def send(self, message):
        with self.lock:
            if self.socket and self.connected:
                try:
                    self.socket.sendall(message.encode('utf-8'))
                except socket.error as e:
                    print(f"[TCPClient] Send failed: {e}")

    def send_and_wait_for_reply(self, message, timeout=5):
        self.reply_queue = queue.Queue(maxsize=1)
        self.send(message)
        try:
            return self.reply_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def stop(self):
        self.running = False
        with self.lock:
            if self.socket:
                self.socket.close()
                self.socket = None
                self.connected = False

    def set_receive_callback(self, callback_fn):
        self.receive_callback = callback_fn

    def receive_callback_internal(self, message):
        if "INTERRUPT" in message:
            print("[TCPClient] INTERRUPT received — saving image")
            _, values = message.strip().split(":")
            temp, hum = values.split(",")
            self.store_sensor_data(float(temp), float(hum), motion_triggered=True)
            threading.Thread(target=self.handle_interrupt, daemon=True).start()
        elif message.startswith("TEMP_HUM"):
            _, values = message.strip().split(":")
            temp, hum = values.split(",")
            self.store_sensor_data(float(temp), float(hum), motion_triggered=False)
        elif self.reply_queue and not self.reply_queue.full():
            try:
                self.reply_queue.put_nowait(message)
            except queue.Full:
                pass

        if self.receive_callback:
            self.receive_callback(message)

    def handle_interrupt(self):
        self.send("IR_ON")
        time.sleep(3)

        frame_data = self.udp_client.get_frame() if self.udp_client else None
        if frame_data:
            np_frame = np.frombuffer(frame_data, dtype=np.uint8)
            frame = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            image_path = os.path.join(settings.MEDIA_ROOT, "gallery", f"{timestamp}.jpg")
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            cv2.imwrite(image_path, frame)
            print(f"[TCPClient] Saved image at {image_path}")
        else:
            print("[TCPClient] No UDP frame available.")

        self.send("IR_OFF")

    def sensor_polling_loop(self):
        while self.running:
            time.sleep(10)
            self.send("GET_SENSOR_DATA")

    def store_sensor_data(self, temperature, humidity, motion_triggered):
        from .models import SensorData  # ✅ Lazy import inside function
        try:
            SensorData.objects.create(
                temperature=temperature,
                humidity=humidity,
                motion_triggered=motion_triggered,
            )
        except (OperationalError, sqlite3.OperationalError):
            pass

    def get_active_visitors(self):
        # Dummy fallback; replace with real logic
        return 1
