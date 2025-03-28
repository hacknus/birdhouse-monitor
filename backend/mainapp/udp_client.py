import socket
import time
import os

# Define the file where the Raspberry Pi IP is stored
IP_FILE = 'raspberry_pi_ip.txt'
UDP_PORT = 5005  # The port where Raspberry Pi sends video frames


# Function to read IP address from the file
def read_ip_from_file():
    try:
        with open(IP_FILE, 'r') as file:
            ip_address = file.readline().strip()
            return ip_address
    except FileNotFoundError:
        print(f"Error: {IP_FILE} not found.")
        return None
    except Exception as e:
        print(f"Error reading {IP_FILE}: {e}")
        return None


# This is the generator that provides JPEG frames to Django view
def img_generator():
    while True:
        # Keep trying to connect and receive frames from the Raspberry Pi
        ip_address = read_ip_from_file()

        if ip_address:
            try:
                print(f"Connecting to {ip_address}...")

                # Create a UDP socket to receive video frames
                udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                udp_socket.bind((ip_address, UDP_PORT))

                print(f"Connected to {ip_address}:{UDP_PORT}")

                while True:
                    # Receive JPEG frame from the Raspberry Pi
                    jpeg, addr = udp_socket.recvfrom(65536)  # Max size of a UDP packet

                    if jpeg:
                        # Yield the frame as part of the multipart response
                        yield (
                                b"--frame\r\n"
                                b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n\r\n"
                        )
                    else:
                        time.sleep(0.1)  # Pause if no data is received
            except (socket.timeout, socket.error) as e:
                print(f"Error: {e}. Reconnecting...")
                time.sleep(2)  # Retry connection after 2 seconds
        else:
            print("IP address not found, retrying in 2 seconds...")
            time.sleep(2)  # Retry reading the IP address every 2 seconds