#!/usr/bin/env python3
"""
Quick WebSocket connection test
"""
import asyncio
import websockets
import json
import sys

async def test_connection(host='172.18.20.200', port=8765):
    url = f'ws://{host}:{port}'
    print(f"🔍 Testing connection to {url}...")
    
    try:
        async with websockets.connect(url) as ws:
            print("✅ Connected successfully!")
            
            # Test registration
            test_device = {
                'type': 'register',
                'device_id': 'test_device_123',
                'device_type': 'mobile',
                'device_name': 'Test Mobile'
            }
            
            print(f"📤 Sending: {test_device}")
            await ws.send(json.dumps(test_device))
            
            # Wait for response
            response = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(response)
            print(f"📥 Received: {data}")
            
            if data.get('type') == 'registered':
                print("✅ Registration successful!")
                print(f"   Device ID: {data.get('device_id')}")
                print(f"   Known device: {data.get('is_known_device')}")
                return True
            else:
                print(f"❌ Unexpected response: {data}")
                return False
                
    except asyncio.TimeoutError:
        print("❌ Timeout waiting for response")
        return False
    except ConnectionRefusedError:
        print("❌ Connection refused - is the server running?")
        return False
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        return False

if __name__ == '__main__':
    host = sys.argv[1] if len(sys.argv) > 1 else '172.18.20.200'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8765
    
    result = asyncio.run(test_connection(host, port))
    sys.exit(0 if result else 1)
