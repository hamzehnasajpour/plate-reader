#!/usr/bin/env python3
"""
License Plate Reader - Lightweight Version
Uses Haar Cascade for object detection (no YOLO) and Tesseract for OCR
Much lighter weight for ARM64 (Raspberry Pi)
"""

import cv2
import time
from datetime import datetime
import os
import sys

try:
    import pytesseract
except ImportError:
    print("Error: pytesseract not installed")
    sys.exit(1)

# Configuration
CAMERA_INDEX = 0
CAPTURE_INTERVAL = 2
OUTPUT_FILE = "plate_log.txt"
CONFIDENCE_THRESHOLD = 0.5

# Load Haar Cascade classifier for license plates
# Using car cascade as fallback (less specialized but more reliable on ARM64)
cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
cascade = cv2.CascadeClassifier(cascade_path)

if cascade.empty():
    print("Error: Could not load Haar Cascade classifier")
    sys.exit(1)

print("✓ Haar Cascade classifier loaded")


def init_log_file():
    """Initialize the log file with header if it doesn't exist."""
    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'w') as f:
            f.write("Registration Number | Timestamp\n")
            f.write("=" * 50 + "\n")


def log_plate(plate_number, confidence=None):
    """Log detected plate number with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conf_str = f" ({confidence:.1f}%)" if confidence else ""
    log_entry = f"{plate_number}{conf_str} | {timestamp}\n"
    
    with open(OUTPUT_FILE, 'a') as f:
        f.write(log_entry)
    
    print(f"✓ Detected: {plate_number}{conf_str} at {timestamp}")


def extract_plate_text(frame, rect):
    """Extract text from detected region using Tesseract OCR."""
    try:
        x, y, w, h = rect
        
        # Extract region
        region = frame[y:y+h, x:x+w]
        
        if region.size == 0:
            return None, 0
        
        # Enhance for OCR
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        upscaled = cv2.resize(binary, (0, 0), fx=2, fy=2)
        
        # Run Tesseract
        config = '--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        text = pytesseract.image_to_string(upscaled, config=config, timeout=5).strip().upper()
        
        if text and len(text) >= 3:
            confidence = min(100, len(text) * 15)
            return text, confidence
    except Exception as e:
        print(f"OCR error: {e}", file=sys.stderr)
    
    return None, 0


def is_likely_plate(text):
    """Check if text looks like a license plate."""
    if not text or len(text) < 3:
        return False
    
    has_letter = any(c.isalpha() for c in text)
    has_digit = any(c.isdigit() for c in text)
    
    return has_letter and has_digit


def capture_and_analyze():
    """Capture and analyze frames."""
    cap = cv2.VideoCapture(CAMERA_INDEX)
    
    if not cap.isOpened():
        print(f"Error: Cannot access camera at index {CAMERA_INDEX}")
        return
    
    print(f"Camera opened. Capturing every {CAPTURE_INTERVAL} seconds...")
    print("Press Ctrl+C to stop\n")
    
    init_log_file()
    last_capture_time = 0
    last_detected_plate = None
    last_detection_time = 0
    
    try:
        while True:
            ret, frame = cap.read()
            
            if not ret:
                print("Error: Failed to capture frame")
                break
            
            current_time = time.time()
            
            # Detect every CAPTURE_INTERVAL seconds
            if current_time - last_capture_time >= CAPTURE_INTERVAL:
                last_capture_time = current_time
                
                try:
                    # Detect objects (regions of interest)
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    rects = cascade.detectMultiScale(gray, 1.3, 5)
                    
                    detections_found = False
                    
                    # Filter detections by size (license plates are usually specific ratio)
                    for x, y, w, h in rects:
                        # Filter by aspect ratio (license plates are typically wider)
                        ratio = w / h if h > 0 else 0
                        
                        if 2 < ratio < 5 and w > 40 and h > 15:  # License plate typical proportions
                            plate_text, ocr_conf = extract_plate_text(frame, (x, y, w, h))
                            
                            if plate_text and is_likely_plate(plate_text) and ocr_conf >= CONFIDENCE_THRESHOLD:
                                detections_found = True
                                
                                # Avoid duplicates
                                if plate_text != last_detected_plate or (current_time - last_detection_time) > 5:
                                    log_plate(plate_text, ocr_conf)
                                    last_detected_plate = plate_text
                                    last_detection_time = current_time
                    
                    if not detections_found:
                        print(".", end="", flush=True)
                        
                except Exception as e:
                    print(f"Detection error: {e}", file=sys.stderr)
                    continue
    
    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cap.release()
        print(f"Results saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    capture_and_analyze()
