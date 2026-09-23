#This program runs a database server that receives page requests, looks up 
#the matching HTML content in MariaDB, and sends it back to the requesting client.

#These libraries give the server the tools it needs to communicate over the network,
#handle several clients at once, record useful messages, and talk to MariaDB!
import socket
import threading
import logging
import mariadb

#This sets up readable log messages so we can see what the server is doing while it runs.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("DatabaseServer")

#This entire class is the database server that listens for requests and serves HTML payloads from MariaDB.
class DatabaseServer:
    """TCP server that serves HTML payloads out of MariaDB."""
    #This saves the network and database details that the server will use throughout its lifetime.
    def __init__(
        self,
        host="0.0.0.0",
        port=9000,
        db_host="127.0.0.1",
        db_port=3306,
        db_user="webserver",
        db_password="changeme",
        db_name="webserver_db",
    ):
        self.host = host
        self.port = port
        self.db_config = {
            "host": db_host,
            "port": db_port,
            "user": db_user,
            "password": db_password,
            "database": db_name,
        }
        self._sock = None

    #This creates a fresh connection to MariaDB whenever the server needs to use the database.
    def _get_connection(self):
        if mariadb is None:
            raise RuntimeError(
                "The 'mariadb' package is not installed. "
                "Run: pip install mariadb"
            )
        try:
            return mariadb.connect(**self.db_config)
        except mariadb.Error as e:
            logger.error(f"Could not connect to MariaDB: {e}")
            raise

    #This looks up a requested path and returns the matching HTML page as bytes.
    #If return None is triggered then it signals to the caller that the page was not found.
    def fetch_payload(self, path: str):
        """
        Look up the HTML payload for a given request path.
        Returns the payload as bytes, or None if not found.
        """
        conn = None
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT html_content FROM pages WHERE path = ? LIMIT 1",
                (path,),
            )
            row = cur.fetchone()
            if row is None:
                return None
            html_content = row[0]
            if isinstance(html_content, str):
                html_content = html_content.encode("utf-8")
            return html_content
        except mariadb.Error as e:
            logger.error(f"Query failed for path '{path}': {e}")
            return None
        finally:
            if conn is not None:
                conn.close()

    #This adds a page to the database, or replaces its HTML if that path already exists.
    #This can be useful for loading and updating the pages the server will serve!
    def insert_or_update_page(self, path: str, html_content: str):
        """Helper for seeding/updating pages programmatically."""
        conn = None
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO pages (path, html_content) VALUES (?, ?)
                ON DUPLICATE KEY UPDATE html_content = VALUES(html_content)
                """,
                (path, html_content),
            )
            conn.commit()
            return True
        except mariadb.Error as e:
            logger.error(f"Insert/update failed for path '{path}': {e}")
            return False
        finally:
            if conn is not None:
                conn.close()

    #This opens the listening socket and gives each incoming client its own worker thread.
    #This will let the server handle multiple requests without making clients wait in line!!
    def start(self):
        """Bind, listen, and accept connections until interrupted."""
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self.host, self.port))
        self._sock.listen(5)
        logger.info(f"Database Server listening on {self.host}:{self.port}")

        try:
            while True:
                client_sock, addr = self._sock.accept()
                logger.info(f"Connection from {addr}")
                thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_sock, addr),
                    daemon=True,
                )
                thread.start()
        except KeyboardInterrupt:
            logger.info("Shutting down Database Server...")
        finally:
            self._sock.close()

    #This handles one client's complete request with the following steps: read the request, check that it is a GET request,
    #find the page in MariaDB, and send back the corresponding result.
    def _handle_client(self, client_sock, addr):
        try:
            request_line = self._read_line(client_sock)
            if not request_line:
                return

            logger.info(f"Request from {addr}: {request_line!r}")
            parts = request_line.strip().split(" ", 1)

            if len(parts) != 2 or parts[0] != "GET":
                self._send_response(client_sock, 400, b"")
                return

            path = parts[1].strip()
            payload = self.fetch_payload(path)

            if payload is None:
                logger.info(f"Cache miss (DB miss too) for '{path}'")
                self._send_response(client_sock, 404, b"")
            else:
                logger.info(f"Served '{path}' ({len(payload)} bytes)")
                self._send_response(client_sock, 200, payload)

        except Exception as e:
            logger.error(f"Error handling client {addr}: {e}")
            try:
                self._send_response(client_sock, 500, b"")
            except Exception:
                pass
        finally:
            client_sock.close()

    #This reads the request a little at a time until the client sends a newline.
    #Having the byte limit will keep the client from sending a request that is unreasonably large and could cause problems for the server.
    def _read_line(self, sock, max_bytes=2048):
        """Read from the socket until a newline shows up."""
        buf = b""
        while b"\n" not in buf and len(buf) < max_bytes:
            chunk = sock.recv(64)
            if not chunk:
                break
            buf += chunk
        return buf.decode("utf-8", errors="replace")

    #This translates the result into the simple response format expected by the client.
    #If a page was found, it will include its length and HTML content in the response!
    def _send_response(self, sock, status_code, payload: bytes):
        status_text = {
            200: "200 OK",
            400: "400 BAD REQUEST",
            404: "404 NOT FOUND",
            500: "500 ERROR",
        }.get(status_code, "500 ERROR")

        if payload:
            header = f"{status_text}\r\nContent-Length: {len(payload)}\r\n\r\n"
            sock.sendall(header.encode("utf-8") + payload)
        else:
            header = f"{status_text}\r\n\r\n"
            sock.sendall(header.encode("utf-8"))

#This builds the server with the project's settings and start it when this file is run directly.
if __name__ == "__main__":
    server = DatabaseServer(
        host="0.0.0.0",
        port=9000,
        db_host="127.0.0.1",
        db_user="webserver",
        db_password="changeme",
        db_name="webserver_db",
    )
    server.start()