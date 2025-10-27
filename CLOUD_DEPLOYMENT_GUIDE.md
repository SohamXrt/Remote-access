# Cloud Deployment Guide

## Deploy Relay Server for Remote Access

When devices are on different networks, deploy the relay server to a cloud provider.

### Fly.io Deployment (Recommended)

Fly.io provides always-on WebSocket hosting with free tier ($5/month credit).

#### Prerequisites
- Fly.io account with payment method verified
- flyctl CLI installed

#### Deployment Steps

```bash
# 1. Install flyctl
curl -L https://fly.io/install.sh | sh
export PATH="$HOME/.fly/bin:$PATH"

# 2. Login to Fly.io
flyctl auth login

# 3. Deploy (from project root)
cd /path/to/laptop-remote-access
flyctl deploy

# 4. Check deployment status
flyctl status -a laptop-remote-relay

# 5. View logs
flyctl logs -a laptop-remote-relay
```

#### Your Relay URL
After deployment, your relay will be available at:
```
wss://laptop-remote-relay.fly.dev
```

This URL is already configured in both the laptop client and mobile app.

### Alternative: Your Own VPS

If you prefer to self-host on your own VPS:

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
Environment="PORT=8080"

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable laptop-relay
sudo systemctl start laptop-relay

# Check status
sudo systemctl status laptop-relay

# Open firewall
sudo ufw allow 8080/tcp
```

Then update the relay URL in `persistent_laptop_client.py` and `cordova_app/www/index.html` to point to your VPS.

### Security Considerations

For production use:
1. ✅ WSS (WebSocket Secure) with SSL/TLS - **Automatically provided by Fly.io**
2. Add authentication tokens for API access
3. Implement rate limiting
4. Use environment variables for configuration
5. Set up monitoring and logging

### Why Fly.io?

- ✅ **Always-on**: No sleep/wake delays
- ✅ **Free tier**: $5/month credit (enough for this relay)
- ✅ **Automatic HTTPS/WSS**: SSL certificates included
- ✅ **Global edge network**: Low latency worldwide
- ✅ **WebSocket support**: Native WS/WSS support
- ✅ **Simple deployment**: Single command deployment

### Cost Estimate

Your relay server configuration:
- 2 machines × 256MB RAM
- Estimated: **$3-4/month**
- **Covered by free $5/month credit**
