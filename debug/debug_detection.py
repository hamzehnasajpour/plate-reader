#!/usr/bin/env python3
"""
Debug script to analyze plate detection step-by-step
Captures one frame and saves visualizations at each detection stage
"""

import cv2
import sys
import os
from pathlib import Path

try:
    import pytesseract
except ImportError:
    print("Error: pytesseract not installed")
    sys.exit(1)

# Configuration (same as main)
CAMERA_INDEX = 0
MIN_WIDTH = 30
MIN_HEIGHT = 10
MIN_ASPECT_RATIO = 2.0
MAX_ASPECT_RATIO = 5.0
MIN_FILL_RATIO = 0.4
MAX_FILL_RATIO = 0.95
MIN_TEXT_LENGTH = 6
MAX_TEXT_LENGTH = 6

# Create debug directory
DEBUG_DIR = "debug/detection_output"
Path(DEBUG_DIR).mkdir(parents=True, exist_ok=True)

def detect_plate_contours_debug(gray_frame):
    """Detect plates with debug output and visualization"""
    
    # Step 1: Bilateral filter
    filtered = cv2.bilateralFilter(gray_frame, 13, 15, 15)
    cv2.imwrite(f"{DEBUG_DIR}/01_filtered.jpg", filtered)
    print("✓ Saved: 01_filtered.jpg")
    
    # Step 2: Canny edge detection
    edges = cv2.Canny(filtered, 30, 200)
    cv2.imwrite(f"{DEBUG_DIR}/02_edges.jpg", edges)
    print("✓ Saved: 02_edges.jpg")
    
    # Step 3: Dilation
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    edges_dilated = cv2.dilate(edges, kernel, iterations=3)
    cv2.imwrite(f"{DEBUG_DIR}/03_edges_dilated.jpg", edges_dilated)
    print("✓ Saved: 03_edges_dilated.jpg")
    
    # Step 4: Find contours
    contours, _ = cv2.findContours(edges_dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    print(f"\n🔍 Found {len(contours)} total contours")
    
    # Step 5: Sort by area
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:20]
    print(f"📊 Top 20 by area (showing areas):")
    for i, c in enumerate(contours[:5]):
        area = cv2.contourArea(c)
        print(f"  {i+1}. Area: {area:.0f} px²")
    
    detected_plates = []
    
    # Visualize filtering process
    vis_frame = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2BGR)
    
    # Step 6: Filter for 4-sided rectangles
    for idx, contour in enumerate(contours):
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.018 * peri, True)
        
        if len(approx) != 4:
            continue
        
        x, y, w, h = cv2.boundingRect(approx)
        
        # Check filters
        passes_size = w >= MIN_WIDTH and h >= MIN_HEIGHT
        ratio = w / h if h > 0 else 0
        passes_ratio = MIN_ASPECT_RATIO <= ratio <= MAX_ASPECT_RATIO
        
        area = w * h
        contour_area = cv2.contourArea(contour)
        fill_ratio = contour_area / area if area > 0 else 0
        passes_fill = MIN_FILL_RATIO <= fill_ratio <= MAX_FILL_RATIO
        
        if passes_size and passes_ratio and passes_fill:
            detected_plates.append((x, y, w, h))
            cv2.rectangle(vis_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)  # Green = valid
            print(f"\n✅ Valid plate candidate #{len(detected_plates)}:")
            print(f"   Position: ({x}, {y})")
            print(f"   Size: {w}×{h}")
            print(f"   Aspect ratio: {ratio:.2f}")
            print(f"   Fill ratio: {fill_ratio:.2f}")
        else:
            cv2.rectangle(vis_frame, (x, y), (x+w, y+h), (0, 0, 255), 1)  # Red = rejected
            if not passes_size:
                print(f"❌ Rejected (too small: {w}×{h})")
            elif not passes_ratio:
                print(f"❌ Rejected (bad ratio: {ratio:.2f}, need {MIN_ASPECT_RATIO}-{MAX_ASPECT_RATIO})")
            elif not passes_fill:
                print(f"❌ Rejected (fill ratio: {fill_ratio:.2f}, need {MIN_FILL_RATIO}-{MAX_FILL_RATIO})")
    
    cv2.imwrite(f"{DEBUG_DIR}/04_contours_filtered.jpg", vis_frame)
    print(f"\n✓ Saved: 04_contours_filtered.jpg (Green=valid, Red=rejected)")
    
    return detected_plates


def main():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    
    if not cap.isOpened():
        print(f"❌ Error: Cannot access camera at index {CAMERA_INDEX}")
        return
    
    print("📷 Capturing frame...")
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("❌ Failed to capture frame")
        return
    
    # Save original frame
    cv2.imwrite(f"{DEBUG_DIR}/00_original.jpg", frame)
    print(f"✓ Saved: 00_original.jpg ({frame.shape[1]}×{frame.shape[0]})")
    
    # Detect plates
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    detected = detect_plate_contours_debug(gray)
    
    print(f"\n{'='*60}")
    print(f"📊 SUMMARY: Found {len(detected)} valid plate candidates")
    print(f"{'='*60}")
    
    # Try OCR on each candidate
    if detected:
        print("\n🔤 Testing Tesseract OCR on each candidate...")
        for idx, rect in enumerate(detected):
            x, y, w, h = rect
            region = frame[y:y+h, x:x+w]
            
            # Save region
            cv2.imwrite(f"{DEBUG_DIR}/plate_{idx+1}_original.jpg", region)
            
            # Simple preprocessing
            gray_region = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            
            # Upscale
            scale = max(3, int(400 / max(w, h)))
            upscaled = cv2.resize(gray_region, (0, 0), fx=scale, fy=scale, 
                                 interpolation=cv2.INTER_CUBIC)
            
            # Threshold
            _, thresh = cv2.threshold(upscaled, 150, 255, cv2.THRESH_BINARY)
            
            cv2.imwrite(f"{DEBUG_DIR}/plate_{idx+1}_preprocessed.jpg", thresh)
            
            # OCR
            config = '--psm 11 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            text = pytesseract.image_to_string(thresh, config=config).strip().upper()
            
            print(f"\n  📋 Candidate #{idx+1}:")
            print(f"     Raw text: '{text}'")
            print(f"     Length: {len(text)}")
            print(f"     Valid (6 chars, letters+digits): {len(text)==6 and any(c.isalpha() for c in text) and any(c.isdigit() for c in text)}")
    else:
        print("\n⚠️  No valid plate candidates found!")
        print("\nTroubleshooting tips:")
        print("1. Check if 02_edges.jpg shows clear plate edges")
        print("2. If edges are too faint, lower Canny thresholds (currently 30, 200)")
        print("3. If too much noise, increase bilateral filter strength")
        print("4. Check 04_contours_filtered.jpg - are red boxes where plates should be?")
        print("5. Try adjusting MIN_ASPECT_RATIO or MIN_FILL_RATIO")
    
    print(f"\n📁 All debug images saved to: {DEBUG_DIR}/")


if __name__ == "__main__":
    main()
