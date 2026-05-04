#!/usr/bin/env python3
"""
Find available USB cameras on your system
"""

import cv2
import os

print("Available cameras on this system:")
print("=" * 50)

# Check /dev/video* devices
video_devices = []
for i in range(10):
    device = f"/dev/video{i}"
    if os.path.exists(device):
        video_devices.append(i)
        print(f"Found: {device}")

if not video_devices:
    print("No /dev/video devices found")

print("\nTesting OpenCV camera access:")
print("-" * 50)

# Test each video device with OpenCV
for i in video_devices:
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            height, width = frame.shape[:2]
            print(f"✓ Camera {i}: {width}x{height} - WORKING")
        else:
            print(f"✗ Camera {i}: Device exists but cannot capture")
        cap.release()
    else:
        print(f"✗ Camera {i}: Cannot open device")

print("\nUsage in main.py:")
print("-" * 50)
print("Edit main.py and change CAMERA_INDEX to the working camera number")
print("Example: CAMERA_INDEX = 0")
