#!/usr/bin/env python3
"""
Simple HTTP server to serve the HTML test files.
"""

import http.server
import socketserver
import os
import sys

# Add the parent directory to the path so we can import from the root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

PORT = 8080

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Set the directory to the html directory
        self.directory = os.path.join(os.path.dirname(__file__), 'html')
        super().__init__(*args, **kwargs)
        
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        http.server.SimpleHTTPRequestHandler.end_headers(self)

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def main():
    print(f"Serving at http://localhost:{PORT}")
    print(f"Open your browser and navigate to http://localhost:{PORT}/test_api.html")
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()

if __name__ == "__main__":
    main()
