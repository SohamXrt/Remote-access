# Deploy to Glitch - Quick Guide

## 🎨 Why Glitch?
- ✅ **100% FREE forever**
- ✅ **No credit card required**
- ✅ **5-10 second wake time**
- ✅ **Easy setup** - Web-based editor

---

## 🚀 Step-by-Step Deployment

### Step 1: Create Glitch Account
1. Go to **https://glitch.com**
2. Click **"Sign Up"**
3. Sign up with **GitHub** (easiest)
4. No card required!

### Step 2: Import from GitHub
1. Click **"New Project"** → **"Import from GitHub"**
2. Paste your repo URL: `https://github.com/SohamXrt/Remote-access`
3. Wait 30 seconds for import

### Step 3: Configure the Project
Glitch will auto-detect Python. Create these files in Glitch editor:

**Create `start.sh`:**
```bash
#!/bin/bash
python3 persistent_cloud_relay.py
```

**Create/Edit `glitch.json`:**
```json
{
  "install": "pip3 install -r requirements.txt",
  "start": "bash start.sh",
  "watch": {
    "ignore": [
      "\\.pyc$"
    ]
  }
}
```

**Edit `requirements.txt`** (should already exist):
```
websockets==12.0
```

### Step 4: Make start.sh executable
In Glitch terminal (bottom):
```bash
chmod +x start.sh
```

### Step 5: Get Your WebSocket URL
1. Click **"Share"** button (top right)
2. Copy the **Live Site** URL (e.g., `laptop-remote-relay.glitch.me`)
3. Your WebSocket URL: `wss://laptop-remote-relay.glitch.me`

---

## 🔧 Alternative: Quick Manual Setup

If import doesn't work, create new Python project manually:

1. **New Project** → **"hello-webpage"** → Change to Python
2. **Delete** default files
3. **Upload** these files from your laptop:
   - `persistent_cloud_relay.py`
   - `requirements.txt`
4. **Create** `start.sh` and `glitch.json` as shown above
5. Click **"Tools"** → **"Terminal"** → Run:
   ```bash
   chmod +x start.sh
   pip3 install -r requirements.txt
   refresh
   ```

---

## 📊 Monitor Your App

### View Logs:
Click **"Logs"** button at bottom of Glitch editor

### Check if Running:
```bash
curl -I https://your-project.glitch.me
```

Should return HTTP 400 (normal for WebSocket server)

---

## ⚙️ Glitch Configuration

**Auto-sleep:** After 5 minutes of no HTTP/WebSocket requests
**Wake time:** ~5-10 seconds
**Max memory:** 512MB
**Always on:** No (free tier sleeps)

---

## 🐛 Troubleshooting

### If app crashes:
1. Check **Logs** in Glitch
2. Verify `requirements.txt` has `websockets==12.0`
3. Ensure `start.sh` is executable

### If connection fails:
1. Verify project is running (green dot on Glitch)
2. Use `wss://` (not `ws://`)
3. Check logs for errors

### If app won't start:
1. Click **"Tools"** → **"Terminal"**
2. Run: `refresh`
3. Check for Python errors in logs

---

## 💡 Keep Your App Awake (Optional)

Free service to ping your Glitch app every 5 minutes:

1. Go to **https://cron-job.org** (free, no signup)
2. Create job: Ping `https://your-project.glitch.me` every 5 min
3. App will never sleep!

**Note:** This uses more resources but keeps your relay always available.

---

## 🎯 Success Checklist

- [ ] Glitch account created (no card!)
- [ ] Project imported/created
- [ ] `start.sh` and `glitch.json` configured
- [ ] App running (green indicator)
- [ ] WebSocket URL copied
- [ ] Laptop client updated
- [ ] Mobile app updated
- [ ] APK rebuilt and installed
- [ ] Successfully paired! 🎉

---

## 📈 Performance

**Latency:**
- India → USA (Glitch servers): ~200ms
- Good enough for remote control!

**Wake time:** 5-10 seconds on first connection

---

## 🆘 Need Help?

1. **Glitch Support**: https://support.glitch.com/
2. **Community**: https://support.glitch.com/c/help/
3. **Status**: https://status.glitch.com/

---

**Estimated Setup Time**: 5-10 minutes
**Monthly Cost**: $0 (FREE FOREVER!)
**Reliability**: ⭐⭐⭐⭐☆ (Good for personal use)
