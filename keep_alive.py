"""
Keep-alive web server to prevent Railway/hosting from sleeping.
Runs a simple HTTP server on PORT so health checks pass.
"""
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK - Bot is alive!")

    def log_message(self, format, *args):
        pass  # Suppress default access logs


def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


def keep_alive():
    """Start the keep-alive server in a background thread."""
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    print(f"Keep-alive server started on port {os.environ.get('PORT', 8080)}")
