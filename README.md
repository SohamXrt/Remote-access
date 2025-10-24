# 🔒 Laptop Remote Access System

A comprehensive biometric authentication system that allows secure remote access to your Ubuntu laptop using your mobile phone. The system features a hacker-style terminal interface and provides 80-90% of laptop functionality through your mobile device.

## 🚀 Features

### Core Authentication
- **Biometric Authentication**: Secure fingerprint-based login through mobile app
- **Device Pairing**: QR code and PIN-based initial device pairing
- **Secure Communication**: End-to-end encryption using RSA and AES
- **Login Interception**: Seamless integration with Ubuntu login system

### Remote Control Features
- **System Control**: Lock, unlock, sleep, shutdown, restart
- **File Management**: Browse, copy, share, delete files even when laptop is off
- **Real-time Status**: Battery level, network status, connection monitoring
- **Session Management**: Secure session handling and monitoring

### User Interface
- **Hacker Terminal**: Green text on black background with cool effects
- **Mobile App**: Black background with white text for optimal viewing
- **Real-time Updates**: Live status updates and notifications
- **Intuitive Controls**: Easy-to-use mobile interface for all operations

## 📁 Project Structure

```
laptop-remote-access/
├── shared/
│   └── crypto_utils.py          # Cryptographic utilities and device pairing
├── terminal_client/
│   ├── auth_terminal.py         # Hacker-style terminal interface
│   └── auth_client.py           # Authentication client with backend integration
├── mobile_backend/
│   └── server.py                # FastAPI backend server
├── mobile_app_mockup/
│   └── index.html               # Mobile app HTML mockup
├── configs/                     # Configuration and key storage
├── venv/                        # Python virtual environment
└── README.md                    # This file
```

## 🛠️ Setup Instructions

### Prerequisites
- Ubuntu 20.04 or later
- Python 3.8+
- Node.js (for mobile app development)
- Modern web browser (for mobile app mockup)

### Installation

1. **Clone the repository** (or use the existing setup):
   ```bash
   cd ~/laptop-remote-access
   ```

2. **Activate the virtual environment**:
   ```bash
   source venv/bin/activate
   ```

3. **Verify dependencies are installed**:
   ```bash
   pip list | grep -E "(fastapi|uvicorn|cryptography|qrcode|psutil|requests|websockets|rich)"
   ```

### Quick Start

1. **Start the backend server**:
   ```bash
   cd mobile_backend
   python server.py
   ```
   The server will start on `http://localhost:8000`

2. **In a new terminal, run the authentication client**:
   ```bash
   cd terminal_client
   python auth_client.py --demo
   ```

3. **Open the mobile app mockup**:
   ```bash
   cd mobile_app_mockup
   python -m http.server 8080
   ```
   Then open `http://localhost:8080` in your browser

## 🎮 Usage Guide

### Initial Device Pairing

1. **Start the authentication terminal**:
   ```bash
   python terminal_client/auth_client.py --demo
   ```

2. **The terminal will display**:
   - A QR code for easy pairing
   - A 6-digit pairing code
   - Instructions for mobile app setup

3. **On your mobile device**:
   - Open the mobile app
   - Enter the 6-digit pairing code
   - Complete the pairing process

### Daily Authentication Flow

1. **Boot your laptop and enter your password**
2. **The authentication terminal automatically appears**
3. **Your mobile device receives a biometric authentication request**
4. **Scan your fingerprint on the mobile app**
5. **Desktop session launches automatically**

### Remote Control Operations

#### System Control
```python
# Through mobile app or API calls
POST /remote-command
{
    "device_id": "your_device_id",
    "command": "lock|unlock|sleep|shutdown|restart"
}
```

#### File Operations
```python
# List files
POST /file-operation
{
    "device_id": "your_device_id",
    "operation": "list",
    "path": "/home/username"
}

# Copy files
POST /file-operation
{
    "device_id": "your_device_id",
    "operation": "copy",
    "path": "/source/file",
    "destination": "/dest/file"
}
```

## 🔧 Command Line Options

### Authentication Client
```bash
# Demo mode (safe testing)
python auth_client.py --demo

# Setup system integration
python auth_client.py --setup

# Lock screen mode
python auth_client.py --lock

# Handle remote unlock
python auth_client.py --unlock
```

### Terminal Interface
```bash
# Demo mode
python auth_terminal.py

# Lock screen mode
python auth_terminal.py --lock
```

## 🔐 Security Features

### Encryption
- **RSA 2048-bit**: Asymmetric encryption for key exchange
- **AES-256**: Symmetric encryption for message communication
- **Secure Key Storage**: Local encrypted key storage
- **Session Tokens**: Time-limited authentication tokens

### Authentication
- **Multi-factor**: Password + biometric authentication
- **Device Pairing**: Cryptographic device verification
- **Session Management**: Secure session handling
- **Timeout Protection**: Automatic session timeout

## 📱 Mobile App Features

### Interface
- **Dark Theme**: Black background with white text
- **Real-time Status**: Connection, battery, last seen
- **Biometric Prompt**: Fingerprint authentication interface
- **System Controls**: Lock, sleep, restart, shutdown buttons

### File Browser
- **Directory Navigation**: Browse laptop filesystem
- **File Operations**: Copy, delete, move files
- **Remote Access**: Access files even when laptop is off
- **Preview Support**: File type detection and icons

## 🌐 API Endpoints

### Core Authentication
- `POST /pair-device` - Initial device pairing
- `POST /auth-request` - Request biometric authentication
- `GET /auth-status/{device_id}` - Check authentication status
- `WebSocket /ws/{device_id}` - Real-time communication

### System Control
- `POST /remote-command` - Execute system commands
- `GET /system-status` - Get laptop status
- `POST /file-operation` - File system operations

### Device Management
- `GET /paired-devices` - List paired devices
- `DELETE /unpair-device/{device_id}` - Remove device

## 🚨 System Integration

### Ubuntu Integration (Advanced)

For full system integration, you'll need to:

1. **Create PAM Module**: Custom authentication module
2. **Modify GDM**: Display manager configuration
3. **Setup Systemd Services**: Background service management
4. **Configure Autostart**: Automatic startup on boot

```bash
# Run setup assistant
python auth_client.py --setup
```

This creates the necessary scripts and provides guidance for system-level integration.

## 🧪 Testing

### Unit Tests
```bash
# Test cryptographic functions
python -m pytest tests/test_crypto.py

# Test authentication flow
python -m pytest tests/test_auth.py
```

### Integration Testing
```bash
# Test complete flow
python tests/test_integration.py
```

### Manual Testing
1. **Start backend server**
2. **Run terminal demo**: `python auth_client.py --demo`
3. **Open mobile mockup**: Browser at `localhost:8080`
4. **Test pairing and authentication flow**

## 🛡️ Security Considerations

### Production Deployment
- Change default ports and URLs
- Implement certificate-based authentication
- Use proper certificate management
- Set up firewall rules
- Enable audit logging

### Best Practices
- Regular key rotation
- Secure backup of device keys
- Monitor authentication attempts
- Implement rate limiting
- Use VPN for remote access

## 🔧 Troubleshooting

### Common Issues

**Backend server not starting:**
```bash
# Check if port 8000 is available
netstat -tlnp | grep :8000

# Check Python dependencies
pip install -r requirements.txt
```

**Authentication failing:**
```bash
# Check device pairing
python -c "from shared.crypto_utils import CryptoManager; cm = CryptoManager(); print(cm.load_paired_devices())"

# Check server connection
curl http://localhost:8000/
```

**Terminal display issues:**
```bash
# Install terminal dependencies
sudo apt install -y python3-rich

# Check terminal compatibility
echo $TERM
```

## 🚀 Future Enhancements

### Planned Features
- **Multi-device Support**: Multiple mobile devices per laptop
- **Geofencing**: Location-based authentication
- **Voice Commands**: Voice control integration
- **Notification System**: Push notifications for events
- **Cloud Sync**: Configuration synchronization
- **Biometric Alternatives**: Face recognition, voice authentication

### Advanced Integration
- **Active Directory**: Enterprise authentication
- **LDAP Support**: Directory service integration
- **Audit Logging**: Comprehensive security logging
- **Mobile Apps**: Native iOS and Android applications

## 📄 License

This project is for educational and personal use. For production deployment, ensure compliance with your organization's security policies.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs in `configs/`
3. Test individual components
4. Create detailed issue reports

---

**⚠️ Important**: This system provides powerful remote access capabilities. Use responsibly and ensure proper security measures are in place for production use.