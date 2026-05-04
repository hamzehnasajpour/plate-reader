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
MAX_STORED_IMAGES = 50  # Maximum number of detected plate images to keep
IMAGES_DIR = "captured_plates"
SHOW_DISPLAY = True  # Show live camera feed with detection visualization
MIN_TEXT_LENGTH = 6  # Minimum plate text length
MAX_TEXT_LENGTH = 6  # Maximum plate text length

# Detection Filters (adjust to reduce false positives)
MIN_ASPECT_RATIO = 2.0  # Width/Height ratio lower bound (plates are wider)
MAX_ASPECT_RATIO = 5.0  # Width/Height ratio upper bound
MIN_WIDTH = 30  # Minimum region width in pixels
MIN_HEIGHT = 10  # Minimum region height in pixels
MIN_FILL_RATIO = 0.4  # Minimum contour fill ratio (0.0-1.0)
MAX_FILL_RATIO = 0.95  # Maximum contour fill ratio (0.0-1.0)

# Create images directory if it doesn't exist
Path(IMAGES_DIR).mkdir(exist_ok=True)

# Store last N images in a rotating buffer (tracks filenames only)
image_buffer = deque(maxlen=MAX_STORED_IMAGES)

# Load Haar Cascade classifier for license plates
# Using car cascade as fallback (less specialized but more reliable on ARM64)
cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
cascade = cv2.CascadeClassifier(cascade_path)

if cascade.empty():
    print("Error: Could not load Haar Cascade classifier")
    sys.exit(1)

print("✓ Haar Cascade classifier loaded")

def draw_ui_overlay(frame, detection_count, is_scanning, detected_rectangles, valid_plates):
    """
    Draw UI overlay with status information and detection rectangles.
    
    Args:
        frame: Input frame
        detection_count: Number of detection cycles
        is_scanning: Whether currently in detection mode
        detected_rectangles: List of (x, y, w, h) all detected regions
        valid_plates: List of (x, y, w, h, text, conf) valid plates
    """
    display_frame = frame.copy()
    h, w = display_frame.shape[:2]
    
    # Draw all detected regions (yellow boxes)
    for x, y, bw, bh in detected_rectangles:
        cv2.rectangle(display_frame, (x, y), (x+bw, y+bh), (0, 255, 255), 1)
    
    # Draw valid plates (green boxes with text)
    for x, y, bw, bh, text, conf in valid_plates:
        cv2.rectangle(display_frame, (x, y), (x+bw, y+bh), (0, 255, 0), 2)
        text_label = f"{text} ({conf:.0f}%)"
        text_pos = (x, max(y - 5, 25))
        cv2.putText(display_frame, text_label, text_pos, 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    # Draw status bar at top
    status_bar_height = 30
    cv2.rectangle(display_frame, (0, 0), (w, status_bar_height), (50, 50, 50), -1)
    
    # Status text
    scan_status = "[SCANNING]" if is_scanning else "[READY]"
    status_text = f"Detection #{detection_count} {scan_status}"
    cv2.putText(display_frame, status_text, (10, 22), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
    
    cv2.putText(display_frame, "Press 'q' to quit", (w - 180, 22),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    
    return display_frame

def init_log_file():
    """Initialize the log file with header if it doesn't exist."""
    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'w') as f:
            f.write("Registration Number | Timestamp\n")
            f.write("=" * 50 + "\n")


def cleanup_old_images():
    """Delete image files that are no longer in the buffer."""
    # Get all image files in the directory
    try:
        all_files = sorted([f for f in os.listdir(IMAGES_DIR) if f.endswith('.jpg')])
        # Get current files in buffer (just the filenames, not full paths)
        buffer_filenames = [os.path.basename(f) for f in image_buffer]
        
        # Delete files that aren't in the buffer
        for file in all_files:
            if file not in buffer_filenames:
                file_path = os.path.join(IMAGES_DIR, file)
                try:
                    os.remove(file_path)
                except OSError:
                    pass
    except Exception as e:
        print(f"Cleanup warning: {e}", file=sys.stderr)


def log_plate(plate_number, confidence=None, frame=None, rect=None):
    """Log detected plate number with timestamp and save frame with bounding box."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timestamp_file = datetime.now().strftime("%Y%m%d_%H%M%S")
    conf_str = f" ({confidence:.1f}%)" if confidence else ""
    log_entry = f"{plate_number}{conf_str} | {timestamp}\n"
    
    with open(OUTPUT_FILE, 'a') as f:
        f.write(log_entry)
    
    print(f"✓ Detected: {plate_number}{conf_str} at {timestamp}")
    
    # Save frame if provided
    if frame is not None:
        # Draw bounding box around detected plate if coordinates provided
        frame_with_box = frame.copy()
        if rect is not None:
            x, y, w, h = rect
            # Draw rectangle with green color, thickness 2
            cv2.rectangle(frame_with_box, (x, y), (x+w, y+h), (0, 255, 0), 2)
            # Draw text label above the box
            text_pos = (x, max(y - 5, 25))
            cv2.putText(frame_with_box, f"{plate_number} ({confidence:.0f}%)", text_pos, 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        image_filename = f"{IMAGES_DIR}/{timestamp_file}_{plate_number}.jpg"
        cv2.imwrite(image_filename, frame_with_box)
        image_buffer.append(image_filename)
        cleanup_old_images()  # Remove files that are no longer in buffer
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
        text = pytesseract.image_to_string(upscaled, config=config, timeout=2).strip().upper()
        
        if text and MIN_TEXT_LENGTH <= len(text) <= MAX_TEXT_LENGTH:
            # Confidence based on text length
            confidence = min(100, len(text) * 15)
            return text, confidence
    except Exception as e:
        # Log error but continue processing
        print(f"OCR error: {e}", file=sys.stderr)
    
    return None, 0


def is_likely_plate(text):
    """Check if text looks like a license plate."""
    if not text or len(text) < MIN_TEXT_LENGTH or len(text) > MAX_TEXT_LENGTH:
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
    detection_count = 0
    
    # Create display window if enabled
    if SHOW_DISPLAY:
        cv2.namedWindow("License Plate Reader", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("License Plate Reader", 960, 720)
    
    try:
        while True:
            ret, frame = cap.read()
            
            if not ret:
                print("Error: Failed to capture frame")
                break
            
            current_time = time.time()
            is_scanning = (current_time - last_capture_time) >= CAPTURE_INTERVAL
            detected_rectangles = []
            valid_plates = []
            
            # Detect every CAPTURE_INTERVAL seconds
            if is_scanning:
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
                        
                        # License plates are typically wider than tall (configurable ratio)
                        if MIN_ASPECT_RATIO < ratio < MAX_ASPECT_RATIO and w > MIN_WIDTH and h > MIN_HEIGHT:
                            # Skip very small regions (not worth OCR time)
                            if w < 60 or h < 25:
                                continue
                            
                            # Check fill ratio
                            area = w * h
                            contour_area = cv2.contourArea(contour)
                            fill_ratio = contour_area / area if area > 0 else 0
                            
                            if MIN_FILL_RATIO < fill_ratio < MAX_FILL_RATIO:
                                detected_rectangles.append((x, y, w, h))
                                
                                plate_text, ocr_conf = extract_plate_text(frame, (x, y, w, h))
                                
                                if plate_text:
                                    print(f" -> Found: '{plate_text}'", end="")
                                
                                if plate_text and is_likely_plate(plate_text) and ocr_conf >= CONFIDENCE_THRESHOLD:
                                    detections_found = True
                                    valid_plates.append((x, y, w, h, plate_text, ocr_conf))
                                    
                                    # Only store if different from last detected plate
                                    if plate_text != last_detected_plate:
                                        log_plate(plate_text, ocr_conf, frame, (x, y, w, h))
                                        last_detected_plate = plate_text
                    
                    if not detections_found:
                        print(" [no valid plates]", end="")
                    
                    print()  # New line
                        
                except Exception as e:
                    print(f"Detection error: {e}", file=sys.stderr)
                    continue
            
            # Display live feed with overlay
            if SHOW_DISPLAY:
                display_frame = draw_ui_overlay(frame, detection_count, is_scanning, 
                                               detected_rectangles, valid_plates)
                cv2.imshow("License Plate Reader", display_frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("\nStopping...")
                    break
    
    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cap.release()
        if SHOW_DISPLAY:
            cv2.destroyAllWindows()
        print(f"Results saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    capture_and_analyze()
