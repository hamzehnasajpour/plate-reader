#!/usr/bin/env python3
"""
Simple test - just captures and saves frames every 2 seconds
Tests if the basic capture/save mechanism works
"""

import cv2
import time
from datetime import datetime
from pathlib import Path

CAMERA_INDEX = 0
CAPTURE_INTERVAL = 2
TEST_DIR = "test_frames"

Path(TEST_DIR).mkdir(exist_ok=True)

print(f"Opening camera...")
cap = cv2.VideoCapture(CAMERA_INDEX)

if not cap.isOpened():
    print(f"Error: Cannot access camera at index {CAMERA_INDEX}")
    exit(1)

print(f"✓ Camera opened")
print(f"Saving test frames to {TEST_DIR}/ every {CAPTURE_INTERVAL} seconds")
print(f"Press Ctrl+C to stop\n")

last_time = 0
frame_count = 0

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        current_time = time.time()
        
        if current_time - last_time >= CAPTURE_INTERVAL:
            last_time = current_time
            frame_count += 1
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{TEST_DIR}/frame_{frame_count:03d}_{timestamp}.jpg"
            
            try:
                cv2.imwrite(filename, frame)
                size = Path(filename).stat().st_size
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Saved: {filename} ({size} bytes)")
            except Exception as e:
                print(f"Error saving file: {e}")

except KeyboardInterrupt:
    print(f"\nStopped")

finally:
    cap.release()
    print(f"✓ Test complete - {frame_count} frames saved to {TEST_DIR}/")
