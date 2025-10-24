#!/usr/bin/env python3
"""
Test script to verify the laptop remote access system functionality
"""
import os
import sys
import time
import requests
import subprocess
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    try:
        from shared.crypto_utils import CryptoManager
        from terminal_client.auth_terminal import HackerTerminal
        from terminal_client.auth_client import AuthenticationClient
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_crypto_manager():
    """Test cryptographic utilities"""
    print("\n🔐 Testing crypto manager...")
    try:
        from shared.crypto_utils import CryptoManager
        
        # Create crypto manager
        cm = CryptoManager(config_dir="configs")
        
        # Test key generation
        assert cm.device_id is not None
        assert cm.private_key is not None
        assert cm.public_key is not None
        
        # Test pairing code generation
        code = cm.generate_pairing_code()
        assert len(code) == 6 and code.isdigit()
        
        # Test encryption/decryption
        session_key = cm.generate_session_key()
        message = "Hello, World!"
        encrypted = cm.encrypt_message(message, session_key)
        decrypted = cm.decrypt_message(encrypted, session_key)
        assert decrypted == message
        
        print("✅ Crypto manager tests passed")
        return True
    except Exception as e:
        print(f"❌ Crypto manager test failed: {e}")
        return False

def test_terminal_interface():
    """Test terminal interface creation"""
    print("\n🖥️ Testing terminal interface...")
    try:
        from terminal_client.auth_terminal import HackerTerminal
        
        terminal = HackerTerminal()
        assert terminal.console is not None
        assert terminal.crypto_manager is not None
        
        print("✅ Terminal interface tests passed")
        return True
    except Exception as e:
        print(f"❌ Terminal interface test failed: {e}")
        return False

def test_backend_server():
    """Test if backend server can be started"""
    print("\n🚀 Testing backend server...")
    try:
        # Start server in background
        server_process = subprocess.Popen([
            "python", "mobile_backend/server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        time.sleep(3)
        
        # Test server connection
        try:
            response = requests.get("http://localhost:8000/", timeout=5)
            if response.status_code == 200:
                print("✅ Backend server started successfully")
                server_process.terminate()
                server_process.wait()
                return True
        except requests.RequestException:
            pass
        
        server_process.terminate()
        server_process.wait()
        print("❌ Backend server failed to start or respond")
        return False
        
    except Exception as e:
        print(f"❌ Backend server test failed: {e}")
        return False

def test_file_structure():
    """Test if all required files exist"""
    print("\n📁 Testing file structure...")
    
    required_files = [
        "shared/crypto_utils.py",
        "terminal_client/auth_terminal.py",
        "terminal_client/auth_client.py",
        "mobile_backend/server.py",
        "mobile_app_mockup/index.html",
        "README.md"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
        return True

def test_mobile_app():
    """Test mobile app mockup"""
    print("\n📱 Testing mobile app mockup...")
    try:
        mobile_app_path = Path("mobile_app_mockup/index.html")
        if mobile_app_path.exists():
            content = mobile_app_path.read_text()
            
            # Check for key elements
            assert "Laptop Remote Access" in content
            assert "Biometric authentication" in content
            assert "System Controls" in content
            assert "File Browser" in content
            
            print("✅ Mobile app mockup tests passed")
            return True
        else:
            print("❌ Mobile app mockup not found")
            return False
    except Exception as e:
        print(f"❌ Mobile app test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🔒 Laptop Remote Access System - Test Suite")
    print("=" * 50)
    
    tests = [
        test_file_structure,
        test_imports,
        test_crypto_manager,
        test_terminal_interface,
        test_mobile_app,
        test_backend_server
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        if test_func():
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Start the backend server: python mobile_backend/server.py")
        print("2. Run the terminal client: python terminal_client/auth_client.py --demo")
        print("3. Open mobile app: python -m http.server 8080 (in mobile_app_mockup/)")
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)