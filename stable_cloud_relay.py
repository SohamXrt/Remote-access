#!/usr/bin/env python3
"""
Stable Cloud Relay Server
Rock-solid version with comprehensive error handling
"""
import asyncio
import websockets
import json
import logging
from datetime import datetime
import traceback

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global state
devices = {}  # device_id -> websocket
device_info = {}  # device_id -> info
paired_devices = set()  # pairs of (device1, device2)

async def safe_send(websocket, message):
    """Safely send message to websocket with error handling"""
    try:
        if websocket and hasattr(websocket, 'close_code') and websocket.close_code is None:
            await websocket.send(json.dumps(message))
            return True
        elif websocket:
            await websocket.send(json.dumps(message))
            return True
    except Exception as e:
        logger.warning(f"Failed to send message: {e}")
    return False

async def handle_client(websocket):
    """Handle WebSocket client connection with robust error handling"""
    device_id = None
    
    try:
        logger.info(f"New client connected from {websocket.remote_address}")
        
        async for message in websocket:
            try:
                if isinstance(message, bytes):
                    message = message.decode('utf-8')
                
                data = json.loads(message)
                msg_type = data.get('type', '')
                
                logger.debug(f"Received {msg_type} from {device_id or 'unregistered'}")
                
                if msg_type == 'register':
                    # Register device
                    device_id = data.get('device_id', '')
                    device_type = data.get('device_type', 'unknown')
                    device_name = data.get('device_name', 'Unknown')
                    
                    if not device_id:
                        await safe_send(websocket, {
                            'type': 'error',
                            'message': 'device_id is required'
                        })
                        continue
                    
                    devices[device_id] = websocket
                    device_info[device_id] = {
                        'device_type': device_type,
                        'device_name': device_name,
                        'connected_at': datetime.now().isoformat()
                    }
                    
                    await safe_send(websocket, {
                        'type': 'registered',
                        'device_id': device_id,
                        'message': f'{device_type} registered successfully'
                    })
                    
                    logger.info(f"✅ {device_name} ({device_type}) registered: {device_id[:8]}...")
                    
                elif msg_type == 'pair_request':
                    # Mobile wants to pair
                    if not device_id:
                        await safe_send(websocket, {
                            'type': 'error', 
                            'message': 'Not registered'
                        })
                        continue
                        
                    pairing_code = data.get('pairing_code', '')
                    device_name = data.get('device_name', 'Mobile')
                    
                    logger.info(f"📱 Pairing request from {device_name} with code: {pairing_code}")
                    
                    # Find laptops and send pairing request
                    laptop_found = False
                    for laptop_id, laptop_ws in list(devices.items()):
                        if laptop_id == device_id:
                            continue
                            
                        laptop_info = device_info.get(laptop_id, {})
                        if laptop_info.get('device_type') == 'laptop':
                            success = await safe_send(laptop_ws, {
                                'type': 'pair_request',
                                'from_device_id': device_id,
                                'pairing_code': pairing_code,
                                'device_name': device_name
                            })
                            
                            if success:
                                laptop_found = True
                                logger.info(f"Sent pairing request to {laptop_info['device_name']}")
                                break
                    
                    if not laptop_found:
                        await safe_send(websocket, {
                            'type': 'pairing_failed',
                            'message': 'No laptops available'
                        })
                        
                elif msg_type == 'pair_response':
                    # Laptop responding to pair request
                    if not device_id:
                        continue
                        
                    target_id = data.get('target_device_id', '')
                    accepted = data.get('accepted', False)
                    message = data.get('message', '')
                    
                    if target_id in devices:
                        if accepted:
                            # Create pairing
                            pair = (device_id, target_id)
                            paired_devices.add(pair)
                            
                            # Notify both devices
                            await safe_send(websocket, {
                                'type': 'paired',
                                'peer_device_id': target_id,
                                'message': message
                            })
                            
                            await safe_send(devices[target_id], {
                                'type': 'paired',
                                'peer_device_id': device_id,
                                'message': f'Successfully paired with laptop'
                            })
                            
                            logger.info(f"✅ Devices paired: {device_id[:8]}... <-> {target_id[:8]}...")
                        else:
                            # Notify mobile of rejection
                            await safe_send(devices[target_id], {
                                'type': 'pairing_failed',
                                'message': message
                            })
                            
                elif msg_type == 'relay_message':
                    # Relay message between paired devices
                    if not device_id:
                        continue
                        
                    target_id = data.get('target_device_id', '')
                    message_type = data.get('message_type', 'generic')
                    payload = data.get('payload', {})
                    
                    # Check if devices are paired
                    pair1 = (device_id, target_id)
                    pair2 = (target_id, device_id)
                    
                    if pair1 in paired_devices or pair2 in paired_devices:
                        if target_id in devices:
                            success = await safe_send(devices[target_id], {
                                'type': 'relay_message',
                                'from_device_id': device_id,
                                'message_type': message_type,
                                'payload': payload
                            })
                            
                            if success:
                                logger.info(f"📨 Message relayed: {device_id[:8]}... -> {target_id[:8]}... ({message_type})")
                            else:
                                await safe_send(websocket, {
                                    'type': 'relay_failed',
                                    'message': 'Failed to deliver message'
                                })
                        else:
                            await safe_send(websocket, {
                                'type': 'relay_failed', 
                                'message': 'Target device offline'
                            })
                    else:
                        await safe_send(websocket, {
                            'type': 'relay_failed',
                            'message': 'Devices not paired'
                        })
                        
                elif msg_type == 'ping':
                    await safe_send(websocket, {'type': 'pong'})
                    
                else:
                    logger.warning(f"Unknown message type: {msg_type}")
                    await safe_send(websocket, {
                        'type': 'error',
                        'message': f'Unknown message type: {msg_type}'
                    })
                                
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON from {device_id}: {e}")
                await safe_send(websocket, {
                    'type': 'error',
                    'message': 'Invalid JSON format'
                })
            except Exception as e:
                logger.error(f"Error handling message from {device_id}: {e}")
                logger.error(traceback.format_exc())
                await safe_send(websocket, {
                    'type': 'error',
                    'message': 'Internal server error'
                })
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client disconnected: {device_id or 'unknown'}")
    except Exception as e:
        logger.error(f"Client handler error: {e}")
        logger.error(traceback.format_exc())
    finally:
        # Cleanup
        if device_id:
            try:
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
                    
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

async def main():
    """Start the server with robust error handling"""
    HOST = "0.0.0.0"
    PORT = 8765
    
    logger.info(f"🌐 Stable Cloud Relay starting on {HOST}:{PORT}")
    
    while True:
        try:
            async with websockets.serve(handle_client, HOST, PORT):
                logger.info("✅ Server started successfully")
                await asyncio.Future()  # Run forever
                
        except KeyboardInterrupt:
            logger.info("👋 Server stopped by user")
            break
        except Exception as e:
            logger.error(f"Server error: {e}")
            logger.error(traceback.format_exc())
            logger.info("🔄 Restarting server in 5 seconds...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())