# License Plate Reader

A lightweight, real-time license plate detection and OCR system optimized for Raspberry Pi using edge detection instead of heavy ML frameworks.

## ✨ Features

- **Real-time Detection** - Scans for plates every 2 seconds (configurable)
- **Mobile-like Zoom** - Crop-based zooming with arrow key navigation  
- **Brightness & Contrast Control** - Live adjustment for various lighting conditions
- **Persistent Settings** - Zoom, brightness, contrast levels saved between sessions
- **Fullscreen Display** - Optimized for both laptops and embedded displays
- **Lightweight** - No PyTorch/YOLO, uses edge detection instead
- **Edge Detection Pipeline** - Canny edges → contour analysis → OCR
- **Local Processing** - All data processed locally, no cloud required
- **Auto-logging** - Detections saved to file with timestamps and confidence scores
- **Image Storage** - Keeps last 50 detected plate images with bounding boxes

## 🚀 Quick Start

### Install Dependencies

**For Raspberry Pi / Debian / Ubuntu:**

```bash
sudo apt update
sudo apt install -y tesseract-ocr python3-pip libsm6 libxext6 libv4l-dev

git clone git@github.com:hamzehnasajpour/plate-reader.git
cd plate-reader
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run

```bash
python3 main_lightweight.py
```

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `s` | Toggle scanning ON/OFF (default: OFF) |
| `+` / `-` | Zoom in / out (1.0x to 5.0x) |
| `1` / `2` | Decrease / increase brightness |
| `3` / `4` | Decrease / increase contrast |
| `↑` `↓` `←` `→` | Move zoom region |
| `q` | Quit & save settings |

## 📊 Detection Pipeline

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
Aspect Ratio Filtering (2:1 to 5:1)
    ↓
Fill Ratio Validation (40% - 95%)
    ↓
Tesseract OCR
    ↓
Text Validation (letters + digits)
    ↓
Log & Save to File
```

## 📋 System Requirements

- **Raspberry Pi 4/5** (ARM64, 4GB+ RAM) OR any Linux desktop
- **USB Camera** with 1080p support (falls back to 640×480)
- **Python 3.7+**
- **Tesseract OCR** engine

## 📁 Project Structure

```
plate-reader/
├── main_lightweight.py          # Main application ⭐
├── debug/
│   ├── view_camera.py          # Standalone camera viewer with zoom
│   ├── find_camera.py          # Camera detection utility
│   ├── extract_regions.py      # Contour extraction debug
│   └── analyze_test_frames_v2.py # Frame analysis tool
├── captured_plates/             # Detected images (auto-created)
├── zoom_config.json            # Settings (auto-created)
├── plate_log.txt               # Detection log (auto-created)
├── requirements.txt
├── README.md                   # This file (quick start)
├── README_FULL.md              # Detailed documentation
└── TROUBLESHOOTING.md          # Debug procedures
```

## 📝 Output & Logging

### Detection Log: `plate_log.txt`

```
Registration Number | Timestamp
==================================================
ABC1234 (95%) | 2026-05-06 22:15:42
XYZ5678 (87%) | 2026-05-06 22:16:13
```

### Detected Images: `captured_plates/`

Auto-saved with bounding box around the plate:
```
captured_plates/
├── 20260506_221542_ABC1234.jpg
├── 20260506_221613_XYZ5678.jpg
└── ...  (keeps last 50 images)
```

### Configuration: `zoom_config.json`

Auto-created on first quit:
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

## 🔧 Configuration

Edit `main_lightweight.py` to adjust detection parameters:

```python
CAPTURE_INTERVAL = 2              # Seconds between detections
CONFIDENCE_THRESHOLD = 0.3        # OCR confidence (0.0-1.0)
MIN_ASPECT_RATIO = 2.0           # Plate width/height ratio
MAX_ASPECT_RATIO = 5.0
MIN_WIDTH = 30                   # Minimum region width (pixels)
MIN_HEIGHT = 10
MIN_TEXT_LENGTH = 6              # Characters in plate
MAX_TEXT_LENGTH = 6
```

## 🐛 Troubleshooting

**Camera not recognized:**
```bash
v4l2-ctl --list-devices
python3 debug/find_camera.py
```

**Tesseract not found:**
```bash
sudo apt install -y tesseract-ocr libtesseract-dev
```

**Poor detection in low light:**
- Press `2` to increase brightness
- Press `4` to increase contrast  
- Use `+` to zoom in on the plate

**Segmentation fault:**
- Check available memory: `free -h`
- Reduce `CAPTURE_INTERVAL` from 2 to 3 seconds
- Lower camera resolution in code

For detailed debugging, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md) or [README_FULL.md](README_FULL.md).

## 📚 Full Documentation

See **[README_FULL.md](README_FULL.md)** for comprehensive documentation including:
- Detailed installation guide
- Complete API reference
- Architecture breakdown
- Performance optimization
- All configuration options
- Code structure

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/hamzehnasajpour/plate-reader/issues)
- **Docs**: [README_FULL.md](README_FULL.md)
- **Troubleshoot**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## 🔗 References

- [OpenCV Docs](https://docs.opencv.org/)
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
- [Raspberry Pi Setup](https://www.raspberrypi.org/documentation/)
- [Canny Edge Detection](https://en.wikipedia.org/wiki/Canny_edge_detector)

## 📄 License

[Add your license here]

## 👤 Author

**Hamzeh Nasajpour** - [GitHub](https://github.com/hamzehnasajpour)

---

**Status**: ✅ Stable & Production-Ready | **Python 3.7+** | **ARM64 Compatible**



