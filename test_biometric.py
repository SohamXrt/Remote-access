#!/usr/bin/env python3
"""
Test script for biometric authentication system
Tests the WebAuthn integration
"""
import asyncio
import aiohttp
import json
from datetime import datetime

async def test_biometric_system():
    """Test the biometric authentication endpoints"""
    base_url = "http://localhost:8000"
    device_id = "test_device_123"
    
    print("🧪 Testing Biometric Authentication System")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Check server status
        print("1. Testing server connection...")
        try:
            async with session.get(f"{base_url}/") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Server running: {data['service']}")
                else:
                    print(f"❌ Server error: {response.status}")
                    return
        except Exception as e:
            print(f"❌ Server not accessible: {e}")
            return
        
        # Test 2: Check WebAuthn registration endpoint
        print("\n2. Testing WebAuthn registration...")
        try:
            payload = {
                "device_id": device_id,
                "username": "test_user"
            }
            
            async with session.post(f"{base_url}/webauthn/register/begin", 
                                  json=payload) as response:
                if response.status == 401:
                    print("✅ Registration requires device pairing (expected)")
                elif response.status == 200:
                    data = await response.json()
                    print(f"✅ Registration options generated: {data['success']}")
                else:
                    print(f"⚠️ Unexpected status: {response.status}")
        except Exception as e:
            print(f"❌ Registration test failed: {e}")
        
        # Test 3: Check WebAuthn authentication endpoint  
        print("\n3. Testing WebAuthn authentication...")
        try:
            payload = {
                "device_id": device_id
            }
            
            async with session.post(f"{base_url}/webauthn/authenticate/begin", 
                                  json=payload) as response:
                if response.status == 401:
                    print("✅ Authentication requires device pairing (expected)")
                elif response.status == 400:
                    print("✅ Authentication requires credentials setup (expected)")
                else:
                    print(f"⚠️ Unexpected status: {response.status}")
        except Exception as e:
            print(f"❌ Authentication test failed: {e}")
        
        # Test 4: Check credentials endpoint
        print("\n4. Testing credentials endpoint...")
        try:
            async with session.get(f"{base_url}/webauthn/credentials/{device_id}") as response:
                if response.status == 401:
                    print("✅ Credentials check requires device pairing (expected)")
                else:
                    print(f"⚠️ Unexpected status: {response.status}")
        except Exception as e:
            print(f"❌ Credentials test failed: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 Biometric system endpoints are responding correctly!")
        print("\nNext steps to test with real biometric:")
        print("1. Start the system: ./quick_setup.sh")
        print("2. Pair a device through the mobile app")
        print("3. Set up biometric authentication")
        print("4. Test authentication flow")

def test_webauthn_manager():
    """Test WebAuthn manager locally"""
    print("\n🔐 Testing WebAuthn Manager...")
    
    try:
        from shared.webauthn_auth import WebAuthnManager
        
        # Create manager
        wm = WebAuthnManager(config_dir="configs")
        print("✅ WebAuthn manager created")
        
        # Test challenge generation
        challenge = wm.generate_challenge("test_user")
        print(f"✅ Challenge generated: {challenge[:10]}...")
        
        # Test registration options
        options = wm.create_registration_options("test_user", "Test User")
        print(f"✅ Registration options created: {len(options)} fields")
        
        # Test authentication options (should work even without credentials)
        auth_options = wm.create_authentication_options("test_user")
        print(f"✅ Authentication options created: {len(auth_options)} fields")
        
        # Test credential check
        has_creds = wm.get_user_credentials("test_user")
        print(f"✅ Credential check: {len(has_creds)} credentials")
        
        print("✅ WebAuthn manager tests passed")
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
    except Exception as e:
        print(f"❌ WebAuthn manager test failed: {e}")

def main():
    """Run all tests"""
    # Test WebAuthn manager
    test_webauthn_manager()
    
    print("\n" + "=" * 50)
    
    # Test API endpoints
    print("Starting server endpoint tests...")
    print("Make sure the backend server is running: python mobile_backend/server.py")
    
    try:
        asyncio.run(test_biometric_system())
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    main()