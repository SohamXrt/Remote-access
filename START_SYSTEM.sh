#!/bin/bash
# Quick Start Script for Standalone Laptop Remote Access

echo "🚀 Laptop Remote Access - Quick Start"
echo "======================================"
echo ""

# Check what to start
if [ "$1" == "relay" ]; then
    echo "🌐 Starting Cloud Relay Server..."
    echo "Port: 8765"
    echo "Press Ctrl+C to stop"
    echo ""
    python3 persistent_cloud_relay.py
    
elif [ "$1" == "laptop" ]; then
    echo "💻 Starting Laptop Client..."
    echo "Connecting to cloud relay..."
    echo "Press Ctrl+C to stop"
    echo ""
    python3 persistent_laptop_client.py
    
elif [ "$1" == "install" ]; then
    echo "📱 Installing APK on connected Android device..."
    APK_PATH="cordova_app/platforms/android/app/build/outputs/apk/debug/app-debug.apk"
    
    if [ ! -f "$APK_PATH" ]; then
        echo "❌ APK not found! Build it first:"
        echo "   ./build_standalone_apk.sh"
        exit 1
    fi
    
    adb install -r "$APK_PATH"
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ APK installed successfully!"
        echo "📱 Open 'Laptop Remote' app on your phone"
    else
        echo ""
        echo "❌ Installation failed. Make sure:"
        echo "   - Phone is connected via USB"
        echo "   - USB debugging is enabled"
        echo "   - Run: adb devices"
    fi
    
elif [ "$1" == "build" ]; then
    echo "🔨 Building APK..."
    ./build_standalone_apk.sh
    
else
    echo "Usage:"
    echo "  ./START_SYSTEM.sh relay    - Start cloud relay server"
    echo "  ./START_SYSTEM.sh laptop   - Start laptop client"
    echo "  ./START_SYSTEM.sh build    - Build APK"
    echo "  ./START_SYSTEM.sh install  - Install APK on phone"
    echo ""
    echo "Setup Order:"
    echo "  1. Start relay server (on cloud or local)"
    echo "  2. Build and install APK"
    echo "  3. Start laptop client"
    echo "  4. Open app on phone and pair"
    echo ""
    echo "📖 Read STANDALONE_APK_GUIDE.md for detailed instructions"
fi
