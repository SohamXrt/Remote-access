// WebAuthn Biometric Authentication Module
// Handles real fingerprint/face recognition using Web Authentication API

class BiometricAuth {
    constructor(serverUrl, deviceId) {
        this.serverUrl = serverUrl;
        this.deviceId = deviceId;
        this.isSupported = this.checkSupport();
    }
    
    // Check if WebAuthn is supported
    checkSupport() {
        return 'credentials' in navigator && 'create' in navigator.credentials;
    }
    
    // Convert base64url to ArrayBuffer
    base64urlToArrayBuffer(base64url) {
        const padding = '='.repeat((4 - (base64url.length % 4)) % 4);
        const base64 = base64url.replace(/-/g, '+').replace(/_/g, '/') + padding;
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray.buffer;
    }
    
    // Convert ArrayBuffer to base64url
    arrayBufferToBase64url(arrayBuffer) {
        const bytes = new Uint8Array(arrayBuffer);
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        const base64 = window.btoa(binary);
        return base64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
    }
    
    // Register biometric credential (setup)
    async registerBiometric(username) {
        if (!this.isSupported) {
            throw new Error('WebAuthn not supported on this device');
        }
        
        try {
            // Get registration options from server
            const beginResponse = await fetch(`${this.serverUrl}/webauthn/register/begin`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    device_id: this.deviceId,
                    username: username
                })
            });
            
            if (!beginResponse.ok) {
                throw new Error('Failed to initiate biometric registration');
            }
            
            const { options } = await beginResponse.json();
            
            // Convert challenge and user ID from base64url to ArrayBuffer
            options.challenge = this.base64urlToArrayBuffer(options.challenge);
            options.user.id = this.base64urlToArrayBuffer(options.user.id);
            
            // Create credential using platform authenticator (fingerprint/face)
            const credential = await navigator.credentials.create({
                publicKey: options
            });
            
            // Prepare credential data for server
            const credentialData = {
                challenge: options.challenge,
                id: credential.id,
                publicKey: this.arrayBufferToBase64url(credential.response.publicKey),
                signCount: credential.response.signCount || 0,
                credentialId: credential.id
            };
            
            // Send credential to server
            const completeResponse = await fetch(`${this.serverUrl}/webauthn/register/complete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    device_id: this.deviceId,
                    challenge: this.arrayBufferToBase64url(options.challenge),
                    credential_data: credentialData
                })
            });
            
            if (!completeResponse.ok) {
                throw new Error('Failed to complete biometric registration');
            }
            
            const result = await completeResponse.json();
            return result.success;
            
        } catch (error) {
            console.error('Biometric registration failed:', error);
            
            // Handle specific WebAuthn errors
            if (error.name === 'NotSupportedError') {
                throw new Error('Biometric authentication not supported on this device');
            } else if (error.name === 'SecurityError') {
                throw new Error('Security error: Please use HTTPS or localhost');
            } else if (error.name === 'NotAllowedError') {
                throw new Error('Biometric authentication was cancelled or not allowed');
            } else if (error.name === 'InvalidStateError') {
                throw new Error('Biometric credential already exists');
            }
            
            throw error;
        }
    }
    
    // Authenticate using biometric
    async authenticateBiometric() {
        if (!this.isSupported) {
            throw new Error('WebAuthn not supported on this device');
        }
        
        try {
            // Get authentication options from server
            const beginResponse = await fetch(`${this.serverUrl}/webauthn/authenticate/begin`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    device_id: this.deviceId
                })
            });
            
            if (!beginResponse.ok) {
                const error = await beginResponse.json();
                if (beginResponse.status === 400 && error.detail.includes('No biometric credentials')) {
                    throw new Error('NO_CREDENTIALS');
                }
                throw new Error('Failed to initiate biometric authentication');
            }
            
            const { options } = await beginResponse.json();
            
            // Convert challenge from base64url to ArrayBuffer
            options.challenge = this.base64urlToArrayBuffer(options.challenge);
            
            // Convert allowed credentials
            if (options.allowCredentials) {
                options.allowCredentials = options.allowCredentials.map(cred => ({
                    ...cred,
                    id: this.base64urlToArrayBuffer(cred.id)
                }));
            }
            
            // Get credential using platform authenticator
            const credential = await navigator.credentials.get({
                publicKey: options
            });
            
            // Prepare authentication data for server
            const authData = {
                challenge: this.arrayBufferToBase64url(options.challenge),
                credentialId: credential.id,
                authenticatorData: this.arrayBufferToBase64url(credential.response.authenticatorData),
                signature: this.arrayBufferToBase64url(credential.response.signature),
                signCount: credential.response.signCount || 0
            };
            
            // Send authentication to server
            const completeResponse = await fetch(`${this.serverUrl}/webauthn/authenticate/complete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    device_id: this.deviceId,
                    challenge: this.arrayBufferToBase64url(options.challenge),
                    credential_data: authData
                })
            });
            
            if (!completeResponse.ok) {
                throw new Error('Failed to complete biometric authentication');
            }
            
            const result = await completeResponse.json();
            return result.verified;
            
        } catch (error) {
            console.error('Biometric authentication failed:', error);
            
            // Handle specific errors
            if (error.message === 'NO_CREDENTIALS') {
                throw error;
            } else if (error.name === 'NotAllowedError') {
                throw new Error('Biometric authentication was cancelled');
            } else if (error.name === 'SecurityError') {
                throw new Error('Security error: Please use HTTPS or localhost');
            }
            
            throw error;
        }
    }
    
    // Check if user has registered biometric credentials
    async hasCredentials() {
        try {
            const response = await fetch(`${this.serverUrl}/webauthn/credentials/${this.deviceId}`);
            if (!response.ok) return false;
            
            const data = await response.json();
            return data.has_credentials;
        } catch (error) {
            console.error('Failed to check credentials:', error);
            return false;
        }
    }
    
    // Clear biometric credentials
    async clearCredentials() {
        try {
            const response = await fetch(`${this.serverUrl}/webauthn/credentials/${this.deviceId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                throw new Error('Failed to clear credentials');
            }
            
            return true;
        } catch (error) {
            console.error('Failed to clear credentials:', error);
            throw error;
        }
    }
    
    // Get biometric capability info
    async getBiometricCapabilities() {
        if (!this.isSupported) {
            return {
                supported: false,
                reason: 'WebAuthn not supported'
            };
        }
        
        try {
            // Check if platform authenticator is available
            const available = await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();
            
            return {
                supported: true,
                platformAuthenticator: available,
                reason: available ? 'Biometric authentication available' : 'No platform authenticator found'
            };
        } catch (error) {
            return {
                supported: true,
                platformAuthenticator: false,
                reason: 'Unable to detect platform authenticator'
            };
        }
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BiometricAuth;
} else {
    window.BiometricAuth = BiometricAuth;
}