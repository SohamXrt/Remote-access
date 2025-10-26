# Deploy to Railway - Step by Step Guide

## 🚂 Railway Deployment Instructions

### Step 1: Sign Up for Railway
1. Go to **https://railway.app**
2. Click **"Start a New Project"**
3. Sign up with **GitHub** (easiest)

### Step 2: Connect Your Repository
1. In Railway dashboard, click **"+ New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose your repository: **SohamXrt/Remote-access**
4. Railway will auto-detect it's a Python project

### Step 3: Configure Environment
Railway will automatically:
- ✅ Detect `requirements.txt`
- ✅ Install `websockets`
- ✅ Run `persistent_cloud_relay.py`

### Step 4: Get Your WebSocket URL
1. After deployment, go to **Settings** → **Networking**
2. Click **"Generate Domain"**
3. You'll get a URL like: `your-app.railway.app`
4. Your WebSocket URL will be: `wss://your-app.railway.app`

### Step 5: Update Your Code
Replace the Render URL with your Railway URL:

**In `persistent_laptop_client.py` (line 438):**
```python
relay_url = "wss://your-app.railway.app"  # Replace with your Railway URL
```

**In `cordova_app/www/index.html` (line 201):**
```javascript
const CLOUD_RELAY_URL = 'wss://your-app.railway.app';  // Replace with your Railway URL
```

### Step 6: Rebuild and Deploy
```bash
# Commit changes
git add -A
git commit -m "Switch to Railway relay server"
git push origin master

# Rebuild mobile APK
./build_standalone_apk.sh

# Install on phone
adb install -r cordova_app/platforms/android/app/build/outputs/apk/debug/app-debug.apk
```

### Step 7: Restart Laptop Client
```bash
pkill -f persistent_laptop_client
python3 persistent_laptop_client.py
```

---

## ⚙️ Railway Configuration

Railway automatically uses:
- **Port**: Assigned by Railway (via `$PORT` env var)
- **Region**: Auto-selected (closest to you)
- **Resources**: 512MB RAM, 1 vCPU (free tier)

---

## 💰 Free Tier Limits

- **$5 credit per month** (resets monthly)
- **~150 hours** of runtime (more than enough!)
- **500MB RAM** usage
- **No sleep** - Always on!

---

## 🔍 Monitor Your Deployment

1. Go to Railway dashboard
2. Click on your project
3. View **Logs** tab to see:
   - Server starting
   - Devices connecting
   - Pairing attempts

---

## 🐛 Troubleshooting

### If deployment fails:
1. Check **Logs** in Railway dashboard
2. Ensure `requirements.txt` has `websockets==12.0`
3. Ensure `persistent_cloud_relay.py` uses `PORT` env var:
   ```python
   PORT = int(os.environ.get("PORT", 8765))
   ```

### If connection fails:
1. Verify domain is generated: Settings → Networking
2. Use `wss://` (not `ws://`) for secure WebSocket
3. Check Railway logs for errors

---

## 🎉 Success Checklist

- [ ] Railway account created
- [ ] GitHub repo connected
- [ ] Project deployed successfully
- [ ] Domain generated
- [ ] Laptop client updated with new URL
- [ ] Mobile app updated with new URL
- [ ] Mobile APK rebuilt and installed
- [ ] Laptop client restarted
- [ ] Successfully paired!

---

## 📞 Need Help?

If you get stuck:
1. Check Railway logs for errors
2. Verify your WebSocket URL format: `wss://your-app.railway.app`
3. Make sure both laptop and mobile use the SAME URL

---

**Estimated Time**: 10-15 minutes
**Cost**: FREE ($5/month credit included)
**Reliability**: ⭐⭐⭐⭐⭐ (Much better than Render free tier!)
