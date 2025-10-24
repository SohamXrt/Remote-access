#!/usr/bin/env python3
"""
Persistent Cloud Relay Server
Saves device credentials and pairings to disk for persistence across restarts
"""
import asyncio
import websockets
import json
import logging
import os
from datetime import datetime
import hashlib

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Data directory for persistence
DATA_DIR = os.path.expanduser("~/.laptop_remote_access")
DEVICES_FILE = os.path.join(DATA_DIR, "devices.json")
PAIRINGS_FILE = os.path.join(DATA_DIR, "pairings.json")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Global state
devices = {}  # device_id -> websocket (runtime only)
device_info = {}  # device_id -> info (persistent)
paired_devices = set()  # pairs of (device1, device2) (persistent)

def load_persistent_data():
    """Load device info and pairings from disk"""
    global device_info, paired_devices
    
    # Load device info
    if os.path.exists(DEVICES_FILE):
        try:
            with open(DEVICES_FILE, 'r') as f:
                device_info = json.load(f)
            logger.info(f"📁 Loaded {len(device_info)} known devices")
        except Exception as e:
            logger.error(f"Failed to load devices: {e}")
            device_info = {}
    
    # Load pairings
    if os.path.exists(PAIRINGS_FILE):
        try:
            with open(PAIRINGS_FILE, 'r') as f:
                pairing_list = json.load(f)
                paired_devices = set(tuple(pair) for pair in pairing_list)
            logger.info(f"🔗 Loaded {len(paired_devices)} trusted pairings")
        except Exception as e:
            logger.error(f"Failed to load pairings: {e}")
            paired_devices = set()

def save_persistent_data():
    """Save device info and pairings to disk"""
    try:
        # Save device info
        with open(DEVICES_FILE, 'w') as f:
            json.dump(device_info, f, indent=2)
        
        # Save pairings
        pairing_list = [list(pair) for pair in paired_devices]
        with open(PAIRINGS_FILE, 'w') as f:
            json.dump(pairing_list, f, indent=2)
            
        logger.debug("💾 Persistent data saved")
    except Exception as e:
        logger.error(f"Failed to save data: {e}")

def generate_device_fingerprint(device_id, device_name):
    """Generate a consistent fingerprint for device verification"""
    data = f"{device_id}:{device_name}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]

async def handle_client(websocket):
    """Handle WebSocket client connection"""
    device_id = None
    
    try:
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
                    
                    # Check if this is a known device
                    fingerprint = generate_device_fingerprint(device_id, device_name)
                    is_known = device_id in device_info
                    
                    if not is_known:
                        # New device - add to persistent storage
                        device_info[device_id] = {
                            'device_type': device_type,
                            'device_name': device_name,
                            'fingerprint': fingerprint,
                            'first_seen': datetime.now().isoformat(),
                            'last_seen': datetime.now().isoformat()
                        }
                        save_persistent_data()
                        logger.info(f"🆕 New {device_type}: {device_name} ({device_id[:8]}...)")
                    else:
                        # Known device - update last seen
                        device_info[device_id]['last_seen'] = datetime.now().isoformat()
                        save_persistent_data()
                        logger.info(f"🔄 Known {device_type}: {device_name} ({device_id[:8]}...)")
                    
                    await websocket.send(json.dumps({
                        'type': 'registered',
                        'device_id': device_id,
                        'is_known_device': is_known,
                        'message': f'{device_type} registered successfully'
                    }))
                    
                    # Send existing pairings for this device
                    my_pairings = []
                    for pair in paired_devices:
                        if device_id in pair:
                            peer_id = pair[1] if pair[0] == device_id else pair[0]
                            if peer_id in device_info:
                                my_pairings.append({
                                    'peer_device_id': peer_id,
                                    'peer_device_name': device_info[peer_id]['device_name'],
                                    'peer_device_type': device_info[peer_id]['device_type']
                                })
                    
                    if my_pairings:
                        await websocket.send(json.dumps({
                            'type': 'existing_pairings',
                            'pairings': my_pairings,
                            'message': f'Found {len(my_pairings)} existing pairing(s)'
                        }))
                        logger.info(f"📋 Sent {len(my_pairings)} existing pairings to {device_name}")
                    
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
                            # Create persistent pairing
                            pair = (device_id, target_id)
                            paired_devices.add(pair)
                            save_persistent_data()
                            
                            # Notify both devices
                            await websocket.send(json.dumps({
                                'type': 'paired',
                                'peer_device_id': target_id,
                                'peer_device_name': device_info[target_id]['device_name'],
                                'is_persistent': True,
                                'message': message
                            }))
                            
                            await devices[target_id].send(json.dumps({
                                'type': 'paired',
                                'peer_device_id': device_id,
                                'peer_device_name': device_info[device_id]['device_name'],
                                'is_persistent': True,
                                'message': f'Successfully paired with laptop (persistent)'
                            }))
                            
                            logger.info(f"✅ Persistent pairing created: {device_id[:8]}... <-> {target_id[:8]}...")
                        else:
                            # Notify mobile of rejection
                            await devices[target_id].send(json.dumps({
                                'type': 'pairing_failed',
                                'message': message
                            }))
                
                elif msg_type == 'unpair_device':
                    # Remove pairing
                    target_id = data.get('target_device_id')
                    
                    # Remove from paired devices
                    to_remove = []
                    for pair in paired_devices:
                        if device_id in pair and target_id in pair:
                            to_remove.append(pair)
                    
                    for pair in to_remove:
                        paired_devices.remove(pair)
                    
                    save_persistent_data()
                    
                    await websocket.send(json.dumps({
                        'type': 'unpaired',
                        'target_device_id': target_id,
                        'message': 'Device unpaired successfully'
                    }))
                    
                    # Notify the other device if connected
                    if target_id in devices:
                        await devices[target_id].send(json.dumps({
                            'type': 'unpaired',
                            'target_device_id': device_id,
                            'message': 'Device was unpaired remotely'
                        }))
                    
                    logger.info(f"❌ Devices unpaired: {device_id[:8]}... <-> {target_id[:8]}...")
                            
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
                        else:
                            # Target device not currently connected
                            await websocket.send(json.dumps({
                                'type': 'relay_failed',
                                'message': 'Target device is offline'
                            }))
                    else:
                        await websocket.send(json.dumps({
                            'type': 'relay_failed',
                            'message': 'Devices are not paired'
                        }))
                                
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
        # Cleanup runtime state
        if device_id and device_id in devices:
            del devices[device_id]
            if device_id in device_info:
                device_info[device_id]['last_seen'] = datetime.now().isoformat()
                save_persistent_data()
                logger.info(f"❌ {device_info[device_id]['device_name']} disconnected")

async def main():
    """Start the server"""
    HOST = "0.0.0.0"
    PORT = 8765
    
    logger.info(f"🌐 Persistent Cloud Relay starting on {HOST}:{PORT}")
    logger.info(f"💾 Data stored in: {DATA_DIR}")
    
    # Load persistent data
    load_persistent_data()

    MAX_PORT_RETRIES = 5
    current_port = PORT
    
    for i in range(MAX_PORT_RETRIES):
        try:
            logger.info(f"🌐 Persistent Cloud Relay trying to start on {HOST}:{current_port}")
            async with websockets.serve(handle_client, HOST, current_port, reuse_address=True):
                logger.info(f"✅ Persistent Cloud Relay successfully started on {HOST}:{current_port}")
                await asyncio.Future()  # Run forever
            break # Break out of the loop if successful
        except OSError as e:
            if e.errno == 98:  # Address already in use
                logger.warning(f"Port {current_port} already in use. Trying next port...")
                current_port += 1
                if i == MAX_PORT_RETRIES - 1:
                    logger.error("All retry attempts failed. Could not bind to a port.")
                    raise # Re-raise if all retries fail
            else:
                raise # Re-raise for other OS errors

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Server stopped")