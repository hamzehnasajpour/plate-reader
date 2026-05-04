#!/usr/bin/env python3
"""
License Plate Detector using Contour/Edge Detection
Better than Haar Cascade for detecting rectangular license plates
"""

import cv2
import os
from pathlib import Path
import numpy as np

try:
    import pytesseract
except ImportError:
    print("Warning: pytesseract not installed")
    pytesseract = None

# Configuration
TEST_DIR = "test_frames"
OUTPUT_DIR = "plate_analysis_v2"

Path(OUTPUT_DIR).mkdir(exist_ok=True)

print("✓ Starting plate detection via edge detection")

def detect_plate_regions(frame):
    """Detect potential license plate regions using edge detection."""
    
    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Apply bilateral filter to reduce noise while keeping edges
    gray = cv2.bilateralFilter(gray, 11, 17, 17)
    
    # Edge detection
    edges = cv2.Canny(gray, 30, 200)
    
    # Dilate to connect nearby edges
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    edges = cv2.dilate(edges, kernel, iterations=3)
    
    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    plate_regions = []
    
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        
        # Filter by dimensions
        if w < 20 or h < 10:
            continue
        
        ratio = w / h if h > 0 else 0
        
        # License plates are typically 3-5 times wider than tall
        if 2 < ratio < 6:
            # Check if mostly empty (low fill ratio means not solid)
            area = w * h
            contour_area = cv2.contourArea(contour)
            fill_ratio = contour_area / area if area > 0 else 0
            
            # Good plates have moderate fill (edges outlined rectangle)
            if 0.4 < fill_ratio < 0.95:
                plate_regions.append((x, y, w, h, ratio, fill_ratio))
    
    return plate_regions


def extract_and_recognize(frame, x, y, w, h):
    """Extract plate region and run OCR."""
    if pytesseract is None:
        return None, 0
    
    try:
        crop = frame[y:y+h, x:x+w]
        
        # Enhance for OCR - more aggressive preprocessing
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        
        # Improve contrast with CLAHE
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        
        # Threshold
        _, binary = cv2.threshold(gray, 140, 255, cv2.THRESH_BINARY)
        
        # Upscale aggressively for small regions
        scale = max(4, int(300 / max(w, h)))  # Scale to make text ~300px wide
        upscaled = cv2.resize(binary, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        # Denoise
        upscaled = cv2.fastNlMeansDenoising(upscaled, h=10)
        
        # OCR with multiple PSM modes (try different if first fails)
        config_modes = [
            '--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
            '--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
            '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
        ]
        
        for config in config_modes:
            text = pytesseract.image_to_string(upscaled, config=config, timeout=5).strip().upper()
            
            if text and len(text) >= 3:
                has_letters = any(c.isalpha() for c in text)
                has_digits = any(c.isdigit() for c in text)
                
                if has_letters and has_digits:
                    confidence = min(100, len(text) * 12)
                    return text, confidence
    except Exception as e:
        pass
    
    return None, 0


# Get all test images
test_files = sorted(Path(TEST_DIR).glob("*.jpg"))
if not test_files:
    print(f"No JPG files found in {TEST_DIR}/")
    exit(1)

print(f"Found {len(test_files)} test images\n")
print("=" * 70)

total_regions = 0
successful_plates = 0

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
    
    # Detect plate regions
    regions = detect_plate_regions(frame)
    print(f"  Plate-like regions found: {len(regions)}")
    
    if len(regions) == 0:
        print("  ⚠ No rectangular regions detected")
        continue
    
    total_regions += len(regions)
    
    # Create marked-up image
    marked_frame = frame.copy()
    
    # Analyze each region
    for i, (x, y, w, h, ratio, fill) in enumerate(regions):
        print(f"\n  Region {i+1}:")
        print(f"    Position: x={x}, y={y}")
        print(f"    Size: {w}x{h} (ratio: {ratio:.2f}, fill: {fill:.2%})")
        
        # Try OCR
        text, conf = extract_and_recognize(frame, x, y, w, h)
        
        if text:
            print(f"    OCR: '{text}' ({conf:.0f}% confidence)")
            color = (0, 255, 0)  # Green for successful
            successful_plates += 1
            cv2.rectangle(marked_frame, (x, y), (x + w, y + h), color, 3)
            cv2.putText(marked_frame, f"PLATE: {text}", (x, y - 10), 
                      cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        else:
            print(f"    OCR: Failed to extract text")
            color = (0, 165, 255)  # Orange for detected but not recognized
            cv2.rectangle(marked_frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(marked_frame, f"R:{ratio:.2f}", (x, y - 10), 
                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    # Save marked image
    output_path = Path(OUTPUT_DIR) / f"analyzed_{img_path.name}"
    cv2.imwrite(str(output_path), marked_frame)
    print(f"\n  ✓ Saved: {output_path.name}")

print("\n" + "=" * 70)
print("SUMMARY:")
print(f"  Images tested: {len(test_files)}")
print(f"  Total plate-like regions: {total_regions}")
print(f"  Successfully recognized: {successful_plates}")

if successful_plates > 0:
    print(f"\n✓ SUCCESS! Detected and recognized {successful_plates} plate(s)")
elif total_regions > 0:
    print(f"\n⚠ Detected {total_regions} regions but OCR failed")
    print("  Possible causes:")
    print("    - Image quality too low")
    print("    - Unusual plate format")
    print("    - Text too small or blurry")
else:
    print(f"\n✗ No plate-like regions detected")
    print("  Suggestions:")
    print("    - Show license plate clearly to camera")
    print("    - Better lighting")
    print("    - Straight angle (not tilted)")

print(f"\nMarked images saved to: {OUTPUT_DIR}/")
