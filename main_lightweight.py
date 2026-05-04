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
from collections import deque
from pathlib import Path

try:
    import pytesseract
except ImportError:
    print("Error: pytesseract not installed")
    sys.exit(1)

# Configuration
CAMERA_INDEX = 0
CAPTURE_INTERVAL = 2
OUTPUT_FILE = "plate_log.txt"
CONFIDENCE_THRESHOLD = 0.3  # Lower threshold to catch more plates (30%)
MAX_STORED_IMAGES = 5
IMAGES_DIR = "captured_plates"

# Create images directory if it doesn't exist
Path(IMAGES_DIR).mkdir(exist_ok=True)

# Store last 5 images in a rotating buffer
image_buffer = deque(maxlen=MAX_STORED_IMAGES)

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


def log_plate(plate_number, confidence=None, frame=None):
    """Log detected plate number with timestamp and save frame."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timestamp_file = datetime.now().strftime("%Y%m%d_%H%M%S")
    conf_str = f" ({confidence:.1f}%)" if confidence else ""
    log_entry = f"{plate_number}{conf_str} | {timestamp}\n"
    
    with open(OUTPUT_FILE, 'a') as f:
        f.write(log_entry)
    
    print(f"✓ Detected: {plate_number}{conf_str} at {timestamp}")
    
    # Save frame if provided
    if frame is not None:
        image_filename = f"{IMAGES_DIR}/{timestamp_file}_{plate_number}.jpg"
        cv2.imwrite(image_filename, frame)
        image_buffer.append(image_filename)
        print(f"  Saved: {image_filename}")


def extract_plate_text(frame, rect):
    """Extract text from detected region using Tesseract OCR."""
    try:
        x, y, w, h = rect
        
        # Extract region
        region = frame[y:y+h, x:x+w]
        
        if region.size == 0:
            return None, 0
        
        # Enhance for OCR - improved pipeline
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        
        # Improve contrast with CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        
        # Morphological operations to clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
        
        # Adaptive threshold (better than fixed threshold)
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY, 11, 2)
        
        # Upscale aggressively - larger text = better OCR
        scale = max(5, int(400 / max(w, h)))  # Target 400px width
        upscaled = cv2.resize(binary, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        # Final denoise
        upscaled = cv2.fastNlMeansDenoising(upscaled, h=10)
        
        # Run Tesseract OCR
        config = '--psm 8 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        text = pytesseract.image_to_string(upscaled, config=config, timeout=5).strip().upper()
        
        if text and len(text) >= 3:
            # Confidence based on text length
            confidence = min(100, len(text) * 15)
            return text, confidence
    except Exception as e:
        # Log error but continue processing
        print(f"OCR error: {e}", file=sys.stderr)
    
    return None, 0
        
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
    print(f"Confidence threshold: {CONFIDENCE_THRESHOLD * 100}%")
    print(f"Images saved to: {IMAGES_DIR}/")
    print("Press Ctrl+C to stop\n")
    
    init_log_file()
    last_capture_time = 0
    last_detected_plate = None
    last_detection_time = 0
    detection_count = 0
    
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
                detection_count += 1
                
                try:
                    # Detect plate regions using edge detection
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    gray = cv2.bilateralFilter(gray, 11, 17, 17)
                    edges = cv2.Canny(gray, 30, 200)
                    
                    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
                    edges = cv2.dilate(edges, kernel, iterations=3)
                    
                    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                    
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Detection #{detection_count}: Found {len(contours)} contours", end="")
                    
                    detections_found = False
                    
                    # Analyze contours
                    for contour in contours:
                        x, y, w, h = cv2.boundingRect(contour)
                        
                        if w < 20 or h < 10:
                            continue
                        
                        ratio = w / h if h > 0 else 0
                        
                        # License plates are typically 2-5 times wider than tall
                        if 2 < ratio < 5 and w > 30 and h > 10:
                            # Check fill ratio
                            area = w * h
                            contour_area = cv2.contourArea(contour)
                            fill_ratio = contour_area / area if area > 0 else 0
                            
                            if 0.4 < fill_ratio < 0.95:
                                plate_text, ocr_conf = extract_plate_text(frame, (x, y, w, h))
                                
                                if plate_text:
                                    print(f" -> Found: '{plate_text}'", end="")
                                
                                if plate_text and is_likely_plate(plate_text) and ocr_conf >= CONFIDENCE_THRESHOLD:
                                    detections_found = True
                                    
                                    # Avoid duplicates
                                    if plate_text != last_detected_plate or (current_time - last_detection_time) > 5:
                                        log_plate(plate_text, ocr_conf, frame)
                                        last_detected_plate = plate_text
                                        last_detection_time = current_time
                    
                    if not detections_found:
                        print(" [no valid plates]", end="")
                    
                    print()  # New line
                        
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
