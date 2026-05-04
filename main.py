#!/usr/bin/env python3
"""
License Plate Reader
Captures frames from USB camera every 2 seconds and identifies license plates.
Stores detected plate numbers with timestamps to a log file.

Uses YOLOv8 for plate detection and Tesseract OCR for text recognition.
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
    print("Run: pip install pytesseract")
    sys.exit(1)

# Configuration
CAMERA_INDEX = 0  # Default USB camera (change if using a different camera)
CAPTURE_INTERVAL = 10  # Capture every 10 seconds
OUTPUT_FILE = "plate_log.txt"
CONFIDENCE_THRESHOLD = 0.5  # Only log plates with >50% confidence
HEADLESS_MODE = True  # Set to False if display is available

# Global model variables (lazy loaded)
yolo_model = None


def load_models():
    """Lazy load models to reduce initial memory usage."""
    global yolo_model
    
    try:
        print("Loading YOLO model...")
        from ultralytics import YOLO
        yolo_model = YOLO("yolov8n.pt")  # Nano model (fastest)
        print("✓ YOLO loaded")
    except Exception as e:
        print(f"Error loading YOLO: {e}")
        sys.exit(1)
    
    print("✓ Models loaded successfully\n")


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


def extract_plate_text(frame, box):
    """Extract text from detected license plate region using Tesseract OCR."""
    try:
        x1, y1, x2, y2 = box
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        
        # Crop the plate region
        plate_crop = frame[y1:y2, x1:x2]
        
        if plate_crop.size == 0:
            return None, 0
        
        # Enhance the image for better OCR
        gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
        # Apply threshold for better OCR
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        # Upscale for better OCR accuracy
        upscaled = cv2.resize(binary, (0, 0), fx=2, fy=2)
        
        # Run Tesseract OCR with optimized settings
        config = '--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        text = pytesseract.image_to_string(upscaled, config=config, timeout=5).strip().upper()
        
        if text and len(text) >= 3:
            # Confidence based on text length
            confidence = min(100, len(text) * 15)
            return text, confidence
    except Exception as e:
        # Log error but continue processing
        print(f"OCR error: {e}", file=sys.stderr)
    
    return None, 0


def is_likely_plate(text):
    """Check if detected text looks like a license plate."""
    if not text or len(text) < 3:
        return False
    
    # License plates typically have mix of letters and numbers
    has_letter = any(c.isalpha() for c in text)
    has_digit = any(c.isdigit() for c in text)
    
    return has_letter and has_digit


def capture_and_analyze():
    """Capture frames from USB camera and analyze for license plates."""
    if yolo_model is None:
        print("Error: Models not loaded")
        return
    
    cap = cv2.VideoCapture(CAMERA_INDEX)
    
    if not cap.isOpened():
        print(f"Error: Cannot access camera at index {CAMERA_INDEX}")
        print(f"Run 'python3 find_camera.py' to find available cameras")
        return
    
    print(f"Camera opened successfully. Capturing every {CAPTURE_INTERVAL} seconds...")
    print(f"Press 'q' to quit. Results will be saved to {OUTPUT_FILE}\n")
    
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
            
            # Capture every CAPTURE_INTERVAL seconds
            if current_time - last_capture_time >= CAPTURE_INTERVAL:
                last_capture_time = current_time
                
                try:
                    # Run YOLO detection
                    results = yolo_model(frame, conf=0.3, verbose=False)
                    
                    detections_found = False
                    
                    # Process detections
                    for result in results:
                        boxes = result.boxes
                        
                        for box in boxes:
                            x1, y1, x2, y2 = box.xyxy[0]
                            conf = box.conf[0].item()
                            
                            # Extract text from detected region
                            plate_text, ocr_conf = extract_plate_text(frame, [x1, y1, x2, y2])
                            
                            if plate_text and is_likely_plate(plate_text) and ocr_conf >= CONFIDENCE_THRESHOLD:
                                detections_found = True
                                
                                # Avoid logging same plate multiple times
                                if plate_text != last_detected_plate or (current_time - last_detection_time) > 5:
                                    log_plate(plate_text, ocr_conf)
                                    last_detected_plate = plate_text
                                    last_detection_time = current_time
                    
                    if not detections_found:
                        print(".", end="", flush=True)
                        
                except Exception as e:
                    print(f"Error during detection: {e}", file=sys.stderr)
                    continue
            
            # Display frame only if not in headless mode
            if not HEADLESS_MODE:
                cv2.imshow("Plate Reader", frame)
                # Press 'q' to quit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("\nExiting...")
                    break
    
    finally:
        cap.release()
        if not HEADLESS_MODE:
            cv2.destroyAllWindows()
        print(f"\nResults saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    try:
        load_models()
        capture_and_analyze()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
