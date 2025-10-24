#!/bin/bash
# Setup ADB reverse port forwarding so phone can access laptop's WebSocket server

echo "🔧 Setting up ADB reverse port forwarding..."
echo ""

# Check if adb is available
if ! command -v adb &> /dev/null; then
    echo "❌ ADB not found. Install it with: sudo apt install adb"
    exit 1
fi

# Check if device is connected
if ! adb devices | grep -q "device$"; then
    echo "❌ No Android device connected via USB"
    echo "   1. Connect your phone via USB"
    echo "   2. Enable USB debugging on your phone"
    echo "   3. Accept the debugging prompt on your phone"
    exit 1
fi

echo "✅ Android device detected"
echo ""

# Setup reverse port forwarding
# This makes phone's localhost:8765 connect to laptop's localhost:8765
adb reverse tcp:8765 tcp:8765

if [ $? -eq 0 ]; then
    echo "✅ Port forwarding setup successful!"
    echo ""
    echo "📱 Your phone can now connect to: ws://localhost:8765"
    echo "   (which will route to your laptop's relay server)"
    echo ""
    echo "⚠️  Note: This only works while USB is connected"
else
    echo "❌ Failed to setup port forwarding"
    exit 1
fi
