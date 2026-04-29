#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# ///

import http.server
import os
import socket
import webbrowser
from pathlib import Path

PORT = 8765
DIR = Path(__file__).parent.parent

os.chdir(DIR)

class GzipAwareHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Serve .json.gz files with Content-Encoding: gzip so the browser
        # decompresses them automatically, matching GitHub Pages behaviour
        path = self.path.split('?')[0]
        if path.endswith('.json.gz'):
            self.send_header('Content-Encoding', 'gzip')
            self.send_header('Content-Type', 'application/json')
        # Cache large static assets aggressively so reloads are instant over LAN
        if any(path.endswith(ext) for ext in ('.gz', '.js', '.dat')):
            self.send_header('Cache-Control', 'max-age=86400')
        super().end_headers()

    def log_message(self, format, *args):
        print(f"{self.address_string()} - {format % args}")

class ReuseAddrServer(http.server.HTTPServer):
    allow_reuse_address = True
    address_family = socket.AF_INET6

    def server_bind(self):
        # Accept both IPv4 and IPv6 (dual-stack): handles localhost via ::1 and LAN via IPv4
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        super().server_bind()

def lan_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]

local_url = f"http://localhost:{PORT}"
lan_url   = f"http://{lan_ip()}:{PORT}"
print(f"Serving 語 Reader")
print(f"  Local:  {local_url}")
print(f"  Mobile: {lan_url}")
print("Press Ctrl+C to stop.")

webbrowser.open(local_url)

with ReuseAddrServer(("::", PORT), GzipAwareHandler) as httpd:
    httpd.serve_forever()
