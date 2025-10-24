#!/usr/bin/env python3
"""
Mobile web server - Makes the mobile app accessible from phone browsers
"""
import os
import sys
import socket
import subprocess
from pathlib import Path

def get_local_ip():
    """Get the local IP address"""
    try:
        # Connect to a remote address to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"

def main():
    # Change to mobile app directory
    mobile_app_dir = Path("mobile_app_mockup")
    if not mobile_app_dir.exists():
        print("❌ Mobile app directory not found!")
        return
    
    os.chdir(mobile_app_dir)
    
    # Get local IP
    local_ip = get_local_ip()
    port = 8080
    
    print("📱 Starting Mobile Web Server...")
    print("=" * 50)
    print(f"🌐 Local access: http://localhost:{port}")
    print(f"📱 Mobile access: http://{local_ip}:{port}")
    print("=" * 50)
    print("📋 Instructions:")
    print("1. Make sure your phone is on the same WiFi network")
    print(f"2. Open your phone's browser and go to: http://{local_ip}:{port}")
    print("3. Add to home screen for app-like experience")
    print("4. Use the pairing code from your terminal")
    print("\n⚠️  Make sure to start the backend server first!")
    print("   Run: python mobile_backend/server.py")
    print("\n🛑 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Start HTTP server
    try:
        subprocess.run([
            "python3", "-m", "http.server", str(port), "--bind", "0.0.0.0"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Mobile web server stopped")

if __name__ == "__main__":
    main()