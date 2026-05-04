# Troubleshooting & Debug Scripts

## Quick Reference - Debug Scripts

| Script | Goal | Command |
|--------|------|---------|
| **test_frame_save.py** | Verify camera & save mechanism | `python3 debug/test_frame_save.py` |
| **find_camera.py** | Check available USB cameras | `python3 debug/find_camera.py` |
| **analyze_test_frames_v2.py** | Test plate detection on saved frames | `python3 debug/analyze_test_frames_v2.py` |
| **extract_regions.py** | Visualize detected plate regions | `python3 debug/extract_regions.py` |

---

## Workflow: Troubleshooting Plate Detection

### Issue: No plates being detected or saved

**Step 1: Verify Camera Works**
```bash
python3 debug/test_frame_save.py
```
- Captures 5 frames and saves to `test_frames/`
- **Keywords:** camera, USB, frame capture, save mechanism
- **If fails:** Camera not accessible or permissions issue

**Step 2: Check Available Cameras**
```bash
python3 debug/find_camera.py
```
- Lists all USB cameras and resolutions
- **Keywords:** camera detection, device index, USB device
- **If no cameras:** Check USB connection

**Step 3: Test Detection on Saved Frames**
```bash
python3 debug/analyze_test_frames_v2.py
```
- Runs full detection + OCR pipeline on frames from `test_frames/`
- Shows detected regions and extracted text
- **Keywords:** plate detection, edge detection, OCR test, debug detection
- **If detects:** Detection pipeline working, issue is live capture
- **If doesn't detect:** Adjust filters or camera angle

**Step 4: Visualize Detected Regions**
```bash
python3 debug/extract_regions.py
```
- Extracts and saves all detected plate regions for visual inspection
- Saves both raw and enhanced versions to `extracted_plate_regions/`
- **Keywords:** visualization, region extraction, verify detections
- **If regions look wrong:** Detection filters need adjustment

---

## Common Issues & Solutions

### 1. No plates detected
```
Solution: Check camera angle, lighting, plate distance
- Run: python3 debug/test_frame_save.py
- Look at test_frames/ to see what camera sees
- Move camera closer to plate (3-6 inches optimal)
```

### 2. Detections found but text not recognized
```
Solution: OCR needs better preprocessing
- Check extracted_plate_regions/ for visual inspection
- If text visible but unrecognized:
  - Adjust contrast: CLAHE clipLimit in main_lightweight.py
  - Adjust threshold: Try 100-160 range in adaptive threshold
  - Increase upscaling: Change scale=max(5,...) to max(6,...)
```

### 3. Too many false positives
```
Solution: Tighten detection filters
- Edit main_lightweight.py, find_plate_regions() function
- Increase aspect ratio lower bound (currently 2.0): try 2.5
- Increase minimum size: min_w from 30 to 50
- Increase fill_ratio lower bound from 0.4 to 0.5
```

### 4. Camera freeze or slow performance
```
Solution: Check system load
- Keywords: CPU, memory, Raspberry Pi performance
- Run: free -h (check RAM)
- Run: top (check CPU usage)
- Consider reducing frame resolution: change (640, 480) to (320, 240)
```

---

## Running Main Application

```bash
# Start plate reader (detects AAA000 format plates)
python3 main_lightweight.py

# View detected registrations
tail plate_log.txt

# Check last 5 captured plate images
ls -lht captured_plates/ | head -5
```

