import usocket as socket
import gc

class CacheManager:
    def __init__(self, database_ip, database_port=9000, cache_capacity=10):
        self.db_addr = database_ip
        self.db_port = database_port
        self.capacity = cache_capacity
        self.storage = {}  # {resource_uri: page_bytes}

    def fetch_resource(self, resource_uri):
        """
        Retrieves payload from memory if cached.
        Falls back to port 9000 DB fetch on cache miss.
        """
        # 1. Evaluate memory cache hit
        if resource_uri in self.storage:
            print(f"[CACHE HIT] Serving {resource_uri} from SRAM")
            return self.storage[resource_uri]

        # 2. Query upstream DB server on port 9000
        print(f"[CACHE MISS] Fetching {resource_uri} from DB @ {self.db_addr}:{self.db_port}")
        raw_payload = self._request_from_db(resource_uri)

        # 3. Cache entry and manage allocation limits
        if raw_payload:
            if len(self.storage) >= self.capacity:
                oldest_entry = next(iter(self.storage))
                del self.storage[oldest_entry]

            self.storage[resource_uri] = raw_payload
            gc.collect()

        return raw_payload

    def _request_from_db(self, resource_uri):
        sock = None
        try:
            target_info = socket.getaddrinfo(self.db_addr, self.db_port)[0][-1]
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)
            sock.connect(target_info)

            # Transmit wire protocol query
            outbound_msg = f"{resource_uri}\n".encode("utf-8")
            sock.send(outbound_msg)

            # Receive incoming stream chunks
            stream_buffer = []
            while True:
                chunk = sock.recv(1024)
                if not chunk:
                    break
                stream_buffer.append(chunk)

            complete_payload = b"".join(stream_buffer)
            if complete_payload.startswith(b"ERROR"):
                return None

            return complete_payload

        except Exception as err:
            print(f"[ERROR] DB socket communication failed: {err}")
            return None
        finally:
            if sock:
                sock.close()