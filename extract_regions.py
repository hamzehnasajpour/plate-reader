#!/usr/bin/env python3
"""
Save extracted plate regions for visual inspection
Helps diagnose why OCR is failing
"""

import cv2
from pathlib import Path

TEST_DIR = "test_frames"
OUTPUT_DIR = "extracted_plate_regions"

Path(OUTPUT_DIR).mkdir(exist_ok=True)

def detect_and_extract(frame_path):
    """Detect and extract plate regions from image."""
    frame = cv2.imread(str(frame_path))
    if frame is None:
        return None
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 11, 17, 17)
    edges = cv2.Canny(gray, 30, 200)
    
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    edges = cv2.dilate(edges, kernel, iterations=3)
    
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    regions = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        
        if w < 20 or h < 10:
            continue
        
        ratio = w / h if h > 0 else 0
        
        if 2 < ratio < 5 and w > 30 and h > 10:
            area = w * h
            contour_area = cv2.contourArea(contour)
            fill_ratio = contour_area / area if area > 0 else 0
            
            if 0.4 < fill_ratio < 0.95:
                regions.append((x, y, w, h))
    
    return regions

# Process all test images
test_files = sorted(Path(TEST_DIR).glob("*.jpg"))
print(f"Processing {len(test_files)} images...\n")

file_num = 1
for img_path in test_files:
    regions = detect_and_extract(img_path)
    frame = cv2.imread(str(img_path))
    
    if regions:
        print(f"{img_path.name}: Found {len(regions)} regions")
        
        for i, (x, y, w, h) in enumerate(regions):
            crop = frame[y:y+h, x:x+w]
            
            # Save raw crop
            raw_file = f"{OUTPUT_DIR}/{file_num:02d}_raw.jpg"
            cv2.imwrite(raw_file, crop)
            
            # Enhanced version for inspection
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            gray = clahe.apply(gray)
            _, binary = cv2.threshold(gray, 140, 255, cv2.THRESH_BINARY)
            upscaled = cv2.resize(binary, (0, 0), fx=4, fy=4)
            
            enhanced_file = f"{OUTPUT_DIR}/{file_num:02d}_enhanced_x4.jpg"
            cv2.imwrite(enhanced_file, upscaled)
            
            print(f"  Region: {w}x{h} -> Saved: {file_num:02d}_raw.jpg (and enhanced)")
            file_num += 1

print(f"\n✓ Extracted {file_num - 1} regions to {OUTPUT_DIR}/")
print("Open the images to verify they contain license plate text")
