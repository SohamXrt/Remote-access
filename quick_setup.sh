#!/bin/bash
# One-step setup for the entire laptop remote access system

echo "🔒 Laptop Remote Access - Quick Setup"
echo "===================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

# Get local IP
get_local_ip() {
    hostname -I | awk '{print $1}'
}

print_step "1. Starting Backend Server..."
# Start backend server in background
source venv/bin/activate
nohup python mobile_backend/server.py > backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > backend.pid

sleep 3

# Check if backend started
if curl -s http://localhost:8000/ > /dev/null; then
    print_success "Backend server started (PID: $BACKEND_PID)"
else
    echo "❌ Backend server failed to start"
    exit 1
fi

print_step "2. Starting Mobile Web Server..."
# Start mobile server in background
nohup python3 start_mobile_server.py > mobile.log 2>&1 &
MOBILE_PID=$!
echo $MOBILE_PID > mobile.pid

sleep 2

LOCAL_IP=$(get_local_ip)

print_success "Mobile server started (PID: $MOBILE_PID)"
print_success "Servers are running!"

echo ""
echo "📋 Connection Details:"
echo "================================"
echo "Backend API: http://localhost:8000"
echo "Mobile App:  http://$LOCAL_IP:8080"
echo "Local Test:  http://localhost:8080"
echo ""

print_step "3. Phone Setup Options:"
echo ""
echo "Option A: Connect phone via USB (Recommended)"
echo "  1. Enable USB Debugging on your phone"
echo "  2. Connect phone via USB"
echo "  3. Run: ./install_to_phone.sh"
echo ""
echo "Option B: Connect via WiFi"
echo "  1. Make sure phone is on same WiFi"
echo "  2. Open browser on phone"
echo "  3. Go to: http://$LOCAL_IP:8080"
echo "  4. Add to home screen for app experience"
echo ""

print_step "4. Testing the System:"
echo ""
echo "Terminal Demo:"
echo "  python terminal_client/auth_client.py --demo"
echo ""
echo "Authentication Test:"
echo "  python terminal_client/auth_terminal.py"
echo ""

print_step "5. Stopping the System:"
echo ""
echo "To stop all servers:"
echo "  ./stop_servers.sh"
echo ""

# Create stop script
cat > stop_servers.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping Laptop Remote Access servers..."

if [ -f backend.pid ]; then
    BACKEND_PID=$(cat backend.pid)
    kill $BACKEND_PID 2>/dev/null
    rm backend.pid
    echo "✅ Backend server stopped"
fi

if [ -f mobile.pid ]; then
    MOBILE_PID=$(cat mobile.pid)
    kill $MOBILE_PID 2>/dev/null
    rm mobile.pid
    echo "✅ Mobile server stopped"
fi

# Also kill any python servers running on our ports
pkill -f "mobile_backend/server.py" 2>/dev/null
pkill -f "start_mobile_server.py" 2>/dev/null
pkill -f "python3 -m http.server 8080" 2>/dev/null

echo "🏁 All servers stopped"
EOF

chmod +x stop_servers.sh

print_success "Quick setup completed!"
print_info "Check backend.log and mobile.log for server logs"

echo ""
echo "🎉 System is ready! Choose your next step:"
echo "  • USB Install: ./install_to_phone.sh"
echo "  • WiFi Access: Open http://$LOCAL_IP:8080 on phone"
echo "  • Test Demo:   python terminal_client/auth_client.py --demo"
echo "  • Stop All:    ./stop_servers.sh"
echo ""
echo "📱 For phone access, the mobile app will be at:"
echo "   http://$LOCAL_IP:8080"