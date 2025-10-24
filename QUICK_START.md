# Quick Start - Standalone Laptop Remote Access

## 🎯 What You Have Now

A **standalone Android APK** that lets you control your laptop from anywhere in the world **without any backend server running on your laptop**. Just the APK + cloud relay + laptop client.

## ✅ APK Status

**BUILT SUCCESSFULLY!**

Location: `cordova_app/platforms/android/app/build/outputs/apk/debug/app-debug.apk`

## 🚀 Getting Started (3 Steps)

### 1. Start Cloud Relay Server

```bash
./START_SYSTEM.sh relay
```

Or run on a cloud server (AWS/DigitalOcean/etc).

### 2. Install APK on Your Phone

```bash
# Connect phone via USB with USB debugging enabled
./START_SYSTEM.sh install
```

Or manually copy and install the APK from the location above.

### 3. Start Laptop Client

```bash
./START_SYSTEM.sh laptop
```

You'll get a **6-digit pairing code**. Enter it in the mobile app.

## 📱 Using the Mobile App

1. Open "Laptop Remote" on your phone
2. Wait for "Connection: Connected" status (green)
3. Enter the 6-digit code from your laptop
4. Click "Pair Device"
5. ✅ You're connected!

### Available Controls:
- **🔒 Lock** - Lock laptop screen
- **😴 Sleep** - Put laptop to sleep  
- **🔄 Restart** - Restart laptop
- **⚡ Shutdown** - Shut down laptop
- **☀️ Wake Up** - Wake from sleep
- **📁 Files** - Browse laptop files

## 🌍 For Remote Access

### Option 1: Use Your Laptop as Relay (Simple)

1. On your laptop:
   ```bash
   ./START_SYSTEM.sh relay
   ```

2. Forward port 8765 in your router

3. Update APK with your public IP:
   ```javascript
   // Edit: cordova_app/www/standalone_app.html line 213
   const RELAY_URL = 'ws://YOUR_PUBLIC_IP:8765';
   ```

4. Rebuild: `./START_SYSTEM.sh build`

5. Reinstall: `./START_SYSTEM.sh install`

### Option 2: Use Cloud Server (Better)

1. Get a VPS (DigitalOcean, AWS, etc.)

2. On the VPS:
   ```bash
   sudo apt install python3 python3-pip
   pip3 install websockets
   python3 persistent_cloud_relay.py
   ```

3. Update APK with VPS IP/domain:
   ```javascript
   const RELAY_URL = 'ws://your-vps-ip:8765';
   ```

4. Rebuild and reinstall APK

5. Now both laptop and mobile connect to the VPS!

## 🔧 Configuration

### Update Relay Server URL

Before building, edit:
```
cordova_app/www/standalone_app.html
```

Find line 213:
```javascript
const RELAY_URL = 'ws://10.141.47.200:8765';  // Change this!
```

Change to:
- `ws://YOUR_IP:8765` for your server
- `wss://yourdomain.com:8765` for HTTPS/secure

### Then rebuild:
```bash
./START_SYSTEM.sh build
./START_SYSTEM.sh install
```

## 💡 Key Features

### ✅ Works Without Backend
Unlike web apps, this APK doesn't need a backend server running on your laptop. It connects directly via cloud relay.

### ✅ Persistent Pairing
Once paired, you don't need to re-pair after:
- Restarting the app
- Restarting your laptop
- Reconnecting to WiFi

Everything is saved!

### ✅ Global Access
Control your laptop from anywhere in the world as long as:
- Cloud relay is running
- Laptop client is running
- Both have internet connection

### ✅ File Access
Browse and view files on your laptop remotely (up to 1MB per file).

## 🔐 Security Notes

This is a **development version**. For production:

1. Use `wss://` (secure WebSocket) instead of `ws://`
2. Set up HTTPS on your relay server
3. Add authentication tokens
4. Enable firewall rules
5. Use strong pairing codes

See `STANDALONE_APK_GUIDE.md` for security setup.

## 🐛 Troubleshooting

### "Connection: Disconnected" in app
- Check relay server is running
- Verify RELAY_URL matches your server
- Test with: `telnet YOUR_SERVER_IP 8765`

### Pairing fails
- Ensure laptop client is running
- Check code hasn't expired (10 min)
- Both must connect to same relay server

### Commands don't work
- Check laptop client logs
- On Linux: may need sudo permissions
- See permission setup in full guide

### Can't build APK
- Check Cordova is installed: `cordova --version`
- Install: `npm install -g cordova`
- Check Android SDK is set up

## 📂 File Structure

```
laptop-remote-access/
├── cordova_app/
│   ├── www/
│   │   └── standalone_app.html        # Mobile app (edit RELAY_URL here)
│   └── platforms/android/
│       └── app/build/outputs/apk/
│           └── debug/app-debug.apk    # Your APK!
│
├── persistent_cloud_relay.py          # Cloud relay server
├── persistent_laptop_client.py        # Laptop client
│
├── START_SYSTEM.sh                    # Quick start script
├── build_standalone_apk.sh            # Build APK
│
├── QUICK_START.md                     # This file
└── STANDALONE_APK_GUIDE.md           # Full documentation
```

## 📚 Next Steps

1. ✅ APK is built
2. 📱 Install on your phone
3. 🌐 Deploy relay to cloud server (optional)
4. 🔐 Set up HTTPS for security (optional)
5. ☀️ Configure Wake-on-LAN (optional)

## 🎓 Learn More

- **Full Guide**: `STANDALONE_APK_GUIDE.md`
- **Architecture**: Cloud relay bridges mobile ↔ laptop
- **Customization**: Edit `standalone_app.html` for UI changes

## 🆘 Need Help?

```bash
# Check if relay is accessible
telnet YOUR_SERVER_IP 8765

# View laptop client logs
./START_SYSTEM.sh laptop

# Check mobile app console (Chrome DevTools via USB)
chrome://inspect
```

---

## Commands Cheatsheet

```bash
# Start components
./START_SYSTEM.sh relay       # Start relay server
./START_SYSTEM.sh laptop      # Start laptop client

# Build & install
./START_SYSTEM.sh build       # Build APK
./START_SYSTEM.sh install     # Install on phone

# Manual commands
python3 persistent_cloud_relay.py      # Start relay
python3 persistent_laptop_client.py    # Start laptop
cordova build android                   # Build APK manually
adb install -r path/to/app-debug.apk   # Install manually
```

---

**🎉 Your standalone laptop remote access system is ready!**

No more backend servers, no more localhost issues, just pure remote control from anywhere! 🚀
