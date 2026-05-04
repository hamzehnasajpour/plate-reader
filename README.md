# Plate Reader

A Python application that captures video from a USB camera every 2 seconds, detects license plates using edge detection, and logs detected plate numbers with timestamps.

## Features

- Captures frames from USB camera at 2-second intervals
- **Edge detection + contour analysis** - Rectangle detection optimized for license plates
- Extracts text from detected plates using Tesseract OCR
- Logs results to `plate_log.txt` with timestamp and confidence
- **Rotating image storage** - Keeps last 5 detected plate images in `captured_plates/`
- Optimized for Raspberry Pi and ARM64 systems

## Requirements

- Python 3.7+
- USB camera
- Tesseract OCR (installed via `install-dep.sh`)

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

This will install system dependencies and Python packages.

## Usage

### Activate the virtual environment

```bash
source venv/bin/activate
```

### Start the plate reader

```bash
python3 main_lightweight.py
```

This will:
- Continuously capture frames from your USB camera
- Detect license plates using edge detection
- Log recognized plates to `plate_log.txt`
- Save detected frames to `captured_plates/` (rotating, keeps last 5)

## Output Format

Detected plates are saved in `plate_log.txt`:

```
Registration Number | Timestamp
==================================================
AAA000 (90.0%) | 2026-05-04 21:39:07
IGAAA000 (100.0%) | 2026-05-04 21:39:14
```

### Captured Images

When a plate is detected, the frame is automatically saved:

```
captured_plates/
├── plate_001.jpg  (most recent)
├── plate_002.jpg
├── plate_003.jpg
├── plate_004.jpg
└── plate_005.jpg  (oldest, deleted when new one added)
```

## Configuration

Edit `main_lightweight.py` to adjust:
- `CAMERA_INDEX`: USB camera index (default: 0)
- `CAPTURE_INTERVAL`: Capture frequency in seconds (default: 2)
- `CONFIDENCE_THRESHOLD`: Minimum confidence to log (default: 0.3 = 30%)
- `OUTPUT_FILE`: Log file name (default: plate_log.txt)

## How It Works

1. **Frame Capture**: Grab frames from USB camera every 2 seconds
2. **Edge Detection**: Find object boundaries using Canny edge detection
3. **Contour Analysis**: Find rectangular regions matching license plate proportions
4. **Region Filtering**: Keep only rectangles with aspect ratio 2-5x (width/height)
5. **Image Enhancement**: Apply CLAHE contrast + adaptive threshold + upscaling
6. **OCR Extraction**: Use Tesseract to read text from enhanced regions
7. **Validation**: Check for both letters and digits to confirm valid plate
8. **Logging & Storage**: Record to `plate_log.txt` and save frame to `captured_plates/`

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed debug procedures.

### Quick Debug Commands

```bash
# Test camera and save mechanism
python3 debug/test_frame_save.py

# Find available USB cameras
python3 debug/find_camera.py

# Test detection on saved frames
python3 debug/analyze_test_frames_v2.py

# Visualize detected regions
python3 debug/extract_regions.py
```

### Common Issues

- **No plates detected**: Check camera angle, lighting, and plate distance
- **Camera not found**: Run `python3 debug/find_camera.py`
- **Tesseract error**: Install with `sudo apt-get install tesseract-ocr`
- **Memory issues**: Reduce `CAPTURE_INTERVAL` or check `free -h`

## Project Structure

```
plate-reader/
├── main_lightweight.py       # Main app (recommended)
├── main.py                   # Full version (YOLOv8 - not recommended for ARM64)
├── plate_log.txt             # Output log
├── captured_plates/          # Detected plate images (rotating, last 5)
├── test_frames/              # Test frames from camera
├── debug/                    # Debug and analysis scripts
│   ├── test_frame_save.py
│   ├── find_camera.py
│   ├── analyze_test_frames_v2.py
│   └── extract_regions.py
└── requirements.txt          # Python dependencies
```

