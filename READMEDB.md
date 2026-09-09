# Database Administrator — Deliverables

This covers the Database Administrator's three responsibilities from the
lab spec: deploy the schema, store the HTML payloads, and build the
Database Server class.

## Files

- **`schema.sql`** — Creates `webserver_db`, the `pages` table, a
  least-privilege `webserver` DB user, and two sample rows.
- **`db_server.py`** — The `DatabaseServer` class. Runs on the Raspberry
  Pi 5, listens on TCP port 9000, and answers requests by querying
  MariaDB.
- **`test_client.py`** — A throwaway script to test `db_server.py` on
  its own, before the real Cache Manager exists.

## Setup on the Raspberry Pi 5

```bash
# 1. Install MariaDB server if not already present
sudo apt install mariadb-server

# 2. Load the schema
sudo mariadb -u root -p < schema.sql

# 3. Install the Python connector
pip install mariadb --break-system-packages   # or use a venv

# 4. Run the server
python3 db_server.py

# 5. In a second terminal, sanity-check it
python3 test_client.py
```

If `pip install mariadb` fails to build (it needs MariaDB's C connector
libraries), install those first:
```bash
sudo apt install libmariadb3 libmariadb-dev
```

## The protocol (DBSP) — this is what you must agree on with the Backend API Developer

Your `DatabaseServer` and their `CacheManager` (on the Pico 2 W) talk over
a plain TCP socket on **port 9000**. The protocol is deliberately simple
text, so it's light enough for MicroPython to parse and easy to read in
a Wireshark/PCAP trace for the Network Analyst.

**Request** (Cache Manager → Database Server):
```
GET <path>\n
```
Example: `GET /index.html\n`

**Response** (Database Server → Cache Manager):

| Situation        | Response                                                        |
|-------------------|------------------------------------------------------------------|
| Found             | `200 OK\r\nContent-Length: <n>\r\n\r\n<html bytes>`               |
| Not found in DB   | `404 NOT FOUND\r\n\r\n`                                           |
| Malformed request | `400 BAD REQUEST\r\n\r\n`                                         |
| DB/server error   | `500 ERROR\r\n\r\n`                                               |

Talk to your Backend API Developer before they start coding their
socket client — confirm:
1. They're fine with this exact header format (it mirrors HTTP on
   purpose, so parsing is just "find `\r\n\r\n`, then read
   Content-Length bytes").
2. What happens on a `404` on their end (do they serve a default error
   page? Log it? Retry?).
3. Whether they want the connection kept alive for multiple requests or
   closed after each one (currently: one request per connection, then
   the socket closes — simplest for a lab project).

## For the Network Analyst

Your server listens on **port 9000**, matching the "ports 80 and 9000"
called out in the spec — they should point their sniffer filter there
to capture the backend fetch step, separate from the port-80 traffic
between the browser and the Pico 2 W.

## Extending the payload set

Use `insert_or_update_page(path, html_content)` on a `DatabaseServer`
instance (or just re-run modified `INSERT` statements from
`schema.sql`) to add more pages beyond the two samples.
