#!/usr/bin/env python3
"""
Authentication client that bridges the terminal UI with the mobile backend
Handles the complete biometric authentication flow
"""
import os
import sys
import time
import asyncio
import threading
import requests
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.crypto_utils import CryptoManager
from terminal_client.auth_terminal import HackerTerminal

class AuthenticationClient:
    def __init__(self):
        self.crypto_manager = CryptoManager(config_dir="../configs")
        self.terminal = HackerTerminal()
        self.server_url = "http://localhost:8000"
        self.authenticated = False
        self.session_active = False
        
    def check_server_connection(self):
        """Check if the backend server is running"""
        try:
            response = requests.get(f"{self.server_url}/", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
            
    def get_paired_devices(self):
        """Get list of paired mobile devices"""
        paired_devices = self.crypto_manager.load_paired_devices()
        return list(paired_devices.keys()) if paired_devices else []
        
    def request_biometric_auth(self, device_id, message="System login authentication required"):
        """Request biometric authentication from a mobile device"""
        try:
            response = requests.post(
                f"{self.server_url}/auth-request",
                json={
                    "device_id": device_id,
                    "request_type": "biometric_auth",
                    "message": message
                },
                timeout=10
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
            
    def check_auth_status(self, device_id, timeout=30):
        """Check authentication status with polling"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(
                    f"{self.server_url}/auth-status/{device_id}",
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("status") != "pending":
                        return data.get("success", False) and data.get("biometric_verified", False)
                        
            except requests.exceptions.RequestException:
                pass
                
            time.sleep(1)
            
        return False
        
    def run_authentication_flow(self):
        """Run the complete authentication flow"""
        self.terminal.clear_screen()
        self.terminal.print_banner()
        
        # Check server connection
        if not self.check_server_connection():
            self.terminal.print_status("Backend server not available", "error")
            self.terminal.print_status("Please start the mobile backend server first", "error")
            return False
            
        # Check for paired devices
        paired_devices = self.get_paired_devices()
        
        if not paired_devices:
            self.terminal.print_status("No paired devices found", "warning")
            self.terminal.show_pairing_process()
            return False
            
        # Use the first paired device (in production, could be user selectable)
        device_id = paired_devices[0]
        self.terminal.print_status(f"Found paired device: {device_id[:8]}...", "info")
        
        # Show authentication request screen
        self.terminal.show_authentication_request()
        
        # Send authentication request to mobile device
        if not self.request_biometric_auth(device_id):
            self.terminal.print_status("Failed to send authentication request", "error")
            return False
            
        # Wait for authentication response
        self.terminal.print_status("Waiting for biometric authentication...", "info")
        
        if self.check_auth_status(device_id):
            self.terminal.print_status("Authentication successful!", "success")
            self.authenticated = True
            self.terminal.show_system_access()
            return True
        else:
            self.terminal.print_status("Authentication failed or timed out", "error")
            return False
            
    def start_session_monitor(self):
        """Start monitoring the session in the background"""
        def monitor():
            while self.session_active:
                # In production, this would monitor for system events
                # and handle re-authentication requests
                time.sleep(5)
                
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        
    def handle_login_intercept(self):
        """Handle login interception (called when user enters correct password)"""
        self.terminal.clear_screen()
        self.terminal.print_banner()
        self.terminal.monitor_system_events()
        
        # Run authentication flow
        success = self.run_authentication_flow()
        
        if success:
            self.session_active = True
            self.start_session_monitor()
            
            # Launch actual desktop session
            self.terminal.print_status("Starting desktop session...", "info")
            time.sleep(2)
            
            # In production, this would launch the actual desktop
            # os.system("gnome-session --session=ubuntu")
            
        return success
        
    def handle_system_lock(self):
        """Handle system lock event"""
        self.authenticated = False
        self.session_active = False
        self.terminal.show_lock_screen()
        
    def handle_remote_unlock_request(self):
        """Handle remote unlock request from mobile app"""
        paired_devices = self.get_paired_devices()
        
        if paired_devices:
            device_id = paired_devices[0]
            
            # Show authentication prompt
            self.terminal.clear_screen()
            self.terminal.print_banner()
            self.terminal.print_status("Remote unlock requested", "info")
            
            # Request biometric authentication
            if self.request_biometric_auth(device_id, "Remote unlock authentication"):
                self.terminal.show_authentication_request()
                
                if self.check_auth_status(device_id):
                    self.authenticated = True
                    self.session_active = True
                    
                    # Unlock the screen
                    os.system("gnome-screensaver-command --deactivate")
                    self.terminal.print_status("System unlocked successfully", "success")
                    return True
                    
        return False

class SystemIntegration:
    """Integration with Ubuntu system for login interception"""
    
    def __init__(self):
        self.auth_client = AuthenticationClient()
        
    def setup_login_hook(self):
        """Set up login interception (requires system integration)"""
        # This would typically involve:
        # 1. Creating a custom PAM module
        # 2. Modifying GDM configuration
        # 3. Setting up systemd services
        
        self.auth_client.terminal.print_status("Login hook setup required", "warning")
        self.auth_client.terminal.print_status("This requires system-level integration", "info")
        
    def create_startup_script(self):
        """Create startup script for the authentication client"""
        script_content = """#!/bin/bash
# Laptop Remote Access - Authentication Client Startup Script

cd /path/to/laptop-remote-access
source venv/bin/activate

# Start the mobile backend server in background
python mobile_backend/server.py &
SERVER_PID=$!

# Wait a moment for server to start
sleep 3

# Start the authentication terminal
python terminal_client/auth_client.py

# Clean up
kill $SERVER_PID
"""
        
        with open("../startup_auth.sh", "w") as f:
            f.write(script_content)
        
        os.chmod("../startup_auth.sh", 0o755)
        print("Startup script created: ../startup_auth.sh")

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        
        if mode == "--setup":
            integration = SystemIntegration()
            integration.setup_login_hook()
            integration.create_startup_script()
            return
            
        elif mode == "--lock":
            client = AuthenticationClient()
            client.handle_system_lock()
            
            # Wait for unlock request
            while not client.authenticated:
                time.sleep(5)
                # In production, this would listen for unlock signals
                
        elif mode == "--unlock":
            client = AuthenticationClient()
            success = client.handle_remote_unlock_request()
            sys.exit(0 if success else 1)
            
        elif mode == "--demo":
            client = AuthenticationClient()
            client.terminal.run_demo()
            return
    
    # Default: run authentication flow
    client = AuthenticationClient()
    success = client.handle_login_intercept()
    
    if success:
        print("Authentication successful - session started")
        # Keep the session alive
        try:
            while client.session_active:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nSession ended")
    else:
        print("Authentication failed")
        sys.exit(1)

if __name__ == "__main__":
    main()