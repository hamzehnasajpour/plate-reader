# Plate Reader

A Python application that captures video from a USB camera every 2 seconds, detects license plates, and logs detected plate numbers with timestamps.

## Features

- Captures frames from USB camera at 2-second intervals
- Detects and recognizes license plates using OpenALPR
- Confidence-based filtering (only logs plates with >50% confidence)
- Logs results to `plate_log.txt` with timestamp
- Real-time camera feed display (optional)

## Requirements

- Python 3.7+
- USB camera
- OpenALPR library and runtime data

## Installation

### 1. Clone or navigate to the project

```bash
cd /home/hamzeh/dev/plate-reader
```

### 2. Install OpenALPR (system dependency)

**Ubuntu/Debian:**
```bash
sudo apt-get install openalpr openalpr-daemon libopenalpr-dev
```

**macOS:**
```bash
brew install openalpr
```

### 3. Create virtual environment and install Python dependencies

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```bash
python3 main.py
```

The application will:
1. Open your USB camera
2. Capture frames every 2 seconds
3. Analyze for license plates
4. Log detected plates to `plate_log.txt`

Press **'q'** to quit the application.

## Output Format

Detected plates are saved in `plate_log.txt`:

```
Registration Number | Timestamp
==================================================
ABC123D | 2026-05-04 14:23:45
XYZ789K | 2026-05-04 14:24:30
```

## Configuration

Edit `main.py` to adjust:
- `CAMERA_INDEX`: USB camera index (default: 0)
- `CAPTURE_INTERVAL`: Capture frequency in seconds (default: 2)
- `OUTPUT_FILE`: Log file name (default: plate_log.txt)
- Confidence threshold: Line with `confidence > 50`

## Troubleshooting

- **Camera not detected**: Verify USB camera is connected and try changing `CAMERA_INDEX`
- **OpenALPR not found**: Ensure it's installed system-wide
- **No plates detected**: Check camera focus, lighting, and plate visibility
