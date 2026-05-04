#!/bin/bash

# License Plate Reader - Remote SSH Streaming Script
# Usage: ./remote_run.sh [remote_host] [remote_user]
# Example: ./remote_run.sh raspberrypi hamzeh

REMOTE_HOST="${1:-localhost}"
REMOTE_USER="${2:-hamzeh}"
LOCAL_PORT=8080
REMOTE_PORT=8080
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "╔════════════════════════════════════════════════════════╗"
echo "║  📷 License Plate Reader - Remote SSH Streaming        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo

# Check if running locally or remotely
if [ "$REMOTE_HOST" = "localhost" ] || [ "$REMOTE_HOST" = "127.0.0.1" ]; then
    echo "📍 Running LOCAL mode..."
    echo
    
    # Check if Flask is installed
    if ! python3 -c "import flask" 2>/dev/null; then
        echo "⚠️  Flask not installed. Installing..."
        pip install flask
    fi
    
    echo "🚀 Starting local web server..."
    cd "$SCRIPT_DIR"
    python3 main_web_stream.py
else
    echo "📍 Running REMOTE mode..."
    echo "   Host: $REMOTE_USER@$REMOTE_HOST"
    echo
    
    # Check if we can SSH to the host
    if ! ssh -o ConnectTimeout=3 "$REMOTE_USER@$REMOTE_HOST" "echo OK" &>/dev/null; then
        echo "❌ Cannot connect to $REMOTE_USER@$REMOTE_HOST"
        echo
        echo "Make sure:"
        echo "  1. SSH key is set up: ssh-copy-id $REMOTE_USER@$REMOTE_HOST"
        echo "  2. Remote host is accessible"
        exit 1
    fi
    
    echo "✓ SSH connection verified"
    echo
    
    # Start remote server in background
    echo "🚀 Starting remote web server..."
    ssh "$REMOTE_USER@$REMOTE_HOST" "cd ~/dev/plate-reader && python3 main_web_stream.py" &
    SSH_PID=$!
    
    echo "   PID: $SSH_PID"
    echo
    
    # Wait for server to start
    sleep 2
    
    # Set up port forwarding
    echo "🔗 Setting up port forwarding (localhost:$LOCAL_PORT → $REMOTE_HOST:$REMOTE_PORT)..."
    
    # Check if port is already in use
    if lsof -Pi :$LOCAL_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  Port $LOCAL_PORT already in use. Killing previous process..."
        kill $(lsof -t -i :$LOCAL_PORT) 2>/dev/null
        sleep 1
    fi
    
    # Create SSH tunnel
    ssh -N -L 127.0.0.1:$LOCAL_PORT:127.0.0.1:$REMOTE_PORT "$REMOTE_USER@$REMOTE_HOST" &
    TUNNEL_PID=$!
    
    echo "   Tunnel PID: $TUNNEL_PID"
    echo
    
    # Wait for tunnel to establish
    sleep 2
    
    # Open browser
    echo "🌐 Opening browser..."
    sleep 1
    
    if command -v xdg-open >/dev/null; then
        xdg-open "http://localhost:$LOCAL_PORT" &
    elif command -v open >/dev/null; then
        open "http://localhost:$LOCAL_PORT" &
    else
        echo "   Please open: http://localhost:$LOCAL_PORT"
    fi
    
    echo
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║  ✓ Stream is live at http://localhost:$LOCAL_PORT     ║"
    echo "╠════════════════════════════════════════════════════════╣"
    echo "║  🎥 Live Camera Feed                                   ║"
    echo "║  📊 Real-time Statistics                               ║"
    echo "║  📝 Detection Logs                                     ║"
    echo "║  🟨 Yellow = All detections                            ║"
    echo "║  🟩 Green = Valid recognized plates                    ║"
    echo "╠════════════════════════════════════════════════════════╣"
    echo "║  Press Ctrl+C to stop                                  ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo
    
    # Wait for user to stop
    wait $SSH_PID
    
    # Cleanup
    echo
    echo "🛑 Stopping..."
    kill $TUNNEL_PID 2>/dev/null
    wait $TUNNEL_PID 2>/dev/null
    
    echo "✓ Done"
fi
