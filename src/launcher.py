import os
import sys
import http.server
import socketserver
import webbrowser
import json
from vpn_handler import VPNHandler

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Initialize VPN handler globally
vpn_handler = VPNHandler()

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vpn_handler = vpn_handler

    def end_headers(self):
        """Add CORS headers"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        """Handle OPTIONS request for CORS"""
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        """Handle GET requests"""
        if self.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        """Handle POST requests"""
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode("utf-8"))
        
        response = {'success': False, 'error': 'Unknown action'}
        
        try:
            if data.get("action") == "connect":
                country = data.get("country")
                success = self.vpn_handler.start_vpn(country)
                response = {"success": success}
            elif data.get("action") == "disconnect":
                success = self.vpn_handler.stop_vpn()
                response = {"success": success}
            elif data.get("action") == "status":
                status = self.vpn_handler.get_vpn_status()
                response = {
                    "success": True,
                    "status": status,
                    "servers": [{'country': node.country, 'host': node.host, 'port': node.port} 
                              for node in self.vpn_handler.vpn_nodes]
                }
        except Exception as e:
            response = {'success': False, 'error': str(e)}
        
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode("utf-8"))

def main():
    """Main function to start the server"""
    PORT = 8000
    Handler.extensions_map = {
        '': 'application/octet-stream',
        '.html': 'text/html',
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.json': 'application/json',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.ico': 'image/x-icon',
    }
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"VPN Server running at http://localhost:{PORT}")
        webbrowser.open(f"http://localhost:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    main() 