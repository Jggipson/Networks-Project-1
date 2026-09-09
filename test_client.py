"""
Quick standalone test client for db_server.py.

This is NOT the Cache Manager class — it's a throwaway script so you
(the Database Administrator) can verify your server works correctly
in isolation, before the Backend API Developer's real Cache Manager
is ready to talk to it.

Usage:
    1. Start the server:      python3 db_server.py
    2. In another terminal:   python3 test_client.py
"""

import socket


def request_page(path, host="127.0.0.1", port=9000, timeout=5):
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.sendall(f"GET {path}\n".encode("utf-8"))

        data = b""
        while b"\r\n\r\n" not in data:
            chunk = sock.recv(1024)
            if not chunk:
                break
            data += chunk

        header_part, _, rest = data.partition(b"\r\n\r\n")
        header_lines = header_part.decode("utf-8").split("\r\n")
        status_line = header_lines[0]

        content_length = 0
        for line in header_lines[1:]:
            if line.lower().startswith("content-length:"):
                content_length = int(line.split(":", 1)[1].strip())

        body = rest
        while len(body) < content_length:
            chunk = sock.recv(4096)
            if not chunk:
                break
            body += chunk

        return status_line, body


if __name__ == "__main__":
    print("--- Requesting an existing page ---")
    status, body = request_page("/index.html")
    print("Status:", status)
    print("Body:  ", body.decode("utf-8", errors="replace"))

    print("\n--- Requesting a page that doesn't exist ---")
    status, body = request_page("/does-not-exist.html")
    print("Status:", status)
