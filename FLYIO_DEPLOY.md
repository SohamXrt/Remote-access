# Deploy to Fly.io - Complete Guide

## ✈️ Why Fly.io?
- ✅ **Free forever** ($5 credit/month, your relay uses ~$0.50/month)
- ✅ **Never sleeps** - Always on!
- ✅ **Fast** - Global edge network
- ✅ **Reliable** - 99.9% uptime

---

## 📋 Prerequisites
- Debit/Credit card (for verification only, won't charge)
- GitHub account

---

## 🚀 Step-by-Step Deployment

### Step 1: Install Fly.io CLI
```bash
curl -L https://fly.io/install.sh | sh
```

Add to PATH:
```bash
echo 'export FLYCTL_INSTALL="/home/soham/.fly"' >> ~/.bashrc
echo 'export PATH="$FLYCTL_INSTALL/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Step 2: Sign Up & Login
```bash
fly auth signup
# OR if already have account:
fly auth login
```

**Enter your debit card** when prompted (won't be charged!)

### Step 3: Deploy Your App
```bash
cd /home/soham/laptop-remote-access
fly launch --no-deploy
```

When prompted:
- App name: **laptop-remote-relay** (or choose your own)
- Region: **sin** (Singapore - closest to India)
- Setup Postgres? **No**
- Setup Redis? **No**

### Step 4: Configure & Deploy
```bash
# Deploy the app
fly deploy

# Wait 2-3 minutes for deployment
```

### Step 5: Get Your WebSocket URL
```bash
fly status
```

You'll get a URL like: `laptop-remote-relay.fly.dev`

Your WebSocket URL: `wss://laptop-remote-relay.fly.dev`

---

## 🔧 Update Your Code

I'll do this for you once you give me the Fly.io URL!

**In `persistent_laptop_client.py`:**
```python
relay_url = "wss://laptop-remote-relay.fly.dev"
```

**In `cordova_app/www/index.html`:**
```javascript
const CLOUD_RELAY_URL = 'wss://laptop-remote-relay.fly.dev';
```

---

## 📊 Monitor Your App

### View Logs:
```bash
fly logs
```

### Check Status:
```bash
fly status
```

### View Dashboard:
```bash
fly open
# Opens dashboard in browser
```

---

## 💰 Cost Tracking

### Check Usage:
```bash
fly billing
```

**Expected Monthly Cost**: ~$0.50 (well within $5 free credit!)

Breakdown:
- 1 shared-cpu VM: ~$0.30/month
- 160GB bandwidth: FREE
- Storage: Negligible

---

## 🐛 Troubleshooting

### If deployment fails:
```bash
fly logs
# Check for errors
```

### If WebSocket doesn't connect:
1. Verify deployment: `fly status`
2. Check logs: `fly logs`
3. Test connection: `curl -I https://laptop-remote-relay.fly.dev`

### If "app not found":
```bash
fly apps list
# Shows all your apps
```

---

## 🎯 Success Checklist

- [ ] Fly.io CLI installed
- [ ] Signed up with debit card
- [ ] App deployed successfully
- [ ] Got WebSocket URL
- [ ] Updated laptop client code
- [ ] Updated mobile app code
- [ ] Rebuilt mobile APK
- [ ] Installed new APK
- [ ] Tested pairing - SUCCESS! 🎉

---

## ⚙️ Advanced Commands

### Scale (if needed):
```bash
fly scale count 1  # Keep 1 machine always running
```

### Restart app:
```bash
fly apps restart laptop-remote-relay
```

### SSH into machine:
```bash
fly ssh console
```

### Delete app (if needed):
```bash
fly apps destroy laptop-remote-relay
```

---

## 🔐 Security

Fly.io provides:
- ✅ **TLS/SSL** by default (wss://)
- ✅ **DDoS protection**
- ✅ **Automatic certificates**
- ✅ **Private networking**

Your WebSocket connections are encrypted end-to-end!

---

## 📈 Performance

Expected latency:
- India → Singapore: **~50ms**
- USA → Singapore: **~200ms**
- Europe → Singapore: **~150ms**


---

## 🆘 Need Help?

1. **Fly.io Docs**: https://fly.io/docs/
2. **Community Forum**: https://community.fly.io/
3. **Status Page**: https://status.fly.io/

---

**Estimated Setup Time**: 15 minutes
**Monthly Cost**: $0 (within free credits)
**Reliability**: ⭐⭐⭐⭐⭐
