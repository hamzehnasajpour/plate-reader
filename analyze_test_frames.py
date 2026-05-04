#!/usr/bin/env python3
"""
Analyze saved test frames for license plate detection
Tests if cascade detector and OCR work on the captured images
"""

import cv2
import os
from pathlib import Path
from datetime import datetime

try:
    import pytesseract
except ImportError:
    print("Warning: pytesseract not installed, OCR will be skipped")
    pytesseract = None

# Configuration
TEST_DIR = "test_frames"
OUTPUT_DIR = "plate_analysis"
CASCADE_PATH = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'

# Create output directory
Path(OUTPUT_DIR).mkdir(exist_ok=True)

# Load cascade
cascade = cv2.CascadeClassifier(CASCADE_PATH)
if cascade.empty():
    print("Error: Could not load Haar Cascade classifier")
    exit(1)

print("✓ Haar Cascade classifier loaded")

# Get all JPG files
test_files = sorted(Path(TEST_DIR).glob("*.jpg"))
if not test_files:
    print(f"No JPG files found in {TEST_DIR}/")
    exit(1)

print(f"Found {len(test_files)} test images\n")
print("=" * 70)

total_detections = 0
successful_ocr = 0

for img_path in test_files:
    print(f"\nAnalyzing: {img_path.name}")
    print("-" * 70)
    
    # Read image
    frame = cv2.imread(str(img_path))
    if frame is None:
        print("  Error: Could not read image")
        continue
    
    height, width = frame.shape[:2]
    print(f"  Image size: {width}x{height}")
    
    # Convert to grayscale for detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detect objects
    rects = cascade.detectMultiScale(gray, 1.3, 5)
    print(f"  Detections found: {len(rects)}")
    
    if len(rects) == 0:
        print("  ⚠ No regions detected - plate might not look like a face to cascade")
        continue
    
    total_detections += len(rects)
    
    # Create marked-up copy
    marked_frame = frame.copy()
    
    # Analyze each detection
    for i, (x, y, w, h) in enumerate(rects):
        ratio = w / h if h > 0 else 0
        is_plate_like = 1.5 < ratio < 6 and w > 30 and h > 10
        
        print(f"\n  Region {i+1}:")
        print(f"    Position: x={x}, y={y}")
        print(f"    Size: {w}x{h} (ratio: {ratio:.2f})")
        print(f"    Plate-like: {'✓' if is_plate_like else '✗'}")
        
        # Draw bounding box
        color = (0, 255, 0) if is_plate_like else (0, 0, 255)
        cv2.rectangle(marked_frame, (x, y), (x + w, y + h), color, 2)
        cv2.putText(marked_frame, f"R:{ratio:.2f}", (x, y - 10), 
                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Extract region for OCR
        if is_plate_like and pytesseract:
            crop = frame[y:y+h, x:x+w]
            
            # Enhance for OCR
            gray_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray_crop, 150, 255, cv2.THRESH_BINARY)
            upscaled = cv2.resize(binary, (0, 0), fx=2, fy=2)
            
            # Try OCR
            try:
                config = '--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                text = pytesseract.image_to_string(upscaled, config=config, timeout=5).strip().upper()
                
                if text:
                    has_letters = any(c.isalpha() for c in text)
                    has_digits = any(c.isdigit() for c in text)
                    is_valid = has_letters and has_digits and len(text) >= 3
                    
                    print(f"    OCR Text: '{text}'")
                    print(f"    Valid plate: {'✓' if is_valid else '✗'} (letters:{has_letters}, digits:{has_digits}, len:{len(text)})")
                    
                    if is_valid:
                        successful_ocr += 1
                        # Label as successful
                        cv2.putText(marked_frame, f"PLATE: {text}", (x, y + h + 25), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                else:
                    print(f"    OCR: No text detected")
            except Exception as e:
                print(f"    OCR Error: {e}")
    
    # Save marked image
    output_path = Path(OUTPUT_DIR) / f"analyzed_{img_path.name}"
    cv2.imwrite(str(output_path), marked_frame)
    print(f"\n  ✓ Saved analysis: {output_path.name}")

print("\n" + "=" * 70)
print("SUMMARY:")
print(f"  Images tested: {len(test_files)}")
print(f"  Total detections: {total_detections}")
print(f"  Successful OCR results: {successful_ocr}")

if successful_ocr > 0:
    print(f"\n✓ SUCCESS! System detected and recognized {successful_ocr} plate(s)")
    print(f"  Check {OUTPUT_DIR}/ for marked-up images")
elif total_detections > 0:
    print(f"\n⚠ Detections found but OCR failed - check image quality/angle")
    print(f"  Check {OUTPUT_DIR}/ for marked-up images with detected regions")
else:
    print(f"\n✗ No plate-like regions detected by cascade")
    print(f"  Possible solutions:")
    print(f"    - Try different camera angle")
    print(f"    - Move camera closer to plate")
    print(f"    - Improve lighting")
    print(f"    - Different cascade classifier might work better")

print(f"\nAnalyzed images saved to: {OUTPUT_DIR}/")
