#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# ///

import http.server
import os
import webbrowser
from pathlib import Path

PORT = 8765
DIR = Path(__file__).parent

os.chdir(DIR)

class GzipAwareHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Serve .json.gz files with Content-Encoding: gzip so the browser
        # decompresses them automatically, matching GitHub Pages behaviour
        if self.path.split('?')[0].endswith('.json.gz'):
            self.send_header('Content-Encoding', 'gzip')
            self.send_header('Content-Type', 'application/json')
        super().end_headers()

    def log_message(self, format, *args):
        print(f"{self.address_string()} - {format % args}")

class ReuseAddrServer(http.server.HTTPServer):
    allow_reuse_address = True

url = f"http://localhost:{PORT}"
print(f"Serving 語 Reader at {url}")
print("Press Ctrl+C to stop.")

webbrowser.open(url)

with ReuseAddrServer(("localhost", PORT), GzipAwareHandler) as httpd:
    httpd.serve_forever()
