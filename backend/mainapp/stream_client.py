# Stream_video_client.py
import socket
import struct
import threading
import time
from collections import deque

import numpy as np


class StreamVideoClient:
    def __init__(self, port=5005, ip_file='mainapp/raspberry_pi_ip.txt'):
        self.stream_port = port
        self.ip_file = ip_file
        self.running = False
        self.socket = None
        self.thread = None
        self.frame_queue = deque(maxlen=1)
        self.lock = threading.Lock()
        self.expected_size = 0  # Expected size of the full frame
        self.total_chunks = 0  # Total chunks expected for the current frame

    def read_ip(self):
        try:
            with open(self.ip_file, 'r') as file:
                return file.readline().strip()
        except Exception as e:
            print(f"[Stream Client] Error reading IP: {e}")
            return None

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._receive_frames, daemon=True)
            self.thread.start()

    def _receive_frames(self):
        while self.running:
            ip = self.read_ip()
            try:
                print(f"[Stream Client] Binding to {ip}:{self.stream_port}")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                sock.connect((ip, self.stream_port))

                print(f"[Stream Client] Successfully bound to {ip}:{self.stream_port}")

                while self.running:
                    try:
                        # Receive the size of the frame
                        frame_size_data = sock.recv(8)
                        if not frame_size_data:
                            print("No data received, exiting...")
                            break
                        frame_size = struct.unpack("!Q", frame_size_data)[0]

                        # Receive the frame data
                        frame_data = b""
                        while len(frame_data) < frame_size:
                            packet = sock.recv(frame_size - len(frame_data))
                            if not packet:
                                break
                            frame_data += packet

                        # Decode the received frame
                        full_frame = np.frombuffer(frame_data, dtype=np.uint8)

                        with self.lock:
                            self.frame_queue.append(full_frame)

                    except socket.timeout:
                        continue
                    except Exception as e:
                        print(f"[Stream Client] Receive error: {e}")
                        break

            except Exception as e:
                print(f"[Stream Client] Bind error: {e}")
                time.sleep(2)
            finally:
                if self.socket:
                    self.socket.close()
                    self.socket = None

    def get_frame(self):
        with self.lock:
            return self.frame_queue[-1] if self.frame_queue else None

    def stop(self):
        self.running = False
        if self.socket:
            self.socket.close()
        if self.thread:
            self.thread.join()
