import usocket as socket
import gc

# simple cache manager to keep db requests down
class CacheManager:
    def __init__(self, database_ip, database_port=9000, cache_capacity=10):
        # set up connection details and our cache limits
        self.db_addr = database_ip
        self.db_port = database_port
        self.capacity = cache_capacity
        self.storage = {}  # {resource_uri: page_bytes}

    def fetch_resource(self, resource_uri):
        """
        tries to grab the payload from ram if we already have it.
        if not, falls back to hitting the db on port 9000.
        """
        # 1. check if it's already sitting in memory
        if resource_uri in self.storage:
            print(f"[CACHE HIT] Serving {resource_uri} from SRAM")
            return self.storage[resource_uri]

        # 2. ask the upstream db server for it
        print(f"[CACHE MISS] Fetching {resource_uri} from DB @ {self.db_addr}:{self.db_port}")
        raw_payload = self._request_from_db(resource_uri)

        # 3. save it to cache and make sure we aren't hogging too much ram
        if raw_payload:
            # kick out the oldest item if we've hit our limit
            if len(self.storage) >= self.capacity:
                oldest_entry = next(iter(self.storage))
                del self.storage[oldest_entry]

            self.storage[resource_uri] = raw_payload
            # force garbage collection so the micro doesn't crash from out-of-memory
            gc.collect()

        return raw_payload

    def _request_from_db(self, resource_uri):
        sock = None
        try:
            # figure out the ip and prep the tcp socket
            target_info = socket.getaddrinfo(self.db_addr, self.db_port)[0][-1]
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0) # don't hang forever if the network is acting up
            sock.connect(target_info)

            # send the query formatted to the dbsp spec (needs the newline)
            outbound_msg = f"GET {resource_uri}\n".encode("utf-8")
            sock.send(outbound_msg)

            # read the incoming data in 1kb chunks
            stream_buffer = []
            while True:
                chunk = sock.recv(1024)
                if not chunk:
                    break # nothing left to read
                stream_buffer.append(chunk)

            # glue all the chunks back together
            complete_payload = b"".join(stream_buffer)
            
            # bail out if the server threw an error or didn't give a 200
            if not complete_payload.startswith(b"200 OK"):
                return None

            # slice off the protocol headers so we're just left with the html body
            if b"\r\n\r\n" in complete_payload:
                _, body = complete_payload.split(b"\r\n\r\n", 1)
                return body.decode("utf-8")

            return None

        except Exception as err:
            # something went wrong over the network
            print(f"[ERROR] DB socket communication failed: {err}")
            return None
        finally:
            # always clean up the socket so we don't leak file descriptors
            if sock:
                sock.close()
                #haveagoodday
