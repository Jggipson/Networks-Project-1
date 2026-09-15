from web_server import WebServer
from micropy_backendAPI import CacheManager

# Replace DB_PI_IP with your Pi 5's actual IP address on the local network (e.g. run 'hostname -I' on Pi 5)
DB_PI_IP = "192.168.1.XXX"
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASS = "YOUR_WIFI_PASSWORD"

cache_mgr = CacheManager(database_ip=DB_PI_IP, database_port=9000)
server = WebServer(cache_manager=cache_mgr, port=80)

pico_ip = server.connect_wifi(WIFI_SSID, WIFI_PASS)
# CRITICAL FIX: Keep server alive and listening for browser GET requests
server.start()