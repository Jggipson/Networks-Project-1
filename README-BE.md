# Backend API & Cache Manager Module

## Overview
The `CacheManager` class serves as the caching layer and backend communication bridge for the HTTP Web Server. Running locally on the Raspberry Pi Pico 2 W within the MicroPython environment, it optimizes page retrieval by maintaining an in-memory cache of requested HTML payloads. 

When a requested route is present in memory, it serves the asset immediately (**Cache Hit**). If missing (**Cache Miss**), it opens a direct TCP socket connection over port `9000` to the MariaDB Database Server running on the Raspberry Pi 5, caches the returned payload, and delivers it to the Pico's Web Server.

---

## Role & Hardware Specifications
* **Role:** Backend API Developer
* **Target Hardware:** Raspberry Pi Pico 2 W (RP2350)
* **Runtime:** MicroPython
* **Network Port:** 9000 (Outbound TCP Client)
* **Dependencies:** `usocket`, `gc` (MicroPython built-ins)

---

## Architecture & Logic Flow

1. **Request Interception:** The `WebServer` class receives an HTTP `GET` request on port 80 and passes the route path (e.g., `/index.html`) to `CacheManager.fetch_resource(resource_uri)`.
2. **Cache Lookup:**
   * **Cache Hit:** The payload exists in `self.storage`. The raw bytes are returned instantly without network I/O.
   * **Cache Miss:** The URI is not in `self.storage`. The module opens a raw TCP socket to `database_ip:9000`.
3. **Database Fetch:**
   * Sends `{resource_uri}\n` over port 9000.
   * Reads the incoming byte stream from the Pi 5 database service until socket close (EOF).
4. **Memory Management & Eviction:**
   * Newly fetched payloads are stored in `self.storage`.
   * If entries exceed `cache_capacity`, the oldest entry is evicted to prevent heap exhaustion.
   * Explicit garbage collection (`gc.collect()`) runs to clean up transient network buffers.
5. **Handoff:** Returns the payload bytes (or `None` on a 404/failure) to the `WebServer` to construct the HTTP response.

---

## Wire Protocol (Port 9000)

| Direction | Format | Description |
| :--- | :--- | :--- |
| **Pico $\rightarrow$ Pi 5** | `/{route}\n` (UTF-8 encoded) | Requested page path terminated by a newline. |
| **Pi 5 $\rightarrow$ Pico** | `<raw_html_bytes>` | Raw HTML payload. Connection closed by server upon completion (EOF). |
| **Pi 5 $\rightarrow$ Pico** | `ERROR 404\n` | Sent when the requested URI is not found in MariaDB. |

---

## Installation & Deployment

1. Connect the Raspberry Pi Pico 2 W via USB.
2. Upload `cache_manager.py` directly to the Pico's root flash filesystem using Thonny, VS Code (MicroPico), or `mpremote`.
3. Ensure the Raspberry Pi 5 database listener (`db_server.py`) is running on port 9000 and accessible via the shared local Wi-Fi network.

---

## Usage Example

```python
from cache_manager import CacheManager

# Initialize with the static local IP of the Raspberry Pi 5
cache = CacheManager(database_ip="192.168.1.50", database_port=9000, cache_capacity=10)

# Retrieve a payload (handles hit/miss internally)
html_payload = cache.fetch_resource("/index.html")

if html_payload:
    # Web server constructs HTTP 200 OK
    response = b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + html_payload
else:
    # Web server constructs HTTP 404 Not Found
    response = b"HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\n\r\nPage Not Found"
