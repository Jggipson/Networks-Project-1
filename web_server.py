import time
import gc
try:
    # runs on the Raspberry Pi Pico 2 W
    import usocket as socket
    import network
except ImportError:
    # fallback when running on desktop PC
    import socket
    network = None

class WebServer:
    def __init__(self, cache_manager, port=80):
        self.port = port
        self.server_socket = None
        # accept the real Cache Manager instance passed from main
        self.cache_manager = cache_manager

    def connect_wifi(self, ssid, password):
        # connects the Pico 2 W to the local Wi-Fi network
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(ssid, password)

        #if we are unable to connect within the timeout amoutn
        timeout = 10
        while not wlan.isconnected() and timeout > 0:
            print("Connecting to Wi-Fi...")
            time.sleep(1)
            timeout -= 1

        #print statement of whether the connection to the wifi was successful or not
        if wlan.isconnected():
            print("Connected! Pico IP:", wlan.ifconfig()[0])
            return wlan.ifconfig()[0]
        else:
            raise RuntimeError("Failed to connect to Wi-Fi")

    def parse_request(self, raw_request):
        """Extracts the HTTP method and URI path from the request."""
        try:
            lines = raw_request.split("\r\n")
            first_line = lines[0]  # will read url for example "GET /index.html HTTP/1.1"
            parts = first_line.split(" ")
            return parts[0], parts[1]
        except Exception:
            return None, None

    def start(self):
        # starts the socket server listener.
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('', self.port))
        self.server_socket.listen(5)
        
        print(f"Web Server active on port {self.port}...")

        while True:
            client_socket = None
            try:
                client_socket, client_addr = self.server_socket.accept()
                raw_request = client_socket.recv(1024).decode('utf-8')
                method, path = self.parse_request(raw_request)

                if method == "GET":
                    # pass requested path to Cache Manager's fetch_resource method
                    html_payload = self.cache_manager.fetch_resource(path)

                    if html_payload is None:
                        response = "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
                        client_socket.sendall(response.encode('utf-8'))
                    else:
                        if isinstance(html_payload, bytes):
                            html_payload = html_payload.decode('utf-8')

                        # text displayed if the connection was successful
                        response = (
                            "HTTP/1.1 200 OK\r\n"
                            "Content-Type: text/html\r\n"
                            f"Content-Length: {len(html_payload.encode('utf-8'))}\r\n"
                            "Connection: close\r\n\r\n" + html_payload
                        )
                        client_socket.sendall(response.encode('utf-8'))
                else:
                    client_socket.sendall("HTTP/1.1 400 Bad Request\r\n\r\n".encode('utf-8'))

            except Exception as e:
                print("Error processing request:", e)
            finally: #closes socket after completed
                if client_socket:
                    client_socket.close()
                gc.collect()
