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
    def do_GET(self):
        # If a .wasm request has a pre-compressed .wasm.gz sidecar, serve it
        # with correct headers (bypasses SimpleHTTPRequestHandler to avoid
        # conflicting Content-Type from Python's mime-type guessing).
        path = self.path.split('?')[0].lstrip('/')
        if path.endswith('.wasm'):
            gz_path = Path(path + '.gz')
            if gz_path.exists():
                data = gz_path.read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', 'application/wasm')
                self.send_header('Content-Encoding', 'gzip')
                self.send_header('Content-Length', str(len(data)))
                self.send_header('Cache-Control', 'max-age=86400')
                self.end_headers()
                self.wfile.write(data)
                return
        super().do_GET()

    def end_headers(self):
        path = self.path.split('?')[0]
        # Serve .json.gz with Content-Encoding: gzip so the browser decompresses
        # automatically, matching GitHub Pages behaviour.
        if path.endswith('.json.gz'):
            self.send_header('Content-Encoding', 'gzip')
            self.send_header('Content-Type', 'application/json')
        # Cache large static assets aggressively so reloads are instant over LAN.
        if any(path.endswith(ext) for ext in ('.json.gz', '.js', '.dat.gz', '.woff2', '.wasm')):
            self.send_header('Cache-Control', 'max-age=86400')
        super().end_headers()

    def log_message(self, format, *args):
        print(f"{self.address_string()} - {format % args}")

class ReuseAddrServer(http.server.HTTPServer):
    allow_reuse_address = True

def lan_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return None

local_url = f"http://localhost:{PORT}"
ip = lan_ip()
lan_url   = f"http://{ip}:{PORT}" if ip else None
print(f"Serving 語 Reader")
print(f"  Local:  {local_url}")
if lan_url:
    print(f"  Mobile: {lan_url}")
print("Press Ctrl+C to stop.")

webbrowser.open(lan_url or local_url)

try:
    with ReuseAddrServer(("0.0.0.0", PORT), GzipAwareHandler) as httpd:
        httpd.serve_forever()
except KeyboardInterrupt:
    pass
