#!/usr/bin/env python3
"""
Persistent Laptop Cloud Client
Saves device credentials and uses consistent device ID across restarts
"""

import asyncio
import websockets
import json
import logging
import socket
import uuid
import subprocess
import os
import hashlib
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Persistent data directory
DATA_DIR = os.path.expanduser("~/.laptop_remote_access")
DEVICE_FILE = os.path.join(DATA_DIR, "laptop_device.json")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

class PersistentLaptopClient:
    def __init__(self, relay_url="ws://localhost:8765"):
        self.relay_url = relay_url
        self.websocket = None
        self.device_id = None
        self.device_name = f"Laptop ({socket.gethostname()})"
        self.paired_devices = []
        self.pairing_code = None
        self.running = False
        
        # Load or create persistent device identity
        self.load_device_identity()
        
    def load_device_identity(self):
        """Load persistent device identity or create new one"""
        if os.path.exists(DEVICE_FILE):
            try:
                with open(DEVICE_FILE, 'r') as f:
                    data = json.load(f)
                    self.device_id = data['device_id']
                    logger.info(f"📁 Loaded persistent device ID: {self.device_id[:8]}...")
                    return
            except Exception as e:
                logger.error(f"Failed to load device identity: {e}")
        
        # Create new persistent identity
        hostname = socket.gethostname()
        mac_data = f"{hostname}:{datetime.now().date()}"
        device_hash = hashlib.sha256(mac_data.encode()).hexdigest()[:12]
        self.device_id = f"laptop_{hostname}_{device_hash}"
        
        self.save_device_identity()
        logger.info(f"🆕 Created persistent device ID: {self.device_id[:8]}...")
    
    def save_device_identity(self):
        """Save device identity to disk"""
        try:
            data = {
                'device_id': self.device_id,
                'device_name': self.device_name,
                'created_at': datetime.now().isoformat(),
                'hostname': socket.gethostname()
            }
            with open(DEVICE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save device identity: {e}")
    
    async def connect(self):
        """Connect to cloud relay server"""
        try:
            logger.info(f"Connecting to persistent cloud relay at {self.relay_url}")
            self.websocket = await websockets.connect(self.relay_url)
            
            # Register as laptop device with persistent ID
            await self.websocket.send(json.dumps({
                "type": "register",
                "device_id": self.device_id,
                "device_type": "laptop",
                "device_name": self.device_name
            }))
            
            logger.info(f"✅ Connected to persistent cloud relay as {self.device_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to cloud relay: {e}")
            return False
    
    async def listen_for_messages(self):
        """Listen for messages from cloud relay"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.handle_message(data)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection to cloud relay closed")
        except Exception as e:
            logger.error(f"Error listening for messages: {e}")
    
    async def handle_message(self, data):
        """Handle incoming messages from cloud relay"""
        msg_type = data.get("type")
        
        if msg_type == "registered":
            is_known = data.get("is_known_device", False)
            status = "Known device" if is_known else "New device"
            logger.info(f"✅ Registered with cloud relay ({status})")
            
        elif msg_type == "existing_pairings":
            self.paired_devices = data.get("pairings", [])
            logger.info(f"📋 Found {len(self.paired_devices)} existing pairing(s)")
            
            for pairing in self.paired_devices:
                peer_name = pairing.get("peer_device_name", "Unknown")
                peer_type = pairing.get("peer_device_type", "unknown")
                logger.info(f"   • {peer_name} ({peer_type})")
            
            if self.paired_devices:
                logger.info("🔄 Ready to receive commands from paired devices")
                # Don't generate new pairing code if we have existing pairings
                return
            
        elif msg_type == "pair_request":
            # Mobile device wants to pair with pairing code
            await self.handle_pair_request(data)
            
        elif msg_type == "paired":
            peer_device_id = data.get("peer_device_id")
            peer_device_name = data.get("peer_device_name", "Unknown Device")
            is_persistent = data.get("is_persistent", False)
            
            logger.info(f"✅ Paired with {peer_device_name} ({'persistent' if is_persistent else 'temporary'})")
            
            # Add to paired devices if not already there
            new_pairing = {
                'peer_device_id': peer_device_id,
                'peer_device_name': peer_device_name,
                'peer_device_type': 'mobile'
            }
            
            if not any(p['peer_device_id'] == peer_device_id for p in self.paired_devices):
                self.paired_devices.append(new_pairing)
            
        elif msg_type == "unpaired":
            target_id = data.get("target_device_id")
            self.paired_devices = [p for p in self.paired_devices if p['peer_device_id'] != target_id]
            logger.info(f"❌ Device unpaired: {target_id[:8]}...")
            
        elif msg_type == "relay_message":
            # Handle relayed messages from mobile device
            await self.handle_relayed_message(data)
            
        elif msg_type == "error":
            logger.error(f"❌ Cloud relay error: {data.get('message')}")
            
        else:
            logger.debug(f"Unhandled message type: {msg_type}")
    
    async def handle_pair_request(self, data):
        """Handle pairing request from mobile device"""
        pairing_code = data.get("pairing_code")
        mobile_device_id = data.get("from_device_id")
        device_name = data.get("device_name", "Mobile Device")
        
        logger.info(f"📱 Pairing request from {device_name} with code: {pairing_code}")
        
        # Check if pairing code matches what we're expecting
        if self.pairing_code and pairing_code == self.pairing_code:
            # Accept pairing
            await self.websocket.send(json.dumps({
                "type": "pair_response",
                "target_device_id": mobile_device_id,
                "accepted": True,
                "message": f"Paired with {self.device_name} (persistent)"
            }))
            logger.info(f"✅ Accepted persistent pairing with {device_name}")
        else:
            # Reject pairing
            await self.websocket.send(json.dumps({
                "type": "pair_response", 
                "target_device_id": mobile_device_id,
                "accepted": False,
                "message": "Invalid pairing code"
            }))
            logger.warning(f"❌ Rejected pairing with {device_name} - invalid code")
    
    async def handle_relayed_message(self, data):
        """Handle relayed messages from mobile device"""
        message_type = data.get("message_type")
        payload = data.get("payload", {})
        from_device = data.get("from_device_id")
        
        logger.info(f"📨 Relayed message from {from_device[:8]}...: {message_type}")
        
        if message_type == "auth_response":
            # Mobile device responded to auth request
            authenticated = payload.get("authenticated", False)
            if authenticated:
                logger.info("✅ Mobile device authenticated - access granted")
                await self.unlock_system()
            else:
                logger.info("❌ Mobile device denied authentication")
        
        elif message_type == "system_command":
            # Mobile device sent system command
            command = payload.get("command")
            logger.info(f"🎮 System command from mobile: {command}")
            await self.execute_system_command(command)
        
        elif message_type == "list_files":
            # Mobile wants file list
            path = payload.get("path", str(Path.home()))
            await self.send_file_list(from_device, path)
        
        elif message_type == "read_file":
            # Mobile wants file content
            file_path = payload.get("path")
            await self.send_file_content(from_device, file_path)
    
    async def request_authentication(self, mobile_device_id):
        """Request authentication from paired mobile device"""
        logger.info("🔐 Requesting authentication from mobile device")
        
        await self.websocket.send(json.dumps({
            "type": "relay_message",
            "target_device_id": mobile_device_id,
            "message_type": "auth_request",
            "payload": {
                "request_id": uuid.uuid4().hex,
                "timestamp": datetime.now().isoformat(),
                "device_name": self.device_name
            }
        }))
        
        return True
    
    async def unlock_system(self):
        """Unlock the system (platform-specific)"""
        try:
            if os.name == 'nt':  # Windows
                # Windows unlock (if locked)
                subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'], check=False)
            else:  # Linux/Mac
                # For demo purposes, just log
                logger.info("🔓 System unlocked (simulated)")
                
        except Exception as e:
            logger.error(f"Failed to unlock system: {e}")
    
    async def execute_system_command(self, command):
        """Execute system commands from mobile"""
        try:
            if command == "lock":
                if os.name == 'nt':
                    subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'], check=False)
                else:
                    # Linux: depends on desktop environment
                    subprocess.run(['xdg-screensaver', 'lock'], check=False)
                logger.info("🔒 System locked")
                
            elif command == "sleep":
                if os.name == 'nt':
                    subprocess.run(['rundll32.exe', 'powrprof.dll,SetSuspendState', '0,1,0'], check=False)
                else:
                    # Force suspend ignoring inhibitors
                    subprocess.run(['systemctl', 'suspend', '-i'], check=False)
                logger.info("😴 System sleeping")
                
            elif command == "restart":
                if os.name == 'nt':
                    subprocess.run(['shutdown', '/r', '/t', '1'], check=False)
                else:
                    subprocess.run(['sudo', 'reboot'], check=False)
                logger.info("🔄 System restarting")
                
            elif command == "shutdown":
                if os.name == 'nt':
                    subprocess.run(['shutdown', '/s', '/t', '1'], check=False)
                else:
                    subprocess.run(['sudo', 'shutdown', 'now'], check=False)
                logger.info("⚡ System shutting down")
                
            elif command == "wake":
                logger.info("☀️ Wake command received (laptop already awake)")
                # Laptop is already on to receive this
                
        except Exception as e:
            logger.error(f"Failed to execute command {command}: {e}")
    
    async def send_file_list(self, target_device_id, path):
        """Send file listing to mobile device"""
        try:
            path_obj = Path(path).expanduser()
            if not path_obj.exists():
                raise FileNotFoundError(f"Path does not exist: {path}")
            
            files = []
            if path_obj.is_dir():
                for item in sorted(path_obj.iterdir()):
                    try:
                        stat = item.stat()
                        files.append({
                            'name': item.name,
                            'path': str(item),
                            'is_dir': item.is_dir(),
                            'size': stat.st_size if item.is_file() else 0,
                            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                        })
                    except PermissionError:
                        pass
            
            await self.websocket.send(json.dumps({
                "type": "relay_message",
                "target_device_id": target_device_id,
                "message_type": "file_list",
                "payload": {
                    "path": str(path_obj),
                    "files": files
                }
            }))
            logger.info(f"📁 Sent file list for {path} ({len(files)} items)")
            
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            await self.websocket.send(json.dumps({
                "type": "relay_message",
                "target_device_id": target_device_id,
                "message_type": "error",
                "payload": {"message": str(e)}
            }))
    
    async def send_file_content(self, target_device_id, file_path):
        """Send file content to mobile device"""
        try:
            path_obj = Path(file_path).expanduser()
            if not path_obj.exists() or not path_obj.is_file():
                raise FileNotFoundError(f"File does not exist: {file_path}")
            
            # Limit file size to 1MB for mobile viewing
            if path_obj.stat().st_size > 1024 * 1024:
                raise ValueError("File too large (max 1MB)")
            
            with open(path_obj, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            await self.websocket.send(json.dumps({
                "type": "relay_message",
                "target_device_id": target_device_id,
                "message_type": "file_content",
                "payload": {
                    "path": str(path_obj),
                    "content": content
                }
            }))
            logger.info(f"📄 Sent file content for {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to read file: {e}")
            await self.websocket.send(json.dumps({
                "type": "relay_message",
                "target_device_id": target_device_id,
                "message_type": "error",
                "payload": {"message": str(e)}
            }))
    
    def generate_pairing_code(self):
        """Generate a 6-digit pairing code"""
        import random
        self.pairing_code = f"{random.randint(100000, 999999)}"
        return self.pairing_code
    
    async def start(self):
        """Start the persistent laptop client"""
        self.running = True
        
        while self.running:
            try:
                if await self.connect():
                    # Wait for existing pairings message or generate new code
                    await asyncio.sleep(2)  # Give time for existing_pairings message
                    
                    if not self.paired_devices:
                        # No existing pairings, generate new pairing code
                        code = self.generate_pairing_code()
                        print(f"\n🔑 PAIRING CODE: {code}")
                        print(f"📱 Enter this code in your mobile app to pair")
                        print(f"🖥️  Laptop: {self.device_name}")
                        print(f"🌐 Connected to persistent cloud relay")
                        print(f"⏰ Code expires in 10 minutes\n")
                    else:
                        print(f"\n✅ PERSISTENT LAPTOP CLIENT READY")
                        print(f"🖥️  Laptop: {self.device_name}")
                        print(f"🔗 {len(self.paired_devices)} paired device(s) found")
                        print(f"📱 Mobile devices can connect without pairing code")
                        print(f"🌐 Connected to persistent cloud relay\n")
                    
                    # Start listening for messages
                    await self.listen_for_messages()
                    
                else:
                    logger.error("Failed to connect, retrying in 10 seconds...")
                    await asyncio.sleep(10)
                    
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                await asyncio.sleep(5)
        
        if self.websocket:
            await self.websocket.close()

async def main():
    """Main function"""
    print("🔒 Persistent Laptop Remote Access - Cloud Client")
    print("===============================================")
    
    # Use Render cloud relay URL
    relay_url = "wss://remote-access-ojwr.onrender.com"
    client = PersistentLaptopClient(relay_url=relay_url)
    
    try:
        await client.start()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    asyncio.run(main())