# udp_video_client.py
import socket
import struct
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
                print(f"[UDP Client] Successfully bound to {ip}:{self.udp_port}")

                current_frame = []
                total_chunks = None  # To store the total number of chunks
                received_chunks = 0

                while self.running:
                    try:
                        data, addr = self.socket.recvfrom(65536)
                        print(f"[UDP Client] Received data from {addr}: {len(data)} bytes")

                        if total_chunks is None:
                            # The first packet contains the total number of chunks
                            total_chunks = struct.unpack("B", data)[0]
                            print(f"Expecting {total_chunks} chunks for the next frame.")
                            continue  # Skip the total chunks packet

                        chunk_id = struct.unpack("B", data[:1])[0]  # Get the chunk ID from the header
                        chunk_data = data[1:]  # Get the actual data without the header

                        # Add the chunk to the current frame (ensure that the chunks are added in the correct order)
                        current_frame.append((chunk_id, chunk_data))
                        received_chunks += 1

                        # If all chunks for the current frame have been received, reassemble it
                        if received_chunks == total_chunks:
                            print(f"[UDP Client] Full frame received ({received_chunks} chunks). Reassembling frame...")
                            # Sort the chunks based on the chunk ID
                            current_frame.sort(key=lambda x: x[0])

                            # Reassemble the frame
                            full_frame = b''.join([chunk[1] for chunk in current_frame])

                            # Add the complete frame to the frame queue
                            with self.lock:
                                self.frame_queue.append(full_frame)

                            # Reset for the next frame
                            current_frame = []
                            total_chunks = None
                            received_chunks = 0

                        time.sleep(0.01)
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
            print(f"[FRAME Q]  {self.frame_queue}")
            return self.frame_queue[-1] if self.frame_queue else None

    def stop(self):
        self.running = False
        if self.socket:
            self.socket.close()
        if self.thread:
            self.thread.join()
