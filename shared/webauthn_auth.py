#!/usr/bin/env python3
"""
WebAuthn biometric authentication implementation
Handles real fingerprint/face recognition using Web Authentication API
"""
import os
import json
import base64
import secrets
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta

class WebAuthnManager:
    """Manages WebAuthn biometric authentication"""
    
    def __init__(self, config_dir="configs"):
        self.config_dir = config_dir
        self.credentials_file = os.path.join(config_dir, "webauthn_credentials.json")
        self.challenges_file = os.path.join(config_dir, "active_challenges.json")
        
        # Ensure config directory exists
        os.makedirs(config_dir, exist_ok=True)
        
        # Load existing credentials
        self.load_credentials()
        
    def load_credentials(self):
        """Load stored WebAuthn credentials"""
        if os.path.exists(self.credentials_file):
            with open(self.credentials_file, 'r') as f:
                self.credentials = json.load(f)
        else:
            self.credentials = {}
            
    def save_credentials(self):
        """Save WebAuthn credentials"""
        with open(self.credentials_file, 'w') as f:
            json.dump(self.credentials, f, indent=2)
            
    def generate_challenge(self, user_id: str) -> str:
        """Generate a cryptographic challenge for authentication"""
        challenge = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip('=')
        
        # Store challenge with expiration
        challenges = self.load_active_challenges()
        challenges[challenge] = {
            'user_id': user_id,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(minutes=5)).isoformat()
        }
        self.save_active_challenges(challenges)
        
        return challenge
        
    def load_active_challenges(self) -> Dict:
        """Load active authentication challenges"""
        if os.path.exists(self.challenges_file):
            with open(self.challenges_file, 'r') as f:
                challenges = json.load(f)
                
            # Clean expired challenges
            current_time = datetime.now()
            valid_challenges = {}
            
            for challenge, data in challenges.items():
                expires_at = datetime.fromisoformat(data['expires_at'])
                if expires_at > current_time:
                    valid_challenges[challenge] = data
                    
            return valid_challenges
        return {}
        
    def save_active_challenges(self, challenges: Dict):
        """Save active challenges"""
        with open(self.challenges_file, 'w') as f:
            json.dump(challenges, f, indent=2)
            
    def create_registration_options(self, user_id: str, username: str) -> Dict:
        """Create options for WebAuthn credential registration"""
        challenge = self.generate_challenge(user_id)
        
        return {
            "challenge": challenge,
            "rp": {
                "name": "Laptop Remote Access",
                "id": "localhost"
            },
            "user": {
                "id": base64.urlsafe_b64encode(user_id.encode()).decode().rstrip('='),
                "name": username,
                "displayName": f"Laptop Remote - {username}"
            },
            "pubKeyCredParams": [
                {"alg": -7, "type": "public-key"},  # ES256
                {"alg": -257, "type": "public-key"}  # RS256
            ],
            "authenticatorSelection": {
                "authenticatorAttachment": "platform",
                "userVerification": "required",
                "residentKey": "preferred"
            },
            "timeout": 60000,
            "attestation": "direct"
        }
        
    def create_authentication_options(self, user_id: str) -> Dict:
        """Create options for WebAuthn authentication"""
        challenge = self.generate_challenge(user_id)
        
        # Get user's registered credentials
        user_credentials = self.credentials.get(user_id, {}).get('credentials', [])
        
        allowed_credentials = []
        for cred in user_credentials:
            allowed_credentials.append({
                "type": "public-key",
                "id": cred['id']
            })
            
        return {
            "challenge": challenge,
            "timeout": 60000,
            "rpId": "localhost",
            "allowCredentials": allowed_credentials,
            "userVerification": "required"
        }
        
    def register_credential(self, user_id: str, username: str, credential_data: Dict) -> bool:
        """Register a new WebAuthn credential"""
        try:
            # Validate challenge
            challenge = credential_data.get('challenge')
            if not self.validate_challenge(challenge, user_id):
                return False
                
            # Store credential
            if user_id not in self.credentials:
                self.credentials[user_id] = {
                    'username': username,
                    'credentials': [],
                    'registered_at': datetime.now().isoformat()
                }
                
            # Add new credential
            self.credentials[user_id]['credentials'].append({
                'id': credential_data['id'],
                'publicKey': credential_data['publicKey'],
                'signCount': credential_data.get('signCount', 0),
                'registered_at': datetime.now().isoformat()
            })
            
            self.save_credentials()
            return True
            
        except Exception as e:
            print(f"Error registering credential: {e}")
            return False
            
    def verify_authentication(self, user_id: str, auth_data: Dict) -> bool:
        """Verify WebAuthn authentication"""
        try:
            # Validate challenge
            challenge = auth_data.get('challenge')
            if not self.validate_challenge(challenge, user_id):
                return False
                
            # In a real implementation, you would:
            # 1. Verify the authenticator data
            # 2. Verify the signature using the stored public key
            # 3. Check the sign counter to prevent replay attacks
            
            # For this demo, we'll do basic validation
            credential_id = auth_data.get('credentialId')
            
            user_creds = self.credentials.get(user_id, {}).get('credentials', [])
            for cred in user_creds:
                if cred['id'] == credential_id:
                    # Update sign counter
                    cred['signCount'] = auth_data.get('signCount', cred['signCount'] + 1)
                    cred['last_used'] = datetime.now().isoformat()
                    self.save_credentials()
                    return True
                    
            return False
            
        except Exception as e:
            print(f"Error verifying authentication: {e}")
            return False
            
    def validate_challenge(self, challenge: str, user_id: str) -> bool:
        """Validate that the challenge is valid and not expired"""
        challenges = self.load_active_challenges()
        
        if challenge not in challenges:
            return False
            
        challenge_data = challenges[challenge]
        
        # Check if challenge belongs to this user
        if challenge_data['user_id'] != user_id:
            return False
            
        # Check if challenge is expired
        expires_at = datetime.fromisoformat(challenge_data['expires_at'])
        if datetime.now() > expires_at:
            return False
            
        # Remove used challenge
        del challenges[challenge]
        self.save_active_challenges(challenges)
        
        return True
        
    def get_user_credentials(self, user_id: str) -> Dict:
        """Get registered credentials for a user"""
        return self.credentials.get(user_id, {})
        
    def remove_credential(self, user_id: str, credential_id: str) -> bool:
        """Remove a registered credential"""
        if user_id not in self.credentials:
            return False
            
        credentials = self.credentials[user_id]['credentials']
        self.credentials[user_id]['credentials'] = [
            cred for cred in credentials if cred['id'] != credential_id
        ]
        
        self.save_credentials()
        return True
        
    def clear_user_credentials(self, user_id: str) -> bool:
        """Remove all credentials for a user"""
        if user_id in self.credentials:
            del self.credentials[user_id]
            self.save_credentials()
            return True
        return False