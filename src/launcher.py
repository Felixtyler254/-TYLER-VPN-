import os
import sys
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from threading import Thread
import time
import json

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from vpn_handler import VPNHandler

# Global VPN handler
vpn_handler = None

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Remove directory parameter as we'll handle file serving manually
        super().__init__(*args, **kwargs)
        global vpn_handler
        self.vpn_handler = vpn_handler

    def do_GET(self):
        """Handle GET requests for static files"""
        if self.path == '/':
            self.path = '/index.html'
        
        try:
            # Get the file path
            file_path = resource_path(self.path.lstrip('/'))
            
            # Get file extension
            ext = os.path.splitext(self.path)[1]
            
            # Set content type
            content_types = {
                '.html': 'text/html',
                '.css': 'text/css',
                '.js': 'application/javascript'
            }
            content_type = content_types.get(ext, 'application/octet-stream')
            
            # Read and send the file
            with open(file_path, 'rb') as f:
                content = f.read()
                self.send_response(200)
                self.send_header('Content-type', content_type)
                self.send_header('Content-Length', len(content))
                self.end_headers()
                self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404, f"File not found: {self.path}")
        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def log_message(self, format, *args):
        """Override to prevent logging to stderr"""
        pass

    def do_POST(self):
        if self.path == '/connect':
            success = self.vpn_handler.start_vpn()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": success}).encode())
        elif self.path == '/disconnect':
            success = self.vpn_handler.stop_vpn()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": success}).encode())
        elif self.path == '/status':
            status = self.vpn_handler.get_vpn_status()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())
        else:
            self.send_error(404)

def run_server():
    server = HTTPServer(('localhost', 8000), Handler)
    print("VPN Server running at http://localhost:8000")
    server.serve_forever()

def main():
    global vpn_handler
    vpn_handler = VPNHandler()

    # Start the server in a separate thread
    server_thread = Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    # Wait for the server to start
    time.sleep(1)

    # Open the web interface
    webbrowser.open('http://localhost:8000')

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        vpn_handler.stop_vpn()
        sys.exit(0)

if __name__ == '__main__':
    main() 