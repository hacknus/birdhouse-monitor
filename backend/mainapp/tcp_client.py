import socket
import threading
import time

# Define file that contains the Raspberry Pi's IP address
IP_FILE = 'raspberry_pi_ip.txt'
TCP_PORT = 6006


# Read the Raspberry Pi's IP address from the file
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


# Function to attempt to connect to the Raspberry Pi's TCP server
def try_connect_to_raspberry_pi():
    while True:
        ip_address = read_ip_from_file()
        if ip_address:
            try:
                print(f"Trying to connect to {ip_address}:{TCP_PORT}")
                # Create TCP socket
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(5)  # Set timeout for the connection
                    sock.connect((ip_address, TCP_PORT))
                    print(f"Connected to {ip_address}:{TCP_PORT}")

                    # Send a test command (for example, "turn on led")
                    command = "turn on led"
                    sock.sendall(command.encode('utf-8'))
                    print(f"Sent command: {command}")

                    # Wait for a response (if any)
                    response = sock.recv(1024)
                    print(f"Response from server: {response.decode('utf-8')}")

            except (socket.timeout, socket.error) as e:
                print(f"Connection failed to {ip_address}:{TCP_PORT}. Retrying...")
                time.sleep(2)  # Retry every 2 seconds if the connection fails
        else:
            print(f"Failed to read IP address from {IP_FILE}. Retrying...")
            time.sleep(2)  # Retry after 2 seconds if the IP is not found


# Function to start the connection thread
def start_connection_thread():
    connection_thread = threading.Thread(target=try_connect_to_raspberry_pi, daemon=True)
    connection_thread.start()


if __name__ == "__main__":
    start_connection_thread()

    # Keep the main thread running while the connection thread works
    while True:
        time.sleep(1)