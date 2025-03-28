import socket
import threading
import time
import queue

class TCPClient:
    def __init__(self, ip_file='raspberry_pi_ip.txt', port=6006):
        self.ip_file = ip_file
        self.port = port
        self.socket = None
        self.connected = False
        self.lock = threading.Lock()
        self.running = False
        self.receive_callback = None  # Function to call when message received
        self.thread = None
        self.reply_queue = None  # for synchronous responses

    def read_ip_from_file(self):
        try:
            with open(self.ip_file, 'r') as file:
                return file.readline().strip()
        except Exception as e:
            print(f"[TCPClient] Error reading IP file: {e}")
            return None

    def connect_loop(self):
        self.running = True
        while self.running:
            ip_address = self.read_ip_from_file()
            if not ip_address:
                print("[TCPClient] No IP found. Retrying...")
                time.sleep(2)
                continue

            try:
                print(f"[TCPClient] Trying to connect to {ip_address}:{self.port}")
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(5)
                    sock.connect((ip_address, self.port))
                    with self.lock:
                        self.socket = sock
                        self.connected = True
                    print(f"[TCPClient] Connected to {ip_address}:{self.port}")

                    while self.running:
                        try:
                            data = sock.recv(1024)
                            if not data:
                                break
                            message = data.decode('utf-8')
                            print(f"[TCPClient] Received: {message}")
                            self.receive_callback_internal(message)
                        except socket.error as e:
                            print(f"[TCPClient] Socket error: {e}")
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
            print("[TCPClient] Connection thread started.")

    def send(self, message):
        """Send a message without waiting for a reply."""
        with self.lock:
            if self.socket and self.connected:
                try:
                    self.socket.sendall(message.encode('utf-8'))
                    print(f"[TCPClient] Sent: {message}")
                except socket.error as e:
                    print(f"[TCPClient] Send failed: {e}")
            else:
                print("[TCPClient] Cannot send, not connected.")

    def send_and_wait_for_reply(self, message, timeout=5):
        """Send a message and wait for a response."""
        self.reply_queue = queue.Queue(maxsize=1)  # Initialize the queue
        self.send(message)  # Send the command
        try:
            reply = self.reply_queue.get(timeout=timeout)
            return reply
        except queue.Empty:
            return None  # Return None if the reply was not received in time

    def stop(self):
        self.running = False
        with self.lock:
            if self.socket:
                self.socket.close()
                self.socket = None
                self.connected = False
        print("[TCPClient] Client stopped.")

    def set_receive_callback(self, callback_fn):
        """Set a callback function to handle incoming messages."""
        self.receive_callback = callback_fn

    def receive_callback_internal(self, message):
        """Handle received messages and forward them to the queue if waiting."""
        # Forward to queue if someone is waiting
        if self.reply_queue and not self.reply_queue.full():
            try:
                self.reply_queue.put_nowait(message)
            except queue.Full:
                pass
        # Also call user-defined callback
        if self.receive_callback:
            self.receive_callback(message)