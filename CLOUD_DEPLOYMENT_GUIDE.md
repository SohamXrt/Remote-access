# Cloud Deployment Guide

## Deploy Relay Server for Remote Access

When devices are on different networks, deploy the relay server to a cloud provider.

### Option 1: Free Tier Cloud Services

#### A. Railway.app (Easiest)
```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Create new project
railway init

# 4. Deploy
railway up
```

#### B. Render.com (Free Tier)
1. Create account at render.com
2. New Web Service → Connect Git repo
3. Set start command: `python3 persistent_cloud_relay.py`
4. Deploy

#### C. Fly.io (Free Tier)
```bash
# 1. Install flyctl
curl -L https://fly.io/install.sh | sh

# 2. Login
flyctl auth login

# 3. Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
RUN pip install websockets
COPY persistent_cloud_relay.py .
EXPOSE 8765
CMD ["python3", "persistent_cloud_relay.py"]
EOF

# 4. Deploy
flyctl launch
flyctl deploy
```

### Option 2: Your Own VPS

If you have a VPS (DigitalOcean, Linode, AWS EC2, etc):

```bash
# SSH to your server
ssh user@your-server.com

# Install Python and websockets
sudo apt update
sudo apt install python3 python3-pip
pip3 install websockets

# Copy relay server
scp persistent_cloud_relay.py user@your-server.com:~/

# Run with systemd (persistent)
sudo tee /etc/systemd/system/laptop-relay.service << 'EOF'
[Unit]
Description=Laptop Remote Access Relay Server
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/home/your-user
ExecStart=/usr/bin/python3 /home/your-user/persistent_cloud_relay.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable laptop-relay
sudo systemctl start laptop-relay

# Check status
sudo systemctl status laptop-relay

# Open firewall
sudo ufw allow 8765/tcp
```

### Option 3: Ngrok (Quick Testing)

For quick testing without cloud setup:

```bash
# 1. Install ngrok
snap install ngrok

# 2. Authenticate (get token from ngrok.com)
ngrok authtoken YOUR_AUTH_TOKEN

# 3. Expose local server
ngrok tcp 8765
```

You'll get a URL like `tcp://0.tcp.ngrok.io:12345`

### Update APK with Cloud URL

After deploying, update the relay URL in your APK:

```bash
# Edit the relay URL
nano cordova_app/www/standalone_app.html
# Change line 213 to your cloud server:
# const RELAY_URL = 'ws://your-server.com:8765';

nano cordova_app/www/index.html
# Change line 416 similarly

# Rebuild APK
./build_standalone_apk.sh

# Install on phone
adb install -r cordova_app/platforms/android/app/build/outputs/apk/debug/app-debug.apk
```

### Security Considerations

For production use:
1. Use WSS (WebSocket Secure) with SSL/TLS certificate
2. Add authentication tokens
3. Implement rate limiting
4. Use environment variables for configuration
5. Set up monitoring and logging

### Recommended: Railway.app or Render.com

Both offer:
- ✅ Free tier
- ✅ Automatic HTTPS/WSS
- ✅ Easy deployment
- ✅ Good for hobby projects
- ✅ Auto-scaling

## WSS (Secure WebSocket) Setup

If deploying with HTTPS/SSL, update relay URLs to use `wss://` instead of `ws://`:

```javascript
const RELAY_URL = 'wss://your-server.com:8765';
```

Most cloud providers (Railway, Render, Fly.io) automatically provide SSL certificates.
