import network
import socket
import time


WIFI_SSID = "YOUR_WIFI"
WIFI_PASSWORD = "YOUR_PASSWORD"

SERVER_PORT = 80

PI5_IP_ADDRESS = "192.168.X.X"
BACKEND_PORT = 9000


def connect_wifi():

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    while not wlan.isconnected():
        time.sleep(1)

    print("Wi-Fi connected")
    print("IP:", wlan.ifconfig()[0])

    return wlan


def start_server():

    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind(("0.0.0.0", SERVER_PORT))
    server.listen(1)

    print("HTTP server listening on port 80")

    return server


def request_backend(path):

    sock = socket.socket()

    try:
        sock.connect((PI5_IP_ADDRESS, BACKEND_PORT))

        request = path + "\n"
        sock.send(request.encode())

        response = sock.recv(4096)

        return response.decode()

    finally:
        sock.close()


def send_response(client, html):

    response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/html\r\n"
        "Content-Length: {}\r\n"
        "Connection: close\r\n"
        "\r\n"
        "{}"
    ).format(len(html), html)

    client.send(response.encode())


def main():

    connect_wifi()

    server = start_server()

    while True:

        client, address = server.accept()

        print("Connection from:", address)

        request = client.recv(1024)

        print("Request:")
        print(request)

        # Temporary path
        path = "/"

        # Ask Pi 5 backend for the HTML
        html = request_backend(path)

        send_response(client, html)

        client.close()


main()
