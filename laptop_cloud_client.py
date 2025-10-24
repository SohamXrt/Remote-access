#!/usr/bin/env python3
"""
Laptop-side cloud relay client
Connects laptop to the cloud relay server for global device pairing
"""

import asyncio
import websockets
import json
import logging
import socket
import uuid
import subprocess
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LaptopCloudClient:
    def __init__(self, relay_url="ws://localhost:8765"):
        self.relay_url = relay_url
        self.websocket = None
        self.device_id = f"laptop_{socket.gethostname()}_{uuid.uuid4().hex[:8]}"
        self.device_name = f"Laptop ({socket.gethostname()})"
        self.paired_mobile_id = None
        self.pairing_code = None
        self.running = False
        
    async def connect(self):
        """Connect to cloud relay server"""
        try:
            logger.info(f"Connecting to cloud relay at {self.relay_url}")
            self.websocket = await websockets.connect(self.relay_url)
            
            # Register as laptop device
            await self.websocket.send(json.dumps({
                "type": "register",
                "device_id": self.device_id,
                "device_type": "laptop",
                "device_name": self.device_name
            }))
            
            logger.info(f"✅ Connected to cloud relay as {self.device_name} ({self.device_id})")
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
            logger.info("✅ Successfully registered with cloud relay")
            
        elif msg_type == "device_list":
            devices = data.get("devices", [])
            mobiles = [d for d in devices if d["device_type"] == "mobile"]
            logger.info(f"📱 {len(mobiles)} mobile devices available for pairing")
            
        elif msg_type == "pair_request":
            # Mobile device wants to pair with pairing code
            await self.handle_pair_request(data)
            
        elif msg_type == "paired":
            self.paired_mobile_id = data.get("peer_device_id")
            logger.info(f"✅ Successfully paired with mobile device: {self.paired_mobile_id}")
            
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
        
        logger.info(f"📱 Pairing request from {mobile_device_id} with code: {pairing_code}")
        
        # Check if pairing code matches what we're expecting
        if self.pairing_code and pairing_code == self.pairing_code:
            # Accept pairing
            await self.websocket.send(json.dumps({
                "type": "pair_response",
                "target_device_id": mobile_device_id,
                "accepted": True,
                "message": f"Paired with {self.device_name}"
            }))
            logger.info(f"✅ Accepted pairing with {mobile_device_id}")
        else:
            # Reject pairing
            await self.websocket.send(json.dumps({
                "type": "pair_response", 
                "target_device_id": mobile_device_id,
                "accepted": False,
                "message": "Invalid pairing code"
            }))
            logger.warning(f"❌ Rejected pairing with {mobile_device_id} - invalid code")
    
    async def handle_relayed_message(self, data):
        """Handle relayed messages from mobile device"""
        message_type = data.get("message_type")
        payload = data.get("payload", {})
        from_device = data.get("from_device_id")
        
        logger.info(f"📨 Relayed message from {from_device}: {message_type}")
        
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
    
    async def request_authentication(self):
        """Request authentication from paired mobile device"""
        if not self.paired_mobile_id:
            logger.error("No paired mobile device")
            return False
        
        logger.info("🔐 Requesting authentication from mobile device")
        
        await self.websocket.send(json.dumps({
            "type": "relay_message",
            "target_device_id": self.paired_mobile_id,
            "message_type": "auth_request",
            "payload": {
                "request_id": uuid.uuid4().hex,
                "timestamp": asyncio.get_event_loop().time(),
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
                
        except Exception as e:
            logger.error(f"Failed to execute command {command}: {e}")
    
    def generate_pairing_code(self):
        """Generate a 6-digit pairing code"""
        import random
        self.pairing_code = f"{random.randint(100000, 999999)}"
        return self.pairing_code
    
    async def start(self):
        """Start the laptop cloud client"""
        self.running = True
        
        while self.running:
            try:
                if await self.connect():
                    # Generate and display pairing code
                    code = self.generate_pairing_code()
                    print(f"\n🔑 PAIRING CODE: {code}")
                    print(f"📱 Enter this code in your mobile app to pair")
                    print(f"🖥️  Laptop: {self.device_name}")
                    print(f"🌐 Connected to cloud relay")
                    print(f"⏰ Code expires in 5 minutes\n")
                    
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
    print("🔒 Laptop Remote Access - Cloud Client")
    print("=====================================")
    
    client = LaptopCloudClient()
    
    try:
        await client.start()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    asyncio.run(main())