#!/usr/bin/env python3
"""
Simple HTTP server to serve the mobile app
"""
import http.server
import socketserver
import socket
import webbrowser
from pathlib import Path

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"

class SimpleHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            # Serve the simple mobile app
            self.path = '/simple_mobile_app.html'
        elif self.path == '/check-biometric' or self.path == '/check-biometric.html':
            # Serve the biometric checker
            self.path = '/check_biometric.html'
        
        # Add CORS headers
        if self.path.endswith('.html'):
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            # Read and serve the file
            try:
                if self.path == '/check_biometric.html':
                    filename = 'check_biometric.html'
                else:
                    filename = 'simple_mobile_app.html'
                    
                with open(filename, 'r') as f:
                    self.wfile.write(f.read().encode())
            except FileNotFoundError:
                self.wfile.write(b'<h1>File not found</h1>')
        else:
            super().do_GET()

if __name__ == "__main__":
    PORT = 8080
    local_ip = get_local_ip()
    
    # Change to the correct directory
    import os
    os.chdir(Path(__file__).parent)
    
    with socketserver.TCPServer(("", PORT), SimpleHandler) as httpd:
        print("🔒 Simple Laptop Remote Access")
        print("=" * 50)
        print(f"📱 Mobile URL: http://{local_ip}:{PORT}")
        print(f"🌐 Local URL: http://localhost:{PORT}")
        print("=" * 50)
        print("Instructions:")
        print("1. Make sure backend server is running (python mobile_backend/server.py)")
        print("2. Generate pairing code (python terminal_client/auth_client.py)")
        print(f"3. Open http://{local_ip}:{PORT} on your phone")
        print("4. Test connection, then enter pairing code")
        print("=" * 50)
        print("Press Ctrl+C to stop")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")