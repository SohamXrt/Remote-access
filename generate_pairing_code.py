#!/usr/bin/env python3
"""
Simple script to generate pairing codes
"""
import sys
import os
import json
import qrcode
from io import StringIO

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.crypto_utils import CryptoManager

def main():
    print("🔒 LAPTOP REMOTE ACCESS - PAIRING CODE GENERATOR")
    print("=" * 60)
    
    # Initialize crypto manager
    crypto_manager = CryptoManager(config_dir="configs")
    
    # Generate pairing code via backend API to ensure validation
    import requests
    try:
        response = requests.post("http://localhost:8000/generate-pairing-code")
        if response.status_code == 200:
            data = response.json()
            pairing_code = data["pairing_code"]
        else:
            print("⚠️ Backend server not responding, generating local code...")
            pairing_code = crypto_manager.generate_pairing_code()
    except:
        print("⚠️ Could not connect to backend server, generating local code...")
        pairing_code = crypto_manager.generate_pairing_code()
    
    print(f"📱 Generated Pairing Code: {pairing_code}")
    print(f"🆔 Device ID: {crypto_manager.device_id}")
    print("=" * 60)
    
    # Create QR code data
    qr_data = json.dumps({
        "pairing_code": pairing_code,
        "device_id": crypto_manager.device_id,
        "device_name": f"Ubuntu-{os.getlogin()}",
        "server_url": "http://10.141.47.200:8000"
    })
    
    # Generate QR code
    print("📱 QR Code for mobile scanning:")
    print("-" * 60)
    
    qr = qrcode.QRCode(version=1, box_size=1, border=1)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    # Print QR code to terminal
    f = StringIO()
    qr.print_ascii(out=f)
    f.seek(0)
    qr_ascii = f.read()
    print(qr_ascii)
    
    print("-" * 60)
    print(f"Manual Pairing Code: {pairing_code}")
    print("=" * 60)
    print("Instructions:")
    print("1. Make sure backend server is running: python mobile_backend/server.py")
    print("2. Start mobile app server: python serve_simple_app.py") 
    print("3. Open http://10.141.47.200:8080 on your phone")
    print("4. Click 'Test Connection' to verify connectivity")
    print(f"5. Enter pairing code: {pairing_code}")
    print("=" * 60)

if __name__ == "__main__":
    main()