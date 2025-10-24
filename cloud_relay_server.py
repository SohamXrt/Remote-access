#!/usr/bin/env python3
"""
Cloud Relay Server for Distance-Independent Laptop Remote Access
Allows mobile and laptop to communicate regardless of network/distance
"""
import asyncio
import websockets
import json
import uuid
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CloudRelay:
    def __init__(self):
        self.devices = {}  # device_id -> websocket connection
        self.device_info = {}  # device_id -> device metadata
        self.paired_devices = set()  # Set of (laptop_id, mobile_id) pairs
        
    async def register_device(self, websocket, device_data):
        """Register a new device (laptop or mobile)"""
        device_id = device_data.get('device_id')
        device_type = device_data.get('device_type')  # 'laptop' or 'mobile'
        device_name = device_data.get('device_name', 'Unknown Device')
        
        if not device_id or not device_type:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': 'Missing device_id or device_type'
            }))
            return False
            
        # Store device connection and info
        self.devices[device_id] = websocket
        self.device_info[device_id] = {
            'device_type': device_type,
            'device_name': device_name,
            'connected_at': datetime.now().isoformat(),
            'last_seen': datetime.now().isoformat()
        }
        
        logger.info(f"Device registered: {device_name} ({device_type}) - {device_id[:8]}...")
        
        # Send confirmation
        await websocket.send(json.dumps({
            'type': 'registered',
            'device_id': device_id,
            'message': f'{device_type.title()} connected successfully'
        }))
        
        # Notify about available devices
        await self.broadcast_device_list()
        return True
        
    async def handle_pairing(self, data):
        """Handle device pairing requests"""
        laptop_id = data.get('laptop_id')
        mobile_id = data.get('mobile_id')
        pairing_code = data.get('pairing_code')
        
        if not all([laptop_id, mobile_id, pairing_code]):
            return {'type': 'pairing_failed', 'message': 'Missing required fields'}
            
        # In production, validate pairing code
        # For now, accept any 6-digit code
        if len(pairing_code) != 6 or not pairing_code.isdigit():
            return {'type': 'pairing_failed', 'message': 'Invalid pairing code format'}
            
        # Create pairing
        pair = (laptop_id, mobile_id)
        self.paired_devices.add(pair)
        
        logger.info(f"Devices paired: {laptop_id[:8]}... <-> {mobile_id[:8]}...")
        
        # Notify both devices
        laptop_msg = {
            'type': 'paired',
            'peer_device_id': mobile_id,
            'peer_device_type': 'mobile',
            'message': 'Mobile device paired successfully'
        }
        
        mobile_msg = {
            'type': 'paired',
            'peer_device_id': laptop_id,
            'peer_device_type': 'laptop',
            'message': 'Laptop paired successfully'
        }
        
        if laptop_id in self.devices:
            await self.devices[laptop_id].send(json.dumps(laptop_msg))
        if mobile_id in self.devices:
            await self.devices[mobile_id].send(json.dumps(mobile_msg))
            
        return {'type': 'pairing_success', 'message': 'Devices paired successfully'}
        
    async def relay_message(self, sender_id, data):
        """Relay message between paired devices"""
        target_id = data.get('target_device_id')
        message_type = data.get('message_type', 'generic')
        payload = data.get('payload', {})
        
        if not target_id:
            return {'type': 'relay_failed', 'message': 'Missing target_device_id'}
            
        # Check if devices are paired
        sender_info = self.device_info.get(sender_id)
        target_info = self.device_info.get(target_id)
        
        if not sender_info or not target_info:
            return {'type': 'relay_failed', 'message': 'Device not found'}
            
        # Check pairing (either direction)
        pair1 = (sender_id, target_id)
        pair2 = (target_id, sender_id)
        
        if pair1 not in self.paired_devices and pair2 not in self.paired_devices:
            return {'type': 'relay_failed', 'message': 'Devices not paired'}
            
        # Relay the message
        if target_id in self.devices:
            relay_msg = {
                'type': 'relay_message',
                'from_device_id': sender_id,
                'from_device_type': sender_info['device_type'],
                'message_type': message_type,
                'payload': payload,
                'timestamp': datetime.now().isoformat()
            }
            
            try:
                await self.devices[target_id].send(json.dumps(relay_msg))
                logger.info(f"Message relayed: {sender_id[:8]}... -> {target_id[:8]}... ({message_type})")
                return {'type': 'relay_success', 'message': 'Message delivered'}
            except Exception as e:
                logger.error(f"Failed to relay message: {e}")
                return {'type': 'relay_failed', 'message': 'Failed to deliver message'}
        else:
            return {'type': 'relay_failed', 'message': 'Target device not connected'}
            
    async def broadcast_device_list(self):
        """Broadcast available devices to all connected devices"""
        device_list = []
        for device_id, info in self.device_info.items():
            if device_id in self.devices:  # Only include connected devices
                device_list.append({
                    'device_id': device_id,
                    'device_type': info['device_type'],
                    'device_name': info['device_name'],
                    'last_seen': info['last_seen']
                })
                
        broadcast_msg = {
            'type': 'device_list',
            'devices': device_list,
            'total_devices': len(device_list)
        }
        
        # Send to all connected devices
        disconnected = []
        for device_id, websocket in self.devices.items():
            try:
                await websocket.send(json.dumps(broadcast_msg))
            except:
                disconnected.append(device_id)
                
        # Clean up disconnected devices
        for device_id in disconnected:
            await self.disconnect_device(device_id)
            
    async def disconnect_device(self, device_id):
        """Handle device disconnection"""
        if device_id in self.devices:
            del self.devices[device_id]
            
        if device_id in self.device_info:
            device_info = self.device_info[device_id]
            logger.info(f"Device disconnected: {device_info['device_name']} - {device_id[:8]}...")
            del self.device_info[device_id]
            
        # Remove from paired devices
        to_remove = []
        for pair in self.paired_devices:
            if device_id in pair:
                to_remove.append(pair)
        for pair in to_remove:
            self.paired_devices.remove(pair)
            
        # Update device list for remaining devices
        await self.broadcast_device_list()
        
    async def handle_message(self, websocket, device_id, message):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            # Update last seen
            if device_id in self.device_info:
                self.device_info[device_id]['last_seen'] = datetime.now().isoformat()
                
            if message_type == 'ping':
                await websocket.send(json.dumps({'type': 'pong'}))
                
            elif message_type == 'pair_request':
                # Handle pairing request from mobile device
                pairing_code = data.get('pairing_code')
                device_name = data.get('device_name', 'Unknown Mobile')
                
                # Find available laptops with matching pairing code
                laptop_found = False
                for laptop_id, laptop_websocket in self.devices.items():
                    laptop_info = self.device_info.get(laptop_id)
                    if laptop_info and laptop_info['device_type'] == 'laptop':
                        # Send pairing request to laptop
                        try:
                            await laptop_websocket.send(json.dumps({
                                'type': 'pair_request',
                                'from_device_id': device_id,
                                'pairing_code': pairing_code,
                                'device_name': device_name
                            }))
                            laptop_found = True
                            break
                        except:
                            pass
                
                if not laptop_found:
                    await websocket.send(json.dumps({
                        'type': 'pairing_failed',
                        'message': 'No available laptops found'
                    }))
                    
            elif message_type == 'pair_response':
                # Handle pairing response from laptop
                target_id = data.get('target_device_id')
                accepted = data.get('accepted', False)
                message = data.get('message', '')
                
                if target_id in self.devices:
                    if accepted:
                        # Create pairing
                        pair = (device_id, target_id)
                        self.paired_devices.add(pair)
                        
                        # Notify both devices
                        await websocket.send(json.dumps({
                            'type': 'paired',
                            'peer_device_id': target_id,
                            'message': message
                        }))
                        
                        await self.devices[target_id].send(json.dumps({
                            'type': 'paired',
                            'peer_device_id': device_id,
                            'message': f'Paired with laptop'
                        }))
                    else:
                        # Notify mobile of rejection
                        await self.devices[target_id].send(json.dumps({
                            'type': 'pairing_failed',
                            'message': message
                        }))
                        
            elif message_type == 'relay_message':
                result = await self.relay_message(device_id, data)
                # Don't send result back, the relay handles it
                
            elif message_type == 'get_devices':
                await self.broadcast_device_list()
                
            else:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                }))
                
        except json.JSONDecodeError:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': 'Invalid JSON message'
            }))
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await websocket.send(json.dumps({
                'type': 'error',
                'message': 'Internal server error'
            }))

# Global relay instance
relay = CloudRelay()

async def handle_client(websocket):
    """Handle new WebSocket client connection"""
    device_id = None
    try:
        # Wait for registration message
        registration_msg = await websocket.recv()
        registration_data = json.loads(registration_msg)
        
        if registration_data.get('type') != 'register':
            await websocket.send(json.dumps({
                'type': 'error',
                'message': 'First message must be registration'
            }))
            return
            
        # Register the device
        success = await relay.register_device(websocket, registration_data)
        if not success:
            return
            
        device_id = registration_data.get('device_id')
        
        # Handle ongoing messages
        async for message in websocket:
            await relay.handle_message(websocket, device_id, message)
            
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client disconnected: {device_id or 'unknown'}")
    except Exception as e:
        logger.error(f"Error in client handler: {e}")
    finally:
        if device_id:
            await relay.disconnect_device(device_id)

async def main():
    """Start the cloud relay server"""
    HOST = "0.0.0.0"
    PORT = 8765
    
    logger.info(f"🌐 Starting Cloud Relay Server on {HOST}:{PORT}")
    logger.info("📱 Mobile devices and 💻 laptops can connect from anywhere!")
    
    try:
        async with websockets.serve(handle_client, HOST, PORT):
            await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        logger.info("🛑 Cloud Relay Server stopped")

if __name__ == "__main__":
    asyncio.run(main())
