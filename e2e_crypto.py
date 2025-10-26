#!/usr/bin/env python3
"""
End-to-End Encryption Module
Uses AES-256 with a shared secret derived from pairing code
"""
import json
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os

class E2EEncryption:
    def __init__(self, shared_secret: str):
        """
        Initialize encryption with shared secret (derived from pairing code)
        """
        # Derive a 256-bit key from the shared secret
        salt = b'laptop_remote_salt_v1'  # Static salt for simplicity
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        self.key = kdf.derive(shared_secret.encode())
    
    def encrypt_message(self, plaintext: dict) -> str:
        """
        Encrypt a message dictionary
        Returns base64 encoded encrypted data
        """
        # Convert dict to JSON string
        plaintext_bytes = json.dumps(plaintext).encode('utf-8')
        
        # Generate random IV (Initialization Vector)
        iv = os.urandom(16)
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Pad plaintext to multiple of 16 bytes
        padding_length = 16 - (len(plaintext_bytes) % 16)
        padded_plaintext = plaintext_bytes + (bytes([padding_length]) * padding_length)
        
        # Encrypt
        ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()
        
        # Combine IV + ciphertext and encode
        encrypted_data = iv + ciphertext
        return base64.b64encode(encrypted_data).decode('utf-8')
    
    def decrypt_message(self, encrypted_b64: str) -> dict:
        """
        Decrypt a base64 encoded encrypted message
        Returns original message dictionary
        """
        # Decode base64
        encrypted_data = base64.b64decode(encrypted_b64)
        
        # Extract IV and ciphertext
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # Decrypt
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Remove padding
        padding_length = padded_plaintext[-1]
        plaintext_bytes = padded_plaintext[:-padding_length]
        
        # Convert back to dict
        return json.loads(plaintext_bytes.decode('utf-8'))

# Example usage
if __name__ == "__main__":
    # Test encryption
    secret = "test_pairing_code_123456"
    e2e = E2EEncryption(secret)
    
    # Encrypt
    message = {"type": "system_command", "command": "sleep"}
    encrypted = e2e.encrypt_message(message)
    print(f"Encrypted: {encrypted}")
    
    # Decrypt
    decrypted = e2e.decrypt_message(encrypted)
    print(f"Decrypted: {decrypted}")
    print(f"Match: {message == decrypted}")
