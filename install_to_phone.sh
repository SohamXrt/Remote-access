#!/bin/bash
# Script to build and install APK directly to connected Android device

echo "📱 Building and Installing APK to Connected Phone"
echo "==============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if phone is connected
check_device() {
    print_status "Checking for connected Android device..."
    
    # Install adb if not present
    if ! command -v adb &> /dev/null; then
        print_status "Installing Android Debug Bridge (adb)..."
        sudo apt update
        sudo apt install -y android-tools-adb android-tools-fastboot
    fi
    
    # Check device connection
    devices=$(adb devices | grep -v "List of devices" | grep -v "^$" | wc -l)
    
    if [ "$devices" -eq 0 ]; then
        print_error "No Android device detected!"
        print_warning "Please ensure:"
        print_warning "1. USB Debugging is enabled in Developer Options"
        print_warning "2. Phone is connected via USB"
        print_warning "3. You've authorized this computer on your phone"
        print_warning ""
        print_warning "To enable USB Debugging:"
        print_warning "Settings → About Phone → Tap 'Build Number' 7 times"
        print_warning "Settings → Developer Options → Enable 'USB Debugging'"
        return 1
    fi
    
    device_info=$(adb devices | grep -v "List of devices" | head -1)
    print_success "Found device: $device_info"
    return 0
}

# Create a simple APK using Android tools
create_simple_apk() {
    print_status "Creating simple APK package..."
    
    # Create APK structure
    APK_DIR="simple_apk"
    rm -rf "$APK_DIR"
    mkdir -p "$APK_DIR"/{assets,res/values,res/drawable}
    
    # Create AndroidManifest.xml
    cat > "$APK_DIR/AndroidManifest.xml" << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.laptopremote.app"
    android:versionCode="1"
    android:versionName="1.0">
    
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.USE_FINGERPRINT" />
    <uses-permission android:name="android.permission.USE_BIOMETRIC" />
    
    <application
        android:allowBackup="true"
        android:label="Laptop Remote"
        android:theme="@android:style/Theme.Black.NoTitleBar.Fullscreen">
        
        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
EOF

    # Copy web assets
    cp mobile_app_mockup/index.html "$APK_DIR/assets/"
    cp mobile_app_mockup/manifest.json "$APK_DIR/assets/" 2>/dev/null || true
    
    # Create strings.xml
    cat > "$APK_DIR/res/values/strings.xml" << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">Laptop Remote</string>
</resources>
EOF

    print_success "APK structure created"
}

# Build using cordova (simpler approach)
build_with_cordova() {
    print_status "Setting up Cordova project..."
    
    # Install cordova if not present
    if ! command -v cordova &> /dev/null; then
        print_status "Installing Cordova..."
        
        # Install Node.js if needed
        if ! command -v node &> /dev/null; then
            curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
            sudo apt-get install -y nodejs
        fi
        
        sudo npm install -g cordova
    fi
    
    # Create cordova project
    CORDOVA_DIR="cordova_app"
    rm -rf "$CORDOVA_DIR"
    
    print_status "Creating Cordova project..."
    cordova create "$CORDOVA_DIR" com.laptopremote.app "Laptop Remote"
    cd "$CORDOVA_DIR"
    
    # Copy our web app
    rm -rf www/*
    cp ../mobile_app_mockup/* www/
    
    # Add Android platform
    print_status "Adding Android platform..."
    cordova platform add android
    
    # Install plugins for biometric and network
    print_status "Installing plugins..."
    cordova plugin add cordova-plugin-fingerprint-aio || true
    cordova plugin add cordova-plugin-network-information || true
    cordova plugin add cordova-plugin-device || true
    
    # Build APK
    print_status "Building APK..."
    cordova build android
    
    if [ -f "platforms/android/app/build/outputs/apk/debug/app-debug.apk" ]; then
        cp "platforms/android/app/build/outputs/apk/debug/app-debug.apk" "../laptop_remote.apk"
        print_success "APK created: laptop_remote.apk"
        cd ..
        return 0
    else
        print_error "APK build failed"
        cd ..
        return 1
    fi
}

# Install APK to device
install_apk() {
    APK_FILE="$1"
    
    if [ ! -f "$APK_FILE" ]; then
        print_error "APK file not found: $APK_FILE"
        return 1
    fi
    
    print_status "Installing APK to device..."
    
    # Uninstall existing version if present
    adb uninstall com.laptopremote.app 2>/dev/null || true
    
    # Install new APK
    if adb install "$APK_FILE"; then
        print_success "APK installed successfully!"
        print_success "Look for 'Laptop Remote' app on your phone"
        return 0
    else
        print_error "APK installation failed"
        print_warning "Try installing manually:"
        print_warning "1. Copy laptop_remote.apk to your phone"
        print_warning "2. Open file manager and tap the APK"
        print_warning "3. Allow installation from unknown sources if prompted"
        return 1
    fi
}

# Create web app launcher APK (lightweight approach)
create_web_launcher_apk() {
    print_status "Creating web app launcher APK..."
    
    # This creates a simple APK that opens our web app
    APK_DIR="web_launcher"
    rm -rf "$APK_DIR"
    mkdir -p "$APK_DIR"
    
    # Create a simple HTML that redirects to our web app
    cat > "$APK_DIR/index.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Laptop Remote Launcher</title>
    <style>
        body { 
            background: #000; 
            color: #00ff00; 
            font-family: monospace; 
            text-align: center; 
            padding: 50px; 
        }
        .spinner { 
            border: 4px solid #333; 
            border-top: 4px solid #00ff00; 
            border-radius: 50%; 
            width: 40px; 
            height: 40px; 
            animation: spin 2s linear infinite; 
            margin: 20px auto; 
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <h1>🔒 Laptop Remote</h1>
    <div class="spinner"></div>
    <p>Connecting to laptop...</p>
    <p id="status">Enter your laptop's IP address:</p>
    <input type="text" id="ip" placeholder="192.168.1.100" style="background:#111;color:#00ff00;border:1px solid #00ff00;padding:10px;margin:10px;">
    <br>
    <button onclick="connect()" style="background:#00ff00;color:#000;padding:10px 20px;border:none;margin:10px;">Connect</button>
    
    <script>
        function connect() {
            const ip = document.getElementById('ip').value || '192.168.1.100';
            const url = `http://${ip}:8080`;
            document.getElementById('status').textContent = `Connecting to ${url}...`;
            setTimeout(() => {
                window.location.href = url;
            }, 1000);
        }
        
        // Auto-detect common IP ranges
        const commonIPs = ['192.168.1.100', '192.168.0.100', '10.0.0.100'];
        let currentIP = 0;
        
        function tryConnect() {
            if (currentIP < commonIPs.length) {
                document.getElementById('ip').value = commonIPs[currentIP];
                currentIP++;
                setTimeout(tryConnect, 2000);
            }
        }
        
        setTimeout(tryConnect, 3000);
    </script>
</body>
</html>
EOF

    # Use simple method to create APK
    if command -v aapt &> /dev/null; then
        print_status "Building with Android Asset Packaging Tool..."
        # This would require full Android SDK setup
        print_warning "Full Android SDK required for this method"
        return 1
    else
        print_warning "Android build tools not found"
        print_status "Trying alternative method..."
        return 1
    fi
}

# Main execution
main() {
    print_status "Starting APK build and installation process..."
    
    # Check for connected device
    if ! check_device; then
        exit 1
    fi
    
    print_status "Device connected successfully!"
    print_status ""
    print_status "Choose installation method:"
    echo "1) Build with Cordova (recommended)"
    echo "2) Install pre-built web launcher"
    echo "3) Just open browser to web app"
    echo -n "Enter choice [1-3]: "
    read -r choice
    
    case $choice in
        1)
            if build_with_cordova; then
                install_apk "laptop_remote.apk"
            else
                print_error "Cordova build failed"
                exit 1
            fi
            ;;
        2)
            print_status "Creating simple web launcher..."
            # For now, we'll just open the browser
            print_status "Opening browser on your phone..."
            adb shell am start -a android.intent.action.VIEW -d "http://192.168.1.100:8080"
            ;;
        3)
            print_status "Opening web browser..."
            # Get laptop IP
            LAPTOP_IP=$(hostname -I | awk '{print $1}')
            print_status "Opening browser to: http://$LAPTOP_IP:8080"
            adb shell am start -a android.intent.action.VIEW -d "http://$LAPTOP_IP:8080"
            print_success "Browser should open on your phone"
            print_warning "Make sure the mobile server is running:"
            print_warning "python3 start_mobile_server.py"
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
    
    print_success ""
    print_success "🎉 Installation process completed!"
    print_success ""
    print_success "Next steps:"
    print_success "1. Make sure backend server is running: python mobile_backend/server.py"
    print_success "2. Make sure mobile server is running: python start_mobile_server.py"
    print_success "3. Open the app on your phone"
    print_success "4. Enter pairing code from terminal"
}

# Run main function
main "$@"