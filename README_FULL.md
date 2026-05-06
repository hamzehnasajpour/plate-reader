# License Plate Reader - Edge Detection Based

A lightweight, real-time license plate detection and OCR system designed for ARM64 Raspberry Pi. Uses edge detection and contour analysis instead of heavy ML frameworks to ensure reliable operation on resource-constrained devices.

## 🎯 Project Overview

This project implements a two-stage license plate detection pipeline:
1. **Stage 1**: Edge detection using Canny edge detection to identify plate-like regions
2. **Stage 2**: Contour analysis with aspect ratio filtering to isolate license plates
3. **Stage 3**: Tesseract OCR for text extraction and recognition

The system is optimized for nighttime and parking lot scenarios with adjustable brightness and contrast controls.

## ✨ Key Features

- **Real-time Detection**: Scans for license plates every 2 seconds (configurable)
- **Mobile-like Zoom**: Crop-based zooming with arrow key navigation
- **Brightness & Contrast Adjustment**: Live controls for handling overexposed/underexposed scenes
- **Persistent Settings**: Zoom level, position, brightness, and contrast saved between sessions
- **Fullscreen Display**: Optimized for both laptop and embedded displays
- **Lightweight**: No heavy ML frameworks, perfect for Raspberry Pi
- **Configuration Auto-save**: All settings persist in JSON config file
- **Real-time Telemetry**: Live display of resolution, zoom level, detection status

## 🏗️ Architecture

### Detection Pipeline

```
Camera Frame
    ↓
Bilateral Filter (noise reduction)
    ↓
Canny Edge Detection
    ↓
Morphological Dilation
    ↓
Contour Detection
    ↓
Aspect Ratio Filtering (2.0 - 5.0)
    ↓
Fill Ratio Validation (0.4 - 0.95)
    ↓
Tesseract OCR
    ↓
Text Validation & Logging
```

### File Structure

```
plate-reader/
├── main_lightweight.py          # Main application with full GUI
├── debug/
│   ├── view_camera.py          # Standalone camera viewer with zoom
│   ├── find_camera.py          # Camera detection utility
│   ├── extract_regions.py      # Contour extraction debug tool
│   └── analyze_test_frames_v2.py # Frame analysis utility
├── captured_plates/            # Detected plate images (auto-created)
├── zoom_config.json           # Persistent config file
├── plate_log.txt              # Detection log
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 📋 System Requirements

### Hardware
- **Primary**: Raspberry Pi 4/5 (64-bit ARM, 4GB+ RAM recommended)
- **Alternative**: Any Linux system with USB camera support
- **Camera**: USB camera with 1080p support (auto-fallback to 640×480)

### Software
- Python 3.7+
- OpenCV 4.8.1+
- PyTesseract 0.3.10+
- Tesseract OCR engine

## 🔧 Installation & Setup

### 1. Clone Repository

```bash
cd /home/hamzeh/dev  # Or your preferred directory
git clone git@github.com:hamzehnasajpour/plate-reader.git
cd plate-reader
```

### 2. Install System Dependencies

**On Raspberry Pi (Debian/Ubuntu):**

```bash
# Update package manager
sudo apt update && sudo apt upgrade -y

# Install Tesseract OCR
sudo apt install -y tesseract-ocr libtesseract-dev

# Install OpenCV dependencies
sudo apt install -y python3-dev python3-pip
sudo apt install -y libatlas-base-dev libjasper-dev libtiff5-dev zlib1g-dev
sudo apt install -y libjasper-dev libtiff5-dev libjasper1 libjasper-dev
sudo apt install -y libharfbuzz0b libwebp6 libtiff5 libjasper1

# Install video4linux for camera
sudo apt install -y libv4l-dev v4l-utils

# Verify camera detection
v4l2-ctl --list-devices
```

**On Ubuntu/Debian (Desktop):**

```bash
sudo apt update
sudo apt install -y tesseract-ocr python3-dev python3-pip libsm6 libxext6
```

### 3. Create Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # Linux/Mac
# OR
.\venv\Scripts\activate  # Windows
```

### 4. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**requirements.txt contents:**
```
opencv-python==4.8.1.78
pytesseract==0.3.10
numpy>=1.21.0
```

### 5. Verify Installation

```bash
# Test Python imports
python3 -c "import cv2, pytesseract, numpy; print('✓ All imports OK')"

# Test Tesseract
tesseract --version

# Test camera
python3 debug/find_camera.py
```

## 🚀 Running the Application

### Main Application

```bash
# Activate virtual environment
source venv/bin/activate

# Run the main application
python3 main_lightweight.py

# Press 'q' to quit (settings auto-save)
```

### Camera Viewer (Debug Mode)

```bash
python3 debug/view_camera.py
```

### Using Shell Scripts

```bash
# Make scripts executable
chmod +x run.sh view_camera.sh

# Run main app
./run.sh

# View camera
./view_camera.sh
```

## ⌨️ Keyboard Controls

### Scanning
- **`s`** - Toggle scanning ON/OFF (default: OFF)
- When OFF: Camera displays live feed, no detection runs
- When ON: Detection runs every 2 seconds

### Navigation & Zoom
- **`↑` / `↓` / `←` / `→`** - Move zoom region
- **`+` / `-`** - Zoom in/out (range: 1.0x to 5.0x)

### Image Adjustment
- **`1` / `2`** - Decrease/increase brightness (-100 to +100)
- **`3` / `4`** - Decrease/increase contrast (-100 to +100)

### Exit
- **`q`** - Quit (saves all settings + zoom config)

### Shortcut Display
Press any key to see all available shortcuts in the status bar (top of screen)

## 📊 Status Bar Information

The live display shows:
```
Detection #42 [SCANNING] | Scan: ✓ ON
Res: 1920×1080 | Zoom: 2.5x | Scope: 768×432
Brightness: +15 | Contrast: -10
[S]can [+/-]Zoom [1/2]Light [3/4]Contrast [↑↓←→]Move [Q]uit
```

- **Detection #N**: Current detection cycle count
- **[SCANNING]**: Currently processing frame
- **Scan: ✓ ON/✗ OFF**: Scanning enabled/disabled
- **Res**: Camera resolution (actual captured size)
- **Zoom**: Current zoom level
- **Scope**: Size of visible area in pixels
- **Brightness/Contrast**: Current adjustment levels

## 🔧 Configuration

### Config File: `zoom_config.json`

Auto-created on first quit. Stores:

```json
{
  "width": 1920,
  "height": 1080,
  "zoom_level": 2.5,
  "zoom_region_x": 576,
  "zoom_region_y": 324,
  "brightness_adjust": 0,
  "contrast_adjust": 0
}
```

**Auto-loads** if camera resolution matches previous session.

### Detection Parameters (in code)

Modify in `main_lightweight.py`:

```python
CAPTURE_INTERVAL = 2              # Seconds between detections
CONFIDENCE_THRESHOLD = 0.3        # OCR confidence (0.0-1.0)
MIN_ASPECT_RATIO = 2.0           # Plate width/height min
MAX_ASPECT_RATIO = 5.0           # Plate width/height max
MIN_WIDTH = 30                   # Minimum region width (pixels)
MIN_HEIGHT = 10                  # Minimum region height (pixels)
MIN_FILL_RATIO = 0.4             # Contour fill percentage
MAX_FILL_RATIO = 0.95            # Maximum fill percentage
MIN_TEXT_LENGTH = 6              # Minimum plate characters
MAX_TEXT_LENGTH = 6              # Maximum plate characters
```

## 📝 Output & Logging

### Detection Log: `plate_log.txt`

```
Registration Number | Timestamp
==================================================
ABC1234 (95%) | 2026-05-06 22:15:42
XYZ5678 (87%) | 2026-05-06 22:16:13
```

### Captured Plate Images: `captured_plates/`

Auto-saved with bounding box:
```
captured_plates/
├── 20260506_221542_ABC1234.jpg
├── 20260506_221613_XYZ5678.jpg
└── ... (keeps last 50 images)
```

## 🐛 Debugging

### Enable Debug Output

```bash
# Run with debug output
python3 main_lightweight.py 2>&1 | tee debug.log

# View detection in real-time
tail -f debug.log
```

### Common Issues

#### 1. Camera Not Found
```bash
# Check camera
v4l2-ctl --list-devices
ls -la /dev/video*

# Try alternate camera index in code:
CAMERA_INDEX = 0  # Try 0, 1, 2, etc.
```

#### 2. Tesseract Not Found
```bash
# Verify installation
which tesseract
tesseract --version

# Set path if needed (Linux)
export TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata
```

#### 3. OpenCV Build Issues
```bash
# If pip install fails, try:
pip install opencv-python-headless  # Server version
# OR
pip install opencv-contrib-python   # Full version with extras
```

#### 4. Segmentation Fault
If you see segfaults:
- Disable YOLO/PyTorch (already done in this version)
- Check memory: `free -h`
- Reduce resolution or CAPTURE_INTERVAL

#### 5. Poor Detection

**Adjust detection parameters:**
```python
MIN_ASPECT_RATIO = 1.5     # More permissive
MAX_ASPECT_RATIO = 6.0     # Allow wider plates
MIN_FILL_RATIO = 0.3       # Accept less "filled" regions
```

**Use brightness/contrast controls:**
- Press `1` to darken overexposed areas
- Press `4` to increase contrast for better edges

## 💡 Performance Tips

### For Raspberry Pi

```python
# Reduce detection frequency (in main_lightweight.py)
CAPTURE_INTERVAL = 3  # Check every 3 seconds instead of 2

# Reduce resolution for faster processing
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)   # 1280 instead of 1920
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)   # 720 instead of 1080

# Reduce OCR timeout
config = '--psm 8 --oem 3 -c tessedit_char_whitelist=... timeout=1'  # 1 second
```

### Memory Optimization

```python
# Reduce stored images buffer
MAX_STORED_IMAGES = 25  # Instead of 50

# Disable image saving if not needed
# Comment out: cv2.imwrite(image_filename, frame_with_box)
```

## 🏗️ Code Architecture

### Main Functions

**Detection Pipeline:**
- `detect_plate_contours()` - Edge detection → contour analysis
- `extract_plate_text(frame, rect)` - OCR on detected region
- `is_likely_plate(text)` - Validation (letters + digits)

**UI & Display:**
- `draw_ui_overlay(frame, ...)` - Draw detection boxes
- `draw_status_overlay(display_frame, ...)` - Status bar with shortcuts
- `apply_brightness_contrast(frame, ...)` - Real-time adjustment

**Config & Persistence:**
- `load_config()` - Load zoom settings from JSON
- `save_config(...)` - Save settings on exit

**Utilities:**
- `log_plate(plate_number, ...)` - Log to file + save image
- `cleanup_old_images()` - Maintain 50-image buffer

### Key Classes/Objects

- **cap**: OpenCV VideoCapture instance
- **zoom_region_x, zoom_region_y**: Crop position
- **zoom_level**: Magnification factor (1.0 = no zoom)
- **brightness_adjust, contrast_adjust**: -100 to +100 range
- **scanning_enabled**: Boolean toggle for detection
- **detected_rectangles**: List of candidate regions (yellow boxes)
- **valid_plates**: List of OCR-confirmed plates (green boxes)

## 📈 Future Improvements

- [ ] Multi-camera support
- [ ] GPU acceleration (if available)
- [ ] Real-time database logging
- [ ] Plate format validation (country-specific)
- [ ] Deep learning fallback for difficult scenarios
- [ ] Web dashboard for remote viewing
- [ ] Performance profiling and benchmarking
- [ ] Unit tests and CI/CD pipeline

## 🔐 Security Considerations

- **Local Processing**: All data processed locally, never sent to cloud
- **Image Storage**: Detected plates stored in `captured_plates/`, user editable
- **Config File**: `zoom_config.json` contains only UI settings
- **Logs**: `plate_log.txt` contains only detected plate numbers and timestamps

## 📄 License

[Add your license here - e.g., MIT, GPL, etc.]

## 👤 Author

- **Hamzeh Nasajpour** - [GitHub](https://github.com/hamzehnasajpour)

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Commit changes (`git commit -m 'Add improvement'`)
4. Push to branch (`git push origin feature/improvement`)
5. Open a Pull Request

## 📞 Support & Issues

For bugs, features, or questions:
- Create an [Issue](https://github.com/hamzehnasajpour/plate-reader/issues)
- Check existing issues first
- Include: OS, Python version, error messages, camera model

## 📚 References

- [OpenCV Documentation](https://docs.opencv.org/)
- [PyTesseract GitHub](https://github.com/madmaze/pytesseract)
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
- [Raspberry Pi Documentation](https://www.raspberrypi.org/documentation/)
- [Edge Detection (Canny Algorithm)](https://en.wikipedia.org/wiki/Canny_edge_detector)

## 💾 Version History

### v1.2.0 (Current)
- ✅ Added brightness/contrast adjustments
- ✅ Improved shortcut visibility
- ✅ Fixed scan toggle behavior
- ✅ Added fullscreen mode
- ✅ Configuration persistence

### v1.1.0
- ✅ Mobile-like zoom with arrow keys
- ✅ Zoom settings persistence
- ✅ Real-time telemetry display

### v1.0.0
- ✅ Initial release with edge detection
- ✅ Basic OCR integration
- ✅ Detection logging

---

**Last Updated**: May 6, 2026  
**Status**: Stable & Production-Ready
