# udp_video_client.py
import socket
import threading
import time
from collections import deque


class UDPVideoClient:
    def __init__(self, port=5005, ip_file='mainapp/raspberry_pi_ip.txt'):
        self.udp_port = port
        self.ip_file = ip_file
        self.running = False
        self.socket = None
        self.thread = None
        self.frame_queue = deque(maxlen=1)
        self.lock = threading.Lock()

    def read_ip(self):
        try:
            with open(self.ip_file, 'r') as file:
                return file.readline().strip()
        except Exception as e:
            print(f"[UDP Client] Error reading IP: {e}")
            return None

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._receive_frames, daemon=True)
            self.thread.start()

    def _receive_frames(self):
        while self.running:
            ip = "0.0.0.0"
            try:
                print(f"[UDP Client] Binding to {ip}:{self.udp_port}")
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

                # Enable reusing the port so multiple clients can receive the stream
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

                # self.socket.settimeout(5)
                self.socket.bind((ip, self.udp_port))

                while self.running:
                    try:
                        data, _ = self.socket.recvfrom(65536)
                        with self.lock:
                            self.frame_queue.append(data)
                        print(f"[UDP Client] Received frame: {data}")
                    except socket.timeout:
                        continue
                    except Exception as e:
                        print(f"[UDP Client] Receive error: {e}")
                        break

            except Exception as e:
                print(f"[UDP Client] Bind error: {e}")
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
