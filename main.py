#!/usr/bin/env python3
"""
License Plate Reader
Captures frames from USB camera every 2 seconds and identifies license plates.
Stores detected plate numbers with timestamps to a log file.
"""

import cv2
import time
from datetime import datetime
import os
from openalpr import Alpr

# Configuration
CAMERA_INDEX = 0  # Default USB camera (change if using a different camera)
CAPTURE_INTERVAL = 2  # Capture every 2 seconds
OUTPUT_FILE = "plate_log.txt"

# Initialize OpenALPR
alpr = Alpr("us", "/etc/openalpr/openalpr.conf", "/usr/share/openalpr/runtime_data")

if not alpr.is_loaded():
    print("Error loading OpenALPR")
    exit(1)

alpr.set_top_n(3)  # Get top 3 results


def init_log_file():
    """Initialize the log file with header if it doesn't exist."""
    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'w') as f:
            f.write("Registration Number | Timestamp\n")
            f.write("=" * 50 + "\n")


def log_plate(plate_number):
    """Log detected plate number with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{plate_number} | {timestamp}\n"
    
    with open(OUTPUT_FILE, 'a') as f:
        f.write(log_entry)
    
    print(f"✓ Detected: {plate_number} at {timestamp}")


def capture_and_analyze():
    """Capture frames from USB camera and analyze for license plates."""
    cap = cv2.VideoCapture(CAMERA_INDEX)
    
    if not cap.isOpened():
        print(f"Error: Cannot access camera at index {CAMERA_INDEX}")
        return
    
    print(f"Camera opened successfully. Capturing every {CAPTURE_INTERVAL} seconds...")
    print(f"Press 'q' to quit. Results will be saved to {OUTPUT_FILE}\n")
    
    init_log_file()
    last_capture_time = 0
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("Error: Failed to capture frame")
            break
        
        current_time = time.time()
        
        # Capture every CAPTURE_INTERVAL seconds
        if current_time - last_capture_time >= CAPTURE_INTERVAL:
            last_capture_time = current_time
            
            # Analyze frame for license plates
            results = alpr.recognize_ndarray(frame)
            
            # Process results
            if results["results"]:
                for result in results["results"]:
                    candidates = result["candidates"]
                    if candidates:
                        # Get the top candidate (most confident)
                        top_plate = candidates[0]["plate"]
                        confidence = candidates[0]["confidence"]
                        
                        # Only log if confidence is reasonable (>50%)
                        if confidence > 50:
                            log_plate(f"{top_plate} (confidence: {confidence:.1f}%)")
            else:
                print(".", end="", flush=True)  # Indicator of scanning
        
        # Display frame (optional - for debugging)
        cv2.imshow("Plate Reader", frame)
        
        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("\nExiting...")
            break
    
    cap.release()
    cv2.destroyAllWindows()
    alpr.unload()
    print(f"Results saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    try:
        capture_and_analyze()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        alpr.unload()
    except Exception as e:
        print(f"Error: {e}")
        alpr.unload()
