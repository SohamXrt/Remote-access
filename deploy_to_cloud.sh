#!/bin/bash
# Deploy Relay Server to Cloud

echo "🚀 Laptop Remote Access - Cloud Deployment"
echo "=========================================="
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "📦 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit - Laptop Remote Access Relay"
fi

echo ""
echo "Choose deployment option:"
echo "1) Render.com (Recommended - Free, No CC required)"
echo "2) Fly.io (Free tier - requires credit card)"
echo "3) Railway.app (Free $5 credit - requires GitHub)"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo "📘 Deploying to Render.com"
        echo "=========================="
        echo ""
        echo "Steps to deploy:"
        echo "1. Go to https://render.com and sign up (free, no credit card)"
        echo "2. Click 'New +' → 'Web Service'"
        echo "3. Connect your GitHub account or 'Deploy from a public Git repository'"
        echo "4. If using public repo:"
        echo "   - First push this code to GitHub:"
        echo "     git remote add origin YOUR_GITHUB_REPO_URL"
        echo "     git push -u origin main"
        echo "5. In Render:"
        echo "   - Repository: Select your repo"
        echo "   - Name: laptop-remote-relay"
        echo "   - Environment: Docker"
        echo "   - Plan: Free"
        echo "6. Click 'Create Web Service'"
        echo "7. Wait for deployment (2-3 minutes)"
        echo "8. Copy your URL: https://laptop-remote-relay.onrender.com"
        echo ""
        echo "Then update your APK with the URL (see below)"
        ;;
    2)
        echo ""
        echo "✈️  Deploying to Fly.io"
        echo "====================="
        echo ""
        if ! command -v flyctl &> /dev/null; then
            echo "Installing flyctl..."
            curl -L https://fly.io/install.sh | sh
            export FLYCTL_INSTALL="/home/$USER/.fly"
            export PATH="$FLYCTL_INSTALL/bin:$PATH"
        fi
        
        echo "Logging in to Fly.io..."
        flyctl auth login
        
        echo "Creating and deploying app..."
        flyctl launch --name laptop-remote-relay --region sjc --no-deploy
        flyctl deploy
        
        echo ""
        echo "✅ Deployed! Your URL:"
        flyctl status | grep "Hostname"
        ;;
    3)
        echo ""
        echo "🚂 Deploying to Railway.app"
        echo "=========================="
        echo ""
        if ! command -v railway &> /dev/null; then
            echo "Installing Railway CLI..."
            npm install -g @railway/cli
        fi
        
        echo "Logging in to Railway..."
        railway login
        
        echo "Creating project..."
        railway init
        
        echo "Deploying..."
        railway up
        
        echo ""
        echo "✅ Deployed! Get your URL:"
        railway domain
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "📱 Update APK with Cloud URL"
echo "=========================================="
echo ""
echo "After deployment, update the RELAY_URL in your app:"
echo ""
echo "1. Edit cordova_app/www/standalone_app.html (line 213)"
echo "2. Edit cordova_app/www/index.html (line 416)"
echo "3. Change to: const RELAY_URL = 'wss://your-app.onrender.com';"
echo "   (Note: Use 'wss://' for secure WebSocket, not 'ws://')"
echo ""
echo "4. Rebuild APK:"
echo "   cd /home/soham/laptop-remote-access"
echo "   ./build_standalone_apk.sh"
echo ""
echo "5. Install on phone:"
echo "   adb install -r cordova_app/platforms/android/app/build/outputs/apk/debug/app-debug.apk"
echo ""
echo "🎉 Done! Your app will now work from anywhere!"
