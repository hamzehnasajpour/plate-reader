# Troubleshooting - Images Not Being Saved

If images aren't being saved to `captured_plates/`, follow these steps:

## Step 1: Test Basic Frame Capture & Save
First, verify the camera and save mechanism work:

```bash
python3 test_frame_save.py
```

This will save raw frames every 2 seconds to `test_frames/` directory.

**Expected output:**
```
[14:23:45] Saved: test_frames/frame_001_20260504_142345.jpg (691200 bytes)
[14:23:47] Saved: test_frames/frame_002_20260504_142347.jpg (691200 bytes)
```

**If this works:** The camera and save mechanism are fine. Problem is with detection.
**If this fails:** Camera or save permissions issue.

---

## Step 2: Debug Detection
Run the debug version to see what regions are being detected:

```bash
python3 debug_detection.py
```

This saves ALL detected regions (not just valid plates) to `captured_plates_debug/`.

**Expected output:**
```
[14:23:45] Detection #1: Found 5 regions
  Saved: captured_plates_debug/0001_crop_00_ratio2.34.jpg
  Saved: captured_plates_debug/0001_crop_01_ratio1.89.jpg
  Saved: captured_plates_debug/0001_full_frame.jpg
```

**If found 0 regions:** Cascade isn't detecting plate-like objects
**If found regions:** Check if they look like plates (open the JPG files)

---

## Step 3: Check Detection Filters
If debug version finds many regions but main version doesn't save:

**Current filters in main_lightweight.py:**
- Ratio: 1.5 to 6 (width/height ratio)
- Minimum width: 30 pixels
- Minimum height: 10 pixels
- OCR confidence: 30% or higher

Try making these more permissive:

```python
# In main_lightweight.py, line with "if 1.5 < ratio < 6"
# Change to (more lenient):
if 1.0 < ratio < 8 and w > 20 and h > 8:
```

---

## Step 4: Manual Plate Testing
If debug detects regions but OCR fails:

1. Copy an image from `captured_plates_debug/` 
2. Place your license plate in front of camera
3. Verify in debug version that it detects it

---

## Common Issues

**No detections found:**
- Cascade detector is for faces, not optimized for plates
- Camera quality/angle might not work well with face cascade
- Try moving camera closer to objects

**Detections found but not saved:**
- OCR confidence below 30%
- Detected text doesn't have both letters AND numbers
- Text too short (less than 3 characters)

**Issue persists:**
- Check file permissions: `ls -la captured_plates/`
- Check disk space: `df -h`
- Run: `python3 -m pytesseract --help` to verify Tesseract works

