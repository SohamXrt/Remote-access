#!/bin/bash
# Script to create Android APK from the web app

echo "📱 Creating Android APK from Web App"
echo "===================================="

# Check prerequisites
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Node.js
if ! command_exists node; then
    echo "❌ Node.js not found. Installing..."
    curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

# Check if we're in the right directory
if [ ! -f "mobile_app_mockup/index.html" ]; then
    echo "❌ Please run this script from the laptop-remote-access directory"
    exit 1
fi

echo "📦 Setting up Capacitor project..."

# Create package.json for the mobile app
cd mobile_app_mockup
cat > package.json << EOF
{
  "name": "laptop-remote-access",
  "version": "1.0.0",
  "description": "Laptop Remote Access Mobile App",
  "main": "index.html",
  "scripts": {
    "build": "echo 'Build completed'",
    "serve": "python3 -m http.server 8080"
  },
  "keywords": ["laptop", "remote", "biometric", "security"],
  "author": "Your Name",
  "license": "MIT"
}
EOF

# Install Capacitor
echo "⚙️ Installing Capacitor..."
npm install -g @capacitor/cli @capacitor/core
npm install @capacitor/android

# Initialize Capacitor
echo "🔧 Initializing Capacitor..."
npx cap init "Laptop Remote" "com.laptopremote.app" --web-dir .

# Update capacitor.config.json
cat > capacitor.config.json << EOF
{
  "appId": "com.laptopremote.app",
  "appName": "Laptop Remote",
  "webDir": ".",
  "server": {
    "androidScheme": "https"
  },
  "android": {
    "allowMixedContent": true
  }
}
EOF

# Add Android platform
echo "🤖 Adding Android platform..."
npx cap add android

# Copy web assets
echo "📋 Copying web assets..."
npx cap copy android

# Check if Android SDK is available
if [ ! -d "$ANDROID_HOME" ] && [ ! -d "$HOME/Android/Sdk" ]; then
    echo "⚠️ Android SDK not found!"
    echo "To build APK, you need to:"
    echo "1. Install Android Studio: https://developer.android.com/studio"
    echo "2. Set up Android SDK"
    echo "3. Set ANDROID_HOME environment variable"
    echo ""
    echo "For now, the project is ready. Run these commands when SDK is ready:"
    echo "  cd mobile_app_mockup"
    echo "  npx cap open android"
    echo ""
    echo "Or build APK directly:"
    echo "  ./gradlew assembleDebug"
    exit 0
fi

# Open Android Studio (if available)
echo "🚀 Opening Android project..."
npx cap open android

echo ""
echo "✅ Android project created successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Android Studio should open automatically"
echo "2. Build > Generate Signed Bundle / APK"
echo "3. Choose APK and follow the wizard"
echo ""
echo "🔧 Or build from command line:"
echo "  cd android"
echo "  ./gradlew assembleDebug"
echo ""
echo "📁 APK will be in: android/app/build/outputs/apk/debug/"