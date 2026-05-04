#!/usr/bin/env python3
"""
Debug version - saves all detected regions regardless of confidence
Helps troubleshoot why images aren't being saved
"""

import cv2
import time
from datetime import datetime
import os
import sys
from pathlib import Path

# Configuration
CAMERA_INDEX = 0
CAPTURE_INTERVAL = 2
OUTPUT_FILE = "plate_log.txt"
IMAGES_DIR = "captured_plates_debug"

# Create images directory
Path(IMAGES_DIR).mkdir(exist_ok=True)

# Load Haar Cascade classifier
cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
cascade = cv2.CascadeClassifier(cascade_path)

if cascade.empty():
    print("Error: Could not load Haar Cascade classifier")
    sys.exit(1)

print("✓ Haar Cascade classifier loaded")


def capture_and_analyze():
    """Capture and analyze frames - save ALL detections."""
    cap = cv2.VideoCapture(CAMERA_INDEX)
    
    if not cap.isOpened():
        print(f"Error: Cannot access camera at index {CAMERA_INDEX}")
        return
    
    print(f"Camera opened. Capturing every {CAPTURE_INTERVAL} seconds...")
    print(f"Debug images saved to: {IMAGES_DIR}/")
    print("Press Ctrl+C to stop\n")
    
    last_capture_time = 0
    detection_num = 0
    
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
                detection_num += 1
                
                try:
                    # Detect objects
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    rects = cascade.detectMultiScale(gray, 1.3, 5)
                    
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Detection #{detection_num}: Found {len(rects)} regions")
                    
                    if len(rects) > 0:
                        # Save the full frame with regions marked
                        frame_copy = frame.copy()
                        for i, (x, y, w, h) in enumerate(rects):
                            ratio = w / h if h > 0 else 0
                            
                            # Draw rectangle
                            cv2.rectangle(frame_copy, (x, y), (x + w, y + h), (0, 255, 0), 2)
                            cv2.putText(frame_copy, f"R:{ratio:.2f}", (x, y - 10), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                            
                            # Save individual crop
                            crop = frame[y:y+h, x:x+w]
                            crop_file = f"{IMAGES_DIR}/{detection_num:04d}_crop_{i:02d}_ratio{ratio:.2f}.jpg"
                            cv2.imwrite(crop_file, crop)
                            print(f"  Saved: {crop_file}")
                        
                        # Save full frame with boxes
                        frame_file = f"{IMAGES_DIR}/{detection_num:04d}_full_frame.jpg"
                        cv2.imwrite(frame_file, frame_copy)
                        print(f"  Saved: {frame_file}")
                    else:
                        print(f"  No detections in this frame")
                        
                except Exception as e:
                    print(f"Error: {e}")
                    continue
    
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        cap.release()
        print(f"\nDebug images saved to {IMAGES_DIR}/")


if __name__ == "__main__":
    capture_and_analyze()
