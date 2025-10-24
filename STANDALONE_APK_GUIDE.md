# Standalone Laptop Remote Access APK - Complete Guide

## Overview
This standalone Android APK allows you to remotely control your laptop **without needing any backend server running**. It connects directly to a cloud relay server via WebSocket, enabling:

- ✅ Remote system control (lock, sleep, restart, shutdown)
- ✅ File browsing and access
- ✅ Works even when laptop is sleeping (Wake-on-LAN ready)
- ✅ Persistent pairing across app restarts
- ✅ No local backend server required

## Architecture

```
[Android APK] <--WebSocket--> [Cloud Relay Server] <--WebSocket--> [Laptop Client]
     ↑                                                                    ↑
   Mobile                                                              Your PC
 (anywhere)                                                         (anywhere)
```

## Quick Start

### Step 1: Setup Cloud Relay Server

You need a publicly accessible server (VPS, cloud instance, or local with port forwarding).

```bash
# On your cloud server
python3 persistent_cloud_relay.py
```

The relay will run on port 8765 by default.

### Step 2: Update APK Configuration

Before building, update the relay URL in the APK:

```bash
# Edit cordova_app/www/standalone_app.html
# Find line 213:
const RELAY_URL = 'ws://YOUR_SERVER_IP:8765';  // Change this!

# Examples:
# const RELAY_URL = 'ws://123.45.67.89:8765';    // Public IP
# const RELAY_URL = 'ws://myserver.com:8765';     // Domain
# const RELAY_URL = 'wss://myserver.com:8765';    // Secure WebSocket (HTTPS)
```

### Step 3: Build the APK

```bash
# In the laptop-remote-access directory
./build_standalone_apk.sh
```

The APK will be created at:
```
cordova_app/platforms/android/app/build/outputs/apk/debug/app-debug.apk
```

### Step 4: Install APK on Android

**Option A: Using ADB (USB)**
```bash
adb install -r cordova_app/platforms/android/app/build/outputs/apk/debug/app-debug.apk
```

**Option B: Transfer and Install Manually**
1. Copy the APK to your phone (email, USB, cloud storage)
2. Open the APK on your phone
3. Allow installation from unknown sources if prompted
4. Install the app

### Step 5: Start Laptop Client

On your laptop:

```bash
python3 persistent_laptop_client.py
```

You'll see:
```
🔑 PAIRING CODE: 123456
📱 Enter this code in your mobile app to pair
```

### Step 6: Pair Mobile App

1. Open the "Laptop Remote" app on your Android phone
2. Wait for "Connection: Connected" status
3. Enter the 6-digit pairing code from your laptop
4. Click "Pair Device"

✅ Done! You're now paired and can control your laptop remotely.

## Features

### System Controls

- **🔒 Lock**: Lock your laptop screen
- **😴 Sleep**: Put laptop to sleep
- **🔄 Restart**: Restart the laptop
- **⚡ Shutdown**: Shut down the laptop
- **☀️ Wake Up**: Wake laptop from sleep (Wake-on-LAN)

### File Access

- **📁 Files**: Browse laptop files remotely
- **📄 View**: Read file contents (up to 1MB)
- **📋 List**: Navigate directories

### Persistent Pairing

Once paired, the connection is saved:
- **Mobile app** remembers your laptop
- **Laptop client** remembers your mobile device
- **Cloud relay** stores trusted pairings
- No need to re-pair after restart!

## Important Notes

### Wake-on-LAN Setup (Optional)

To wake your laptop when it's fully powered off:

1. Enable WOL in BIOS/UEFI
2. Enable WOL in OS network settings:

**Ubuntu/Linux:**
```bash
sudo ethtool -s eth0 wol g  # Replace eth0 with your interface
```

**Windows:**
- Device Manager → Network Adapter → Properties
- Power Management → "Allow this device to wake the computer"

3. Keep laptop plugged in to power
4. Use the "☀️ Wake Up" button in the mobile app

### Security Considerations

⚠️ **This is a development setup.** For production:

1. **Use WSS (Secure WebSocket)**: Set up HTTPS/TLS on your relay server
2. **Add authentication**: Implement token-based auth for relay connections
3. **Encrypt payloads**: Add end-to-end encryption between devices
4. **Use firewall**: Restrict relay server access
5. **Change default ports**: Use non-standard ports

### Troubleshooting

**Mobile app shows "Disconnected":**
- Check relay server is running
- Verify RELAY_URL in app matches your server
- Check firewall allows port 8765
- Test with: `telnet YOUR_SERVER_IP 8765`

**Pairing fails:**
- Ensure laptop client is running
- Check pairing code hasn't expired (10 min)
- Verify both devices connect to same relay server
- Check relay server logs for errors

**Commands not executing:**
- Verify laptop client has proper permissions
- For shutdown/restart on Linux: add sudo permissions or use PolicyKit
- Check laptop client logs for errors

**File access not working:**
- Check file permissions on laptop
- Ensure path exists
- Files larger than 1MB cannot be viewed

### File Permissions for System Commands

For Linux, to allow shutdown/restart without password:

```bash
# Add to /etc/sudoers (use visudo):
your_username ALL=(ALL) NOPASSWD: /usr/bin/systemctl suspend
your_username ALL=(ALL) NOPASSWD: /usr/sbin/reboot
your_username ALL=(ALL) NOPASSWD: /usr/sbin/shutdown
```

Or use PolicyKit for better security.

## Advanced Configuration

### Change Relay Port

**Relay Server:**
```python
# In persistent_cloud_relay.py
PORT = 8765  # Change this
```

**Mobile App:**
```javascript
// In cordova_app/www/standalone_app.html
const RELAY_URL = 'ws://YOUR_SERVER:YOUR_PORT';
```

**Laptop Client:**
```python
# In persistent_laptop_client.py
relay_url = "ws://YOUR_SERVER:YOUR_PORT"
```

### Deploy Relay on Cloud

**AWS EC2 / DigitalOcean / Linode:**
1. Create Ubuntu instance
2. Open port 8765 in security groups
3. Install Python 3.8+
4. Install websockets: `pip3 install websockets`
5. Run relay: `python3 persistent_cloud_relay.py`
6. Use `systemd` or `screen` to keep it running

**Docker:**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY persistent_cloud_relay.py .
RUN pip install websockets
EXPOSE 8765
CMD ["python", "persistent_cloud_relay.py"]
```

### Production HTTPS Setup

Use nginx as reverse proxy:

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location /relay {
        proxy_pass http://localhost:8765;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Then update mobile app:
```javascript
const RELAY_URL = 'wss://your-domain.com/relay';
```

## File Structure

```
laptop-remote-access/
├── cordova_app/
│   ├── www/
│   │   └── standalone_app.html      # Standalone mobile app
│   ├── config.xml                    # Cordova configuration
│   └── platforms/android/            # Built APK location
├── persistent_cloud_relay.py         # Cloud relay server
├── persistent_laptop_client.py       # Laptop client
├── build_standalone_apk.sh           # Build script
└── STANDALONE_APK_GUIDE.md          # This file
```

## Comparison: Web App vs Standalone APK

| Feature | Web App | Standalone APK |
|---------|---------|----------------|
| Requires backend server | ✅ Yes | ❌ No |
| Works when laptop off | ❌ No | ✅ Yes |
| Native biometrics | ❌ No | ✅ Yes |
| Persistent pairing | ❌ No | ✅ Yes |
| File access | Limited | ✅ Full |
| Installation | None | APK Install |

## Next Steps

1. ✅ Build and install the APK
2. ✅ Deploy cloud relay to a public server
3. ✅ Pair your devices
4. 🔒 Set up HTTPS/WSS for security
5. 📱 Test all remote commands
6. ☀️ Configure Wake-on-LAN
7. 🎨 Customize the UI if needed

## Support

For issues or questions:
- Check the logs: laptop client and relay server both log to console
- Enable debug mode: Set logging level to DEBUG in Python files
- Test connectivity: Use WebSocket test tools like wscat

## License

Use freely for personal projects. Add proper authentication and encryption for production use.

---

**Enjoy your standalone laptop remote access system! 🚀**
