# Plate Reader

A Python application that captures video from a USB camera every 2 seconds, detects license plates using YOLOv8, and logs detected plate numbers with timestamps.

## Features

- **Two detection modes:**
  - **YOLOv8** (main.py): High accuracy, requires powerful CPU
  - **Haar Cascade** (main_lightweight.py): Stable on ARM64, good accuracy
- Captures frames from USB camera at 2-second intervals
- Extracts text from detected plates using Tesseract OCR
- Confidence-based filtering (only logs plates with >50% confidence)
- Logs results to `plate_log.txt` with timestamp
- Optimized for Raspberry Pi and ARM64 systems

## Requirements

- Python 3.7+
- USB camera
- ~2GB available disk space (for model downloads)

## Installation

### 1. Navigate to the project

```bash
cd /home/hamzeh/dev/plate-reader
```

### 2. Run the installation script

```bash
chmod +x install-dep.sh
./install-dep.sh
```

This will:
- Install system dependencies
- Create a Python virtual environment
- Install all Python packages
- Download YOLOv8 pre-trained model

The first run may take 15-30 minutes depending on your internet connection.

## Usage

### Activate the virtual environment

```bash
source venv/bin/activate
```

### Start the plate reader (Lightweight Version - RECOMMENDED)

```bash
python3 main_lightweight.py
```

**Recommended for Raspberry Pi/ARM64 systems.**
- Uses Haar Cascade (built-in to OpenCV)
- Stable and reliable
- Lower memory usage
- Good detection accuracy

### Alternative: Full YOLO Version

```bash
python3 main.py
```

**Requirements:**
- More powerful CPU (not recommended for Raspberry Pi)
- Higher memory usage
- Better accuracy on different plate styles

**Note:** On ARM64 systems like Raspberry Pi, YOLO may cause segmentation faults due to memory constraints. Use `main_lightweight.py` instead.

## Output Format

Detected plates are saved in `plate_log.txt`:

```
Registration Number | Timestamp
==================================================
ABC123D (75.5%) | 2026-05-04 14:23:45
XYZ789K (82.3%) | 2026-05-04 14:24:30
```

## Configuration

Edit `main.py` to adjust:
- `CAMERA_INDEX`: USB camera index (default: 0)
- `CAPTURE_INTERVAL`: Capture frequency in seconds (default: 2)
- `OUTPUT_FILE`: Log file name (default: plate_log.txt)
- `CONFIDENCE_THRESHOLD`: Minimum confidence to log (default: 50%)

## How It Works

1. **YOLOv8 Detection**: Scans each frame for objects that look like license plates
2. **Image Enhancement**: Enhances the detected region for better text recognition
3. **EasyOCR**: Extracts the text from the detected plate
4. **Validation**: Checks if the detected text looks like a valid plate (mix of letters/numbers)
5. **Logging**: Records valid detections with timestamps

## Performance

- **Detection Speed**: ~30-50ms per frame (on ARM64)
- **Memory Usage**: ~500MB with models loaded
- **Accuracy**: Works best with:
  - Well-lit conditions
  - Clear, straight-on plate views
  - Plates at normal distance (not too close/far)

## Troubleshooting

- **Segmentation fault**: Use `main_lightweight.py` instead of `main.py` on ARM64/Raspberry Pi
- **Camera not detected**: Run `python3 find_camera.py` to find your camera index
- **No plates detected**: Improve lighting or move camera closer to plates
- **Memory issues**: Reduce `CAPTURE_INTERVAL` or use lightweight version
- **Tesseract not found**: Install with `sudo apt-get install tesseract-ocr`

