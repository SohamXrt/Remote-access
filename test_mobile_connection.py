#!/usr/bin/env python3
"""
Test mobile connection to cloud relay
"""
import asyncio
import websockets
import json

async def test_mobile_connection():
    try:
        print("🔄 Testing mobile connection to cloud relay...")
        
        # Connect to cloud relay
        websocket = await websockets.connect("ws://localhost:8765")
        print("✅ Connected to cloud relay!")
        
        # Register as mobile device
        await websocket.send(json.dumps({
            "type": "register",
            "device_id": "test_mobile_123",
            "device_type": "mobile", 
            "device_name": "Test Mobile"
        }))
        
        # Wait for registration response
        response = await websocket.recv()
        data = json.loads(response)
        print(f"📱 Registration response: {data}")
        
        # Send a pairing request with test code
        print("🔄 Testing pairing request with code 123456...")
        await websocket.send(json.dumps({
            "type": "pair_request",
            "pairing_code": "123456",
            "device_name": "Test Mobile"
        }))
        
        # Wait for response
        response = await websocket.recv()
        data = json.loads(response)
        print(f"📝 Pairing response: {data}")
        
        await websocket.close()
        print("✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_mobile_connection())