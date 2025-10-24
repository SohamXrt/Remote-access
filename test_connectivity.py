#!/usr/bin/env python3
"""
Simple test server to verify mobile device connectivity
"""
import http.server
import socketserver
import json
import socket

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"

class TestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/test':
            response = {
                "status": "ok",
                "message": "Mobile connectivity test successful!",
                "client_ip": self.client_address[0],
                "server_ip": get_local_ip(),
                "timestamp": __import__('datetime').datetime.now().isoformat()
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            self.wfile.write(json.dumps(response, indent=2).encode())
        else:
            self.send_response(404)
            self.end_headers()
            
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

if __name__ == "__main__":
    PORT = 8001
    local_ip = get_local_ip()
    
    with socketserver.TCPServer(("", PORT), TestHandler) as httpd:
        print(f"🧪 Mobile Connectivity Test Server")
        print(f"📱 Test URL: http://{local_ip}:{PORT}/test")
        print(f"🌐 Local URL: http://localhost:{PORT}/test")
        print("=" * 50)
        print("Open this URL in your phone's browser to test connectivity:")
        print(f"http://{local_ip}:{PORT}/test")
        print("=" * 50)
        print("Press Ctrl+C to stop")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Test server stopped")