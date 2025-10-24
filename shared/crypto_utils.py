"""
Cryptographic utilities for secure device pairing and communication
"""
import secrets
import hashlib
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import json
import os
import time

class CryptoManager:
    def __init__(self, config_dir="configs"):
        self.config_dir = config_dir
        self.keys_file = os.path.join(config_dir, "device_keys.json")
        self.paired_devices_file = os.path.join(config_dir, "paired_devices.json")
        
        # Ensure config directory exists
        os.makedirs(config_dir, exist_ok=True)
        
        # Load or generate device keys
        self.load_or_generate_keys()
    
    def load_or_generate_keys(self):
        """Load existing keys or generate new ones"""
        if os.path.exists(self.keys_file):
            with open(self.keys_file, 'r') as f:
                key_data = json.load(f)
                
            # Load private key
            private_key_pem = key_data['private_key'].encode()
            self.private_key = serialization.load_pem_private_key(
                private_key_pem, password=None
            )
            
            # Load public key
            public_key_pem = key_data['public_key'].encode()
            self.public_key = serialization.load_pem_public_key(public_key_pem)
            
            # Load device ID
            self.device_id = key_data['device_id']
        else:
            # Generate new keys
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            self.public_key = self.private_key.public_key()
            self.device_id = secrets.token_hex(16)
            
            # Save keys
            private_pem = self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            public_pem = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            key_data = {
                'device_id': self.device_id,
                'private_key': private_pem.decode(),
                'public_key': public_pem.decode()
            }
            
            with open(self.keys_file, 'w') as f:
                json.dump(key_data, f, indent=2)
    
    def generate_pairing_code(self):
        """Generate a 6-digit pairing code"""
        return f"{secrets.randbelow(1000000):06d}"
    
    def generate_session_key(self):
        """Generate a symmetric session key for encrypted communication"""
        return Fernet.generate_key()
    
    def encrypt_message(self, message, key):
        """Encrypt message using Fernet symmetric encryption"""
        f = Fernet(key)
        return f.encrypt(message.encode()).decode()
    
    def decrypt_message(self, encrypted_message, key):
        """Decrypt message using Fernet symmetric encryption"""
        f = Fernet(key)
        return f.decrypt(encrypted_message.encode()).decode()
    
    def encrypt_with_public_key(self, message, public_key_pem):
        """Encrypt message with RSA public key"""
        public_key = serialization.load_pem_public_key(public_key_pem.encode())
        encrypted = public_key.encrypt(
            message.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return base64.b64encode(encrypted).decode()
    
    def decrypt_with_private_key(self, encrypted_message):
        """Decrypt message with RSA private key"""
        encrypted_bytes = base64.b64decode(encrypted_message.encode())
        decrypted = self.private_key.decrypt(
            encrypted_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted.decode()
    
    def save_paired_device(self, device_id, device_name, public_key_pem):
        """Save a paired device's information"""
        paired_devices = self.load_paired_devices()
        paired_devices[device_id] = {
            'name': device_name,
            'public_key': public_key_pem,
            'paired_at': time.time()
        }
        
        with open(self.paired_devices_file, 'w') as f:
            json.dump(paired_devices, f, indent=2)
    
    def load_paired_devices(self):
        """Load paired devices"""
        if os.path.exists(self.paired_devices_file):
            with open(self.paired_devices_file, 'r') as f:
                return json.load(f)
        return {}
    
    def is_device_paired(self, device_id):
        """Check if device is paired"""
        paired_devices = self.load_paired_devices()
        return device_id in paired_devices
    
    def get_device_public_key(self, device_id):
        """Get public key for a paired device"""
        paired_devices = self.load_paired_devices()
        if device_id in paired_devices:
            return paired_devices[device_id]['public_key']
        return None

    def unpair_device(self, device_id):
        """Remove a paired device"""
        paired_devices = self.load_paired_devices()
        if device_id in paired_devices:
            del paired_devices[device_id]
            with open(self.paired_devices_file, 'w') as f:
                json.dump(paired_devices, f, indent=2)
            return True
        return False