#!/usr/bin/env python3
"""
Simple Cloud Relay Server for websockets 15.x
"""
import asyncio
import websockets
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global state
devices = {}  # device_id -> websocket
device_info = {}  # device_id -> info
paired_devices = set()  # pairs of (device1, device2)

async def handle_client(websocket):
    """Handle WebSocket client connection"""
    device_id = None
    
    try:
        # Wait for registration
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type')
                
                if msg_type == 'register':
                    # Register device
                    device_id = data.get('device_id')
                    device_type = data.get('device_type')
                    device_name = data.get('device_name', 'Unknown')
                    
                    devices[device_id] = websocket
                    device_info[device_id] = {
                        'device_type': device_type,
                        'device_name': device_name,
                        'connected_at': datetime.now().isoformat()
                    }
                    
                    await websocket.send(json.dumps({
                        'type': 'registered',
                        'device_id': device_id,
                        'message': f'{device_type} registered successfully'
                    }))
                    
                    logger.info(f"✅ {device_name} ({device_type}) registered: {device_id[:8]}...")
                    
                elif msg_type == 'pair_request':
                    # Mobile wants to pair
                    pairing_code = data.get('pairing_code')
                    device_name = data.get('device_name', 'Mobile')
                    
                    logger.info(f"📱 Pairing request from {device_name} with code: {pairing_code}")
                    
                    # Find laptops and send pairing request
                    laptop_found = False
                    for laptop_id, laptop_ws in devices.items():
                        laptop_info = device_info.get(laptop_id, {})
                        if laptop_info.get('device_type') == 'laptop':
                            try:
                                await laptop_ws.send(json.dumps({
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
                            'message': 'No laptops available'
                        }))
                        
                elif msg_type == 'pair_response':
                    # Laptop responding to pair request
                    target_id = data.get('target_device_id')
                    accepted = data.get('accepted', False)
                    message = data.get('message', '')
                    
                    if target_id in devices:
                        if accepted:
                            # Create pairing
                            paired_devices.add((device_id, target_id))
                            
                            # Notify both devices
                            await websocket.send(json.dumps({
                                'type': 'paired',
                                'peer_device_id': target_id,
                                'message': message
                            }))
                            
                            await devices[target_id].send(json.dumps({
                                'type': 'paired',
                                'peer_device_id': device_id,
                                'message': f'Successfully paired with laptop'
                            }))
                            
                            logger.info(f"✅ Devices paired: {device_id[:8]}... <-> {target_id[:8]}...")
                        else:
                            # Notify mobile of rejection
                            await devices[target_id].send(json.dumps({
                                'type': 'pairing_failed',
                                'message': message
                            }))
                            
                elif msg_type == 'relay_message':
                    # Relay message between paired devices
                    target_id = data.get('target_device_id')
                    message_type = data.get('message_type', 'generic')
                    payload = data.get('payload', {})
                    
                    # Check if devices are paired
                    pair1 = (device_id, target_id)
                    pair2 = (target_id, device_id)
                    
                    if pair1 in paired_devices or pair2 in paired_devices:
                        if target_id in devices:
                            try:
                                await devices[target_id].send(json.dumps({
                                    'type': 'relay_message',
                                    'from_device_id': device_id,
                                    'message_type': message_type,
                                    'payload': payload
                                }))
                                logger.info(f"📨 Message relayed: {device_id[:8]}... -> {target_id[:8]}... ({message_type})")
                            except:
                                pass
                                
            except json.JSONDecodeError:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': 'Invalid JSON'
                }))
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client disconnected: {device_id or 'unknown'}")
    except Exception as e:
        logger.error(f"Client handler error: {e}")
    finally:
        # Cleanup
        if device_id:
            if device_id in devices:
                del devices[device_id]
            if device_id in device_info:
                info = device_info[device_id]
                logger.info(f"❌ {info['device_name']} disconnected")
                del device_info[device_id]
            
            # Remove from paired devices
            to_remove = []
            for pair in paired_devices:
                if device_id in pair:
                    to_remove.append(pair)
            for pair in to_remove:
                paired_devices.remove(pair)

async def main():
    """Start the server"""
    HOST = "0.0.0.0"
    PORT = 8765
    
    logger.info(f"🌐 Simple Cloud Relay starting on {HOST}:{PORT}")
    
    async with websockets.serve(handle_client, HOST, PORT):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Server stopped")