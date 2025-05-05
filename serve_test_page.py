#!/usr/bin/env python3
"""
Simple HTTP server to serve the test_api.html file.
"""

import http.server
import socketserver
import os

PORT = 8080

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        http.server.SimpleHTTPRequestHandler.end_headers(self)

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

print(f"Serving at http://localhost:{PORT}")
print("Open your browser and navigate to http://localhost:{PORT}/test_api.html")

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
