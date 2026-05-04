# Remote SSH Streaming Guide

Stream camera feed from your Raspberry Pi (or any remote machine) and view it in a web browser on your local machine.

## Quick Start

### Option 1: Local Use (Simple)

Run on your local machine:

```bash
./remote_run.sh
```

Opens web browser at `http://localhost:8080` showing live camera feed.

### Option 2: Remote Use (SSH Tunnel)

**First time setup:**

```bash
# Copy SSH key to remote machine (one time)
ssh-copy-id hamzeh@raspberrypi.local

# Or if you have a password
ssh-keygen -t ed25519 -f ~/.ssh/id_plate_reader
ssh-copy-id -i ~/.ssh/id_plate_reader.pub hamzeh@raspberrypi.local
```

**Run every time:**

```bash
./remote_run.sh raspberrypi.local hamzeh
# or
./remote_run.sh 192.168.1.100 hamzeh
```

What happens:
1. ✅ Connects to remote machine via SSH
2. ✅ Starts camera capture & web server on remote
3. ✅ Creates secure SSH tunnel to forward video stream
4. ✅ Opens browser at `http://localhost:8080`
5. ✅ Displays live camera with detections in real-time

## Web Interface

### Dashboard Shows:
- 🎥 **Live Camera Feed** - Real-time MJPEG stream with detection overlays
- 🟨 **Yellow Boxes** - All detected plate-like regions
- 🟩 **Green Boxes** - Valid recognized plates with text
- 📊 **Statistics Panel** - Detection count, last plate recognized, box counts
- 📝 **Log Feed** - Recent detections (scrollable)

### Status Bar:
- `Detection #15 [SCANNING]` - Currently scanning for plates
- `Detection #14 [READY]` - Waiting for next 2-second interval

## How It Works

### Local Mode
```
┌─────────────┐
│   Camera    │
└──────┬──────┘
       │
       ↓
┌──────────────────────────┐
│  main_web_stream.py      │  (runs locally)
│  - Captures frames       │
│  - Detects plates        │
│  - Streams MJPEG         │
│  - Logs to file          │
└──────┬───────────────────┘
       │
       ↓
   :8080 (HTTP)
       │
       ↓
┌──────────────────┐
│  Browser         │
│  localhost:8080  │
└──────────────────┘
```

### Remote SSH Mode
```
Remote Machine (Raspberry Pi)        Your Computer
┌──────────┐                        ┌──────────┐
│ Camera   │                        │ Browser  │
└────┬─────┘                        └────┬─────┘
     │                                   │
     ↓                                   │
┌─────────────────────┐                 │
│ main_web_stream.py  │                 │
│ Port :8080          │◄────SSH───────►(port forward)
│ (internal only)     │                 │
└────────────────────┘          localhost:8080
```

## Troubleshooting

### "Cannot connect to remote host"
```bash
# Verify SSH connection
ssh hamzeh@raspberrypi.local

# If password required, set up SSH keys
ssh-copy-id hamzeh@raspberrypi.local
```

### "Port 8080 already in use"
```bash
# Kill previous process
kill $(lsof -t -i :8080)

# Or use different port - edit remote_run.sh, change LOCAL_PORT
```

### "Flask not installed"
```bash
# Install dependencies
pip install flask

# Or let remote_run.sh install automatically
```

### "Blank camera or no video"
```bash
# Check camera is working
python3 debug/test_frame_save.py

# Check Flask server started
# Look for "Running on http://0.0.0.0:8080"
```

### "Stream stops or lags"
- Network latency might cause delays (normal over SSH)
- Check remote system load: `ssh user@host "top -bn1 | head -20"`
- Consider reducing detection frequency by increasing `CAPTURE_INTERVAL`

## Advanced Usage

### Custom Port
Edit `main_web_stream.py`:
```python
HTTP_PORT = 8080  # Change this line
```

### Disable Auto-Browser Open
Comment out browser opening in `remote_run.sh`:
```bash
# if command -v xdg-open >/dev/null; then
#     xdg-open "http://localhost:$LOCAL_PORT" &
```

### Run on Specific Network Interface
Edit `main_web_stream.py`:
```python
# Instead of 0.0.0.0, use specific IP:
app.run(host='192.168.1.100', port=HTTP_PORT)
```

### Access from Other Machines
If remote camera on `192.168.1.100`:
```bash
# From your laptop/desktop:
http://192.168.1.100:8080
```

## Comparison: Local vs Remote vs Display

| Feature | Local | Remote SSH | Direct Display |
|---------|-------|-----------|---|
| Setup | Easy | Medium | Complex |
| Bandwidth | None | Low (SSH) | Medium (X11) |
| Latency | None | Low | Medium |
| Browser Access | ✓ | ✓ | ✗ |
| Best for | Development | Remote monitoring | Debugging |

## Performance Notes

- **Stream FPS**: ~30 FPS over HTTP (limited by camera + detection)
- **Detection Interval**: 2 seconds (adjustable in config)
- **Network**: Tested over SSH tunnel - works well on local network
- **CPU Usage**: ~40-60% on Raspberry Pi 4
- **Memory**: ~300-400 MB

## Security Notes

⚠️ **Warning**: Default setup exposes HTTP server on the network
- Use SSH tunneling for remote access (included in script)
- Don't expose port 8080 to public internet
- For production, add authentication to Flask app

## Files Used

- `main_web_stream.py` - Web streaming server (Flask-based)
- `remote_run.sh` - SSH tunnel & browser launcher script
- `plate_log.txt` - Detection log (same as other versions)
- `captured_plates/` - Saved images (same as other versions)
