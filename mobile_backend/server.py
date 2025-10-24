#!/usr/bin/env python3
"""
FastAPI backend server for mobile app communication
Handles device pairing, biometric authentication, and remote system control
"""
import os
import sys
import asyncio
import json
import psutil
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import shutil

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uvicorn

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.crypto_utils import CryptoManager
from shared.webauthn_auth import WebAuthnManager
from cryptography.hazmat.primitives import serialization

# Data models
class PairDeviceRequest(BaseModel):
    pairing_code: str
    device_id: str
    device_name: str
    public_key: str

class AuthRequest(BaseModel):
    device_id: str
    request_type: str = "biometric_auth"
    message: Optional[str] = None

class AuthResponse(BaseModel):
    device_id: str
    success: bool
    biometric_verified: bool = False
    timestamp: datetime

class RemoteCommand(BaseModel):
    device_id: str
    command: str  # lock, unlock, sleep, shutdown, restart
    parameters: Optional[Dict] = None

class FileOperation(BaseModel):
    device_id: str
    operation: str  # list, copy, delete, move
    path: str
    destination: Optional[str] = None

class SystemStatus(BaseModel):
    device_id: str
    status: str
    battery_level: Optional[int] = None
    network_status: str
    last_seen: datetime

class WebAuthnRegistrationRequest(BaseModel):
    device_id: str
    username: str

class WebAuthnAuthenticationRequest(BaseModel):
    device_id: str

class WebAuthnCredentialResponse(BaseModel):
    device_id: str
    challenge: str
    credential_data: Dict

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket, device_id: str):
        await websocket.accept()
        self.active_connections[device_id] = websocket
        
    def disconnect(self, device_id: str):
        if device_id in self.active_connections:
            del self.active_connections[device_id]
            
    async def send_personal_message(self, message: str, device_id: str):
        if device_id in self.active_connections:
            await self.active_connections[device_id].send_text(message)
            
    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)

# Global variables
crypto_manager = CryptoManager(config_dir="../configs")
webauthn_manager = WebAuthnManager(config_dir="../configs")
connection_manager = ConnectionManager()
pending_auth_requests = {}  # Store pending authentication requests
valid_pairing_codes = set()  # Store valid pairing codes

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Mobile Backend Server Starting...")
    print(f"Device ID: {crypto_manager.device_id}")
    yield
    # Shutdown
    print("🛑 Mobile Backend Server Shutting Down...")

app = FastAPI(
    title="Laptop Remote Access API",
    description="Backend API for secure laptop remote access with biometric authentication",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for mobile app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual mobile app origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication dependency
def verify_device(device_id: str) -> bool:
    return crypto_manager.is_device_paired(device_id)

@app.get("/")
async def root():
    return {
        "service": "Laptop Remote Access API",
        "status": "running",
        "device_id": crypto_manager.device_id,
        "timestamp": datetime.now()
    }

@app.post("/generate-pairing-code")
async def generate_pairing_code():
    """Generate a new valid pairing code"""
    pairing_code = crypto_manager.generate_pairing_code()
    valid_pairing_codes.add(pairing_code)
    
    # Expire old codes (keep only last 5)
    if len(valid_pairing_codes) > 5:
        # Convert to list, sort, and keep only recent ones
        codes_list = sorted(valid_pairing_codes)
        valid_pairing_codes.clear()
        valid_pairing_codes.update(codes_list[-5:])
    
    return {
        "pairing_code": pairing_code,
        "device_id": crypto_manager.device_id,
        "expires_in": 300  # 5 minutes
    }

@app.post("/pair-device")
async def pair_device(request: PairDeviceRequest):
    """Pair a new mobile device with the laptop"""
    try:
        # Validate pairing code format
        if len(request.pairing_code) != 6 or not request.pairing_code.isdigit():
            raise HTTPException(status_code=400, detail="Invalid pairing code format")
        
        # Validate pairing code against generated codes
        if request.pairing_code not in valid_pairing_codes:
            raise HTTPException(status_code=401, detail="Invalid or expired pairing code")
        
        # Remove used pairing code
        valid_pairing_codes.discard(request.pairing_code)
        
        # Save paired device
        crypto_manager.save_paired_device(
            request.device_id,
            request.device_name,
            request.public_key
        )
        
        # Generate session key for this device
        session_key = crypto_manager.generate_session_key()
        
        return {
            "success": True,
            "message": "Device paired successfully",
            "laptop_device_id": crypto_manager.device_id,
            "laptop_public_key": crypto_manager.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode(),
            "session_key": session_key.decode()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pairing failed: {str(e)}")

@app.websocket("/ws/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: str):
    """WebSocket connection for real-time communication"""
    if not verify_device(device_id):
        await websocket.close(code=4001, reason="Device not paired")
        return
        
    await connection_manager.connect(websocket, device_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "auth_response":
                # Handle biometric authentication response
                auth_response = AuthResponse(
                    device_id=device_id,
                    success=message.get("success", False),
                    biometric_verified=message.get("biometric_verified", False),
                    timestamp=datetime.now()
                )
                
                # Store response for terminal to check
                pending_auth_requests[device_id] = auth_response
                
                await websocket.send_text(json.dumps({
                    "type": "auth_ack",
                    "message": "Authentication response received"
                }))
                
    except WebSocketDisconnect:
        connection_manager.disconnect(device_id)

@app.post("/auth-request")
async def request_authentication(request: AuthRequest):
    """Request biometric authentication from mobile device"""
    if not verify_device(request.device_id):
        raise HTTPException(status_code=401, detail="Device not paired")
    
    # Send authentication request via WebSocket
    message = {
        "type": "auth_request",
        "request_type": request.request_type,
        "message": request.message or "Biometric authentication required",
        "timestamp": datetime.now().isoformat()
    }
    
    await connection_manager.send_personal_message(
        json.dumps(message), 
        request.device_id
    )
    
    return {
        "success": True,
        "message": "Authentication request sent to mobile device"
    }

@app.get("/auth-status/{device_id}")
async def get_auth_status(device_id: str):
    """Check authentication status"""
    if not verify_device(device_id):
        raise HTTPException(status_code=401, detail="Device not paired")
    
    if device_id in pending_auth_requests:
        response = pending_auth_requests[device_id]
        # Clear the request once retrieved
        del pending_auth_requests[device_id]
        return response.dict()
    
    return {"status": "pending", "message": "No authentication response yet"}

@app.post("/remote-command")
async def execute_remote_command(command: RemoteCommand):
    """Execute remote system commands"""
    if not verify_device(command.device_id):
        raise HTTPException(status_code=401, detail="Device not paired")
    
    try:
        if command.command == "lock":
            # Lock the screen
            subprocess.run(["gnome-screensaver-command", "--lock"], check=True)
            message = "System locked successfully"
            
        elif command.command == "unlock":
            # Unlock would be handled by the authentication terminal
            message = "Unlock request sent to authentication terminal"
            
        elif command.command == "sleep":
            subprocess.run(["systemctl", "suspend"], check=True)
            message = "System suspended"
            
        elif command.command == "shutdown":
            subprocess.run(["shutdown", "-h", "now"], check=True)
            message = "System shutdown initiated"
            
        elif command.command == "restart":
            subprocess.run(["shutdown", "-r", "now"], check=True)
            message = "System restart initiated"
            
        else:
            raise HTTPException(status_code=400, detail="Unknown command")
        
        return {
            "success": True,
            "command": command.command,
            "message": message,
            "timestamp": datetime.now()
        }
        
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Command failed: {str(e)}")

@app.get("/system-status")
async def get_system_status():
    """Get current system status"""
    try:
        # Get system information
        battery = None
        try:
            battery_info = psutil.sensors_battery()
            if battery_info:
                battery = int(battery_info.percent)
        except:
            pass
        
        # Get network status
        network_status = "connected" if any(
            addr.family.name == 'AF_INET' and not addr.address.startswith('127.')
            for interface in psutil.net_if_addrs().values()
            for addr in interface
        ) else "disconnected"
        
        return SystemStatus(
            device_id=crypto_manager.device_id,
            status="online",
            battery_level=battery,
            network_status=network_status,
            last_seen=datetime.now()
        ).dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")

@app.post("/file-operation")
async def handle_file_operation(operation: FileOperation):
    """Handle file operations (list, copy, delete, move)"""
    if not verify_device(operation.device_id):
        raise HTTPException(status_code=401, detail="Device not paired")
    
    try:
        path = Path(operation.path).expanduser().resolve()
        
        if operation.operation == "list":
            if not path.exists():
                raise HTTPException(status_code=404, detail="Path not found")
            
            if path.is_file():
                return {
                    "type": "file",
                    "name": path.name,
                    "size": path.stat().st_size,
                    "modified": datetime.fromtimestamp(path.stat().st_mtime),
                    "path": str(path)
                }
            
            elif path.is_dir():
                items = []
                for item in path.iterdir():
                    try:
                        stat = item.stat()
                        items.append({
                            "type": "directory" if item.is_dir() else "file",
                            "name": item.name,
                            "size": stat.st_size if item.is_file() else None,
                            "modified": datetime.fromtimestamp(stat.st_mtime),
                            "path": str(item)
                        })
                    except PermissionError:
                        continue  # Skip files we can't access
                
                return {
                    "type": "directory",
                    "path": str(path),
                    "items": sorted(items, key=lambda x: (x["type"] == "file", x["name"].lower()))
                }
        
        elif operation.operation == "copy":
            if not operation.destination:
                raise HTTPException(status_code=400, detail="Destination required for copy")
            
            dest_path = Path(operation.destination).expanduser().resolve()
            
            if path.is_file():
                shutil.copy2(path, dest_path)
            else:
                shutil.copytree(path, dest_path)
            
            return {
                "success": True,
                "message": f"Copied {path} to {dest_path}",
                "operation": "copy"
            }
        
        elif operation.operation == "delete":
            if path.is_file():
                path.unlink()
            else:
                shutil.rmtree(path)
            
            return {
                "success": True,
                "message": f"Deleted {path}",
                "operation": "delete"
            }
        
        elif operation.operation == "move":
            if not operation.destination:
                raise HTTPException(status_code=400, detail="Destination required for move")
            
            dest_path = Path(operation.destination).expanduser().resolve()
            shutil.move(path, dest_path)
            
            return {
                "success": True,
                "message": f"Moved {path} to {dest_path}",
                "operation": "move"
            }
        
        else:
            raise HTTPException(status_code=400, detail="Unknown file operation")
            
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File or directory not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File operation failed: {str(e)}")

@app.get("/paired-devices")
async def get_paired_devices():
    """Get list of paired devices"""
    paired_devices = crypto_manager.load_paired_devices()
    return {
        "devices": paired_devices,
        "count": len(paired_devices)
    }

@app.delete("/unpair-device/{device_id}")
async def unpair_device(device_id: str):
    """Unpair a device"""
    success = crypto_manager.unpair_device(device_id)
    
    if success:
        # Disconnect WebSocket if active
        connection_manager.disconnect(device_id)
        # Also clear WebAuthn credentials
        webauthn_manager.clear_user_credentials(device_id)
        return {"success": True, "message": "Device unpaired successfully"}
    else:
        raise HTTPException(status_code=404, detail="Device not found")

# WebAuthn Biometric Authentication Endpoints

@app.post("/webauthn/register/begin")
async def webauthn_register_begin(request: WebAuthnRegistrationRequest):
    """Begin WebAuthn credential registration (biometric setup)"""
    if not verify_device(request.device_id):
        raise HTTPException(status_code=401, detail="Device not paired")
    
    try:
        options = webauthn_manager.create_registration_options(
            request.device_id, 
            request.username
        )
        return {
            "success": True,
            "options": options
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration setup failed: {str(e)}")

@app.post("/webauthn/register/complete")
async def webauthn_register_complete(response: WebAuthnCredentialResponse):
    """Complete WebAuthn credential registration"""
    if not verify_device(response.device_id):
        raise HTTPException(status_code=401, detail="Device not paired")
    
    try:
        # Get username from paired devices
        paired_devices = crypto_manager.load_paired_devices()
        username = paired_devices.get(response.device_id, {}).get('name', 'Unknown')
        
        success = webauthn_manager.register_credential(
            response.device_id,
            username,
            response.credential_data
        )
        
        if success:
            return {
                "success": True,
                "message": "Biometric credential registered successfully"
            }
        else:
            raise HTTPException(status_code=400, detail="Registration failed")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/webauthn/authenticate/begin")
async def webauthn_authenticate_begin(request: WebAuthnAuthenticationRequest):
    """Begin WebAuthn authentication (biometric login)"""
    if not verify_device(request.device_id):
        raise HTTPException(status_code=401, detail="Device not paired")
    
    try:
        # Check if user has registered credentials
        user_creds = webauthn_manager.get_user_credentials(request.device_id)
        if not user_creds.get('credentials'):
            raise HTTPException(status_code=400, detail="No biometric credentials registered")
        
        options = webauthn_manager.create_authentication_options(request.device_id)
        return {
            "success": True,
            "options": options
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication setup failed: {str(e)}")

@app.post("/webauthn/authenticate/complete")
async def webauthn_authenticate_complete(response: WebAuthnCredentialResponse):
    """Complete WebAuthn authentication"""
    if not verify_device(response.device_id):
        raise HTTPException(status_code=401, detail="Device not paired")
    
    try:
        success = webauthn_manager.verify_authentication(
            response.device_id,
            response.credential_data
        )
        
        if success:
            # Store successful authentication for terminal to check
            auth_response = AuthResponse(
                device_id=response.device_id,
                success=True,
                biometric_verified=True,
                timestamp=datetime.now()
            )
            pending_auth_requests[response.device_id] = auth_response
            
            return {
                "success": True,
                "message": "Biometric authentication successful",
                "verified": True
            }
        else:
            return {
                "success": False,
                "message": "Biometric authentication failed",
                "verified": False
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@app.get("/webauthn/credentials/{device_id}")
async def get_webauthn_credentials(device_id: str):
    """Get registered WebAuthn credentials for a device"""
    if not verify_device(device_id):
        raise HTTPException(status_code=401, detail="Device not paired")
    
    credentials = webauthn_manager.get_user_credentials(device_id)
    return {
        "device_id": device_id,
        "has_credentials": bool(credentials.get('credentials')),
        "credential_count": len(credentials.get('credentials', [])),
        "registered_at": credentials.get('registered_at'),
        "username": credentials.get('username')
    }

@app.delete("/webauthn/credentials/{device_id}")
async def clear_webauthn_credentials(device_id: str):
    """Clear all WebAuthn credentials for a device"""
    if not verify_device(device_id):
        raise HTTPException(status_code=401, detail="Device not paired")
    
    success = webauthn_manager.clear_user_credentials(device_id)
    if success:
        return {"success": True, "message": "Biometric credentials cleared"}
    else:
        raise HTTPException(status_code=404, detail="No credentials found")

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )