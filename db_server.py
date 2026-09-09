"""
Database Server Class
----------------------
COSC 4378 Lab Project — Database Administrator deliverable.

Runs on the Raspberry Pi 5. Listens on a TCP socket (default port 9000)
for requests from the Cache Manager (Backend API, running on the
Pico 2 W). On each request, looks up the requested HTML payload in
MariaDB and sends it back.

Requires the official MariaDB Python connector:
    pip install mariadb

Protocol (DBSP — a simple line-based text protocol, deliberately
close to HTTP so it's easy to eyeball in a packet capture):

    Request  (Cache Manager -> Database Server):
        "GET <path>\n"
        e.g. "GET /index.html\n"

    Response (Database Server -> Cache Manager):
        Success:
            "200 OK\r\nContent-Length: <n>\r\n\r\n<html bytes>"
        Not found:
            "404 NOT FOUND\r\n\r\n"
        Malformed request:
            "400 BAD REQUEST\r\n\r\n"
        Server-side error (DB down, query failed, etc.):
            "500 ERROR\r\n\r\n"

Coordinate this exact format with your Backend API Developer —
this file's docstring is the contract between your two classes.
"""

import socket
import threading
import logging

try:
    import mariadb
except ImportError:  # pragma: no cover
    mariadb = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("DatabaseServer")


class DatabaseServer:
    """TCP server that serves HTML payloads out of MariaDB."""

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

    # ---------------------------------------------------------------
    # Database access
    # ---------------------------------------------------------------

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

    # ---------------------------------------------------------------
    # Networking
    # ---------------------------------------------------------------

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

    def _read_line(self, sock, max_bytes=2048):
        """Read from the socket until a newline shows up."""
        buf = b""
        while b"\n" not in buf and len(buf) < max_bytes:
            chunk = sock.recv(64)
            if not chunk:
                break
            buf += chunk
        return buf.decode("utf-8", errors="replace")

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


if __name__ == "__main__":
    server = DatabaseServer(
        host="0.0.0.0",
        port=9000,
        db_host="127.0.0.1",
        db_user="webserver",
        db_password="changeme",  # TODO: match schema.sql / your real creds
        db_name="webserver_db",
    )
    server.start()
