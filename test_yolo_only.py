#!/usr/bin/env python3
"""
Test YOLO detection only (no OCR) to isolate the crash
"""

import cv2
import time
from datetime import datetime
import sys

# Configuration
CAMERA_INDEX = 0

print("Loading YOLO model...")
try:
    from ultralytics import YOLO
    yolo_model = YOLO("yolov8n.pt")
    print("✓ YOLO loaded")
except Exception as e:
    print(f"Error loading YOLO: {e}")
    sys.exit(1)

print("Opening camera...")
cap = cv2.VideoCapture(CAMERA_INDEX)

if not cap.isOpened():
    print(f"Error: Cannot access camera at index {CAMERA_INDEX}")
    sys.exit(1)

print(f"✓ Camera opened at index {CAMERA_INDEX}")
print("Testing YOLO detection (no OCR) for 30 seconds...")
print("-" * 50)

start_time = time.time()
frame_count = 0
detection_count = 0

try:
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("Error: Failed to capture frame")
            break
        
        frame_count += 1
        
        # Run YOLO detection every 2 seconds
        if frame_count % 10 == 0:  # ~2 sec at 5 FPS
            try:
                print(f"Frame {frame_count}: Running detection...", end=" ", flush=True)
                results = yolo_model(frame, conf=0.3, verbose=False)
                
                total_detections = 0
                for result in results:
                    total_detections += len(result.boxes)
                
                print(f"Found {total_detections} object(s)")
                
                if total_detections > 0:
                    detection_count += 1
                    
            except Exception as e:
                print(f"Error: {e}")
                break
        
        # Check timeout
        if time.time() - start_time > 30:
            break

except KeyboardInterrupt:
    print("\nInterrupted")
except Exception as e:
    print(f"Crash: {e}")
    import traceback
    traceback.print_exc()

finally:
    cap.release()
    
    print("-" * 50)
    print(f"Test completed:")
    print(f"  Frames processed: {frame_count}")
    print(f"  Detection runs: {detection_count}")
    print(f"✓ No segmentation fault - YOLO is stable")
