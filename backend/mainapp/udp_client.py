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
        self.expected_size = 0  # Expected size of the full frame
        self.total_chunks = 0  # Total chunks expected for the current frame

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

                self.socket.bind((ip, self.udp_port))
                print(f"[UDP Client] Successfully bound to {ip}:{self.udp_port}")

                current_frame = []  # To store the chunks for the current frame
                received_chunks = 0  # Number of chunks received for this frame

                while self.running:
                    try:
                        data, addr = self.socket.recvfrom(65536)  # Receive data (maximum buffer size)
                        if self.total_chunks == 0:  # No chunks expected yet, get metadata
                            # The first packet contains the total number of chunks
                            self.total_chunks = struct.unpack("I", data[:4])[0]
                            self.expected_size = struct.unpack("I", data[4:8])[0]
                            print(
                                f"[UDP Client] Expecting {self.total_chunks} chunks for the next frame. Expected frame size: {self.expected_size}")
                            continue  # Skip the total chunks metadata packet

                        chunk_id = struct.unpack("I", data[:4])[0]  # Get the chunk ID (4 bytes)
                        chunk_data = data[4:]  # The actual chunk data (everything after the ID)

                        # Add the chunk to the current frame
                        current_frame.append((chunk_id, chunk_data))
                        received_chunks += 1

                        print(f"[UDP Client] Received chunk {chunk_id}/{self.total_chunks}")

                        # If all chunks for the current frame have been received, reassemble the frame
                        if received_chunks == self.total_chunks:
                            print(f"[UDP Client] All {self.total_chunks} chunks received. Reassembling frame...")

                            # Sort the chunks based on their chunk_id
                            current_frame.sort(key=lambda x: x[0])

                            # Reassemble the full frame by concatenating all chunk data
                            full_frame = b''.join([chunk[1] for chunk in current_frame])

                            # Ensure that the reassembled frame size matches the expected size
                            if len(full_frame) == self.expected_size:
                                print(f"[UDP Client] Frame successfully reassembled. Size: {len(full_frame)} bytes")

                                # Add the complete frame to the frame queue
                                with self.lock:
                                    self.frame_queue.append(full_frame)
                            else:
                                print(
                                    f"[UDP Client] Error: Frame size mismatch! Expected {self.expected_size}, but got {len(full_frame)}")

                            # Reset for the next frame
                            current_frame = []
                            self.total_chunks = 0
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
            return self.frame_queue[-1] if self.frame_queue else None

    def stop(self):
        self.running = False
        if self.socket:
            self.socket.close()
        if self.thread:
            self.thread.join()
