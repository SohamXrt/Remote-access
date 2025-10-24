#!/bin/bash
# Build Standalone Laptop Remote Access APK

echo "🔨 Building Standalone Laptop Remote Access APK..."
echo "=================================================="

cd cordova_app

echo ""
echo "📦 Installing Cordova dependencies..."
npm install

echo ""
echo "🔧 Adding Android platform (if not exists)..."
cordova platform add android 2>/dev/null || echo "Android platform already added"

echo ""
echo "🏗️  Building APK..."
cordova build android

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! APK built successfully!"
    echo ""
    echo "📱 APK Location:"
    echo "   Debug: cordova_app/platforms/android/app/build/outputs/apk/debug/app-debug.apk"
    echo ""
    echo "📲 Install on your Android device:"
    echo "   adb install -r platforms/android/app/build/outputs/apk/debug/app-debug.apk"
    echo ""
    echo "🌐 IMPORTANT: Update RELAY_URL in standalone_app.html"
    echo "   Current: ws://10.141.47.200:8765"
    echo "   Change to your cloud relay server IP/domain"
    echo ""
else
    echo ""
    echo "❌ Build failed. Please check the errors above."
    exit 1
fi
