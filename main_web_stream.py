#!/usr/bin/env python3
"""
License Plate Reader - Web Streaming Version
Stream camera feed over HTTP for remote viewing via SSH
"""

import cv2
import time
from datetime import datetime
import os
import sys
from collections import deque
from pathlib import Path
import threading

try:
    import pytesseract
except ImportError:
    print("Error: pytesseract not installed")
    sys.exit(1)

try:
    from flask import Flask, render_template_string, Response
except ImportError:
    print("Error: Flask not installed. Install with: pip install flask")
    sys.exit(1)

# Configuration
CAMERA_INDEX = 0
CAPTURE_INTERVAL = 2
OUTPUT_FILE = "plate_log.txt"
CONFIDENCE_THRESHOLD = 0.3
MAX_STORED_IMAGES = 50
IMAGES_DIR = "captured_plates"
HTTP_PORT = 8080

# Create images directory if it doesn't exist
Path(IMAGES_DIR).mkdir(exist_ok=True)

# Store last N images in a rotating buffer
image_buffer = deque(maxlen=MAX_STORED_IMAGES)

# Load Haar Cascade classifier
cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
cascade = cv2.CascadeClassifier(cascade_path)

if cascade.empty():
    print("Error: Could not load Haar Cascade classifier")
    sys.exit(1)

print("✓ Haar Cascade classifier loaded")

# Global variables for streaming
frame_buffer = None
frame_lock = threading.Lock()
latest_stats = {
    "detection_count": 0,
    "last_plate": "None",
    "detected_boxes": [],
    "valid_plates": []
}
stats_lock = threading.Lock()

# Flask app
app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>License Plate Reader - Remote Stream</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #1a1a1a;
            color: #fff;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            color: #4CAF50;
            margin-bottom: 20px;
        }
        .video-container {
            background: #000;
            border: 3px solid #4CAF50;
            border-radius: 5px;
            overflow: hidden;
            margin-bottom: 20px;
        }
        #video {
            width: 100%;
            display: block;
            background: #000;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-box {
            background: #2a2a2a;
            border-left: 4px solid #4CAF50;
            padding: 15px;
            border-radius: 5px;
        }
        .stat-label {
            font-size: 12px;
            color: #888;
            text-transform: uppercase;
        }
        .stat-value {
            font-size: 24px;
            color: #4CAF50;
            font-weight: bold;
            margin-top: 5px;
        }
        .log-box {
            background: #2a2a2a;
            border: 1px solid #4CAF50;
            border-radius: 5px;
            overflow-y: auto;
            max-height: 300px;
        }
        .log-entry {
            padding: 8px 15px;
            border-bottom: 1px solid #333;
            font-size: 14px;
            font-family: monospace;
        }
        .log-entry:last-child {
            border-bottom: none;
        }
        .log-entry.success {
            color: #4CAF50;
        }
        .status {
            padding: 10px;
            border-radius: 5px;
            text-align: center;
            margin-bottom: 20px;
            font-weight: bold;
        }
        .status.active {
            background: #4CAF50;
            color: #000;
        }
        .status.inactive {
            background: #f44336;
            color: #fff;
        }
        .instructions {
            background: #2a2a2a;
            border-left: 4px solid #2196F3;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📷 License Plate Reader - Remote Stream</h1>
        
        <div id="status" class="status active">
            🟢 LIVE - Receiving stream...
        </div>
        
        <div class="instructions">
            <strong>How to use:</strong><br>
            • <span style="color: #FFEB3B;">Yellow boxes</span> = Detected regions<br>
            • <span style="color: #4CAF50;">Green boxes</span> = Recognized plates<br>
            • Scans every 2 seconds • Results logged to plate_log.txt
        </div>
        
        <div class="video-container">
            <img 
                id="video" 
                src="/video_feed" 
                alt="Camera Feed" 
                onerror="document.getElementById('status').className='status inactive'; document.getElementById('status').textContent='🔴 ERROR - Stream disconnected'"
                onload="document.getElementById('status').className='status active'; document.getElementById('status').textContent='🟢 LIVE - Receiving stream...'"
            />
        </div>
        
        <div class="stats">
            <div class="stat-box">
                <div class="stat-label">Detection Cycles</div>
                <div class="stat-value" id="detection-count">0</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Last Plate</div>
                <div class="stat-value" id="last-plate" style="font-size: 18px;">None</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Regions Detected</div>
                <div class="stat-value" id="detected-count">0</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Valid Plates Found</div>
                <div class="stat-value" id="valid-count">0</div>
            </div>
        </div>
        
        <div>
            <h2 style="border-bottom: 2px solid #4CAF50; padding-bottom: 10px;">Latest Detections</h2>
            <div class="log-box" id="log-box">
                <div class="log-entry">Waiting for detections...</div>
            </div>
        </div>
    </div>
    
    <script>
        // Update stats every 500ms
        setInterval(function() {
            fetch('/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('detection-count').textContent = data.detection_count;
                    document.getElementById('last-plate').textContent = data.last_plate;
                    document.getElementById('detected-count').textContent = data.detected_boxes;
                    document.getElementById('valid-count').textContent = data.valid_plates;
                })
                .catch(err => console.error('Error fetching stats:', err));
        }, 500);
    </script>
</body>
</html>
"""


def init_log_file():
    """Initialize the log file with header if it doesn't exist."""
    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'w') as f:
            f.write("Registration Number | Timestamp\n")
            f.write("=" * 50 + "\n")


def cleanup_old_images():
    """Delete image files that are no longer in the buffer."""
    try:
        all_files = sorted([f for f in os.listdir(IMAGES_DIR) if f.endswith('.jpg')])
        buffer_filenames = [os.path.basename(f) for f in image_buffer]
        
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
    
    # Update last plate
    with stats_lock:
        latest_stats["last_plate"] = f"{plate_number} ({confidence:.0f}%)"
    
    # Save frame if provided
    if frame is not None:
        frame_with_box = frame.copy()
        if rect is not None:
            x, y, w, h = rect
            cv2.rectangle(frame_with_box, (x, y), (x+w, y+h), (0, 255, 0), 2)
            text_label = f"{plate_number} ({confidence:.0f}%)"
            text_pos = (x, max(y - 5, 25))
            cv2.putText(frame_with_box, text_label, text_pos, 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        image_filename = f"{IMAGES_DIR}/{timestamp_file}_{plate_number}.jpg"
        cv2.imwrite(image_filename, frame_with_box)
        image_buffer.append(image_filename)
        cleanup_old_images()
        print(f"  Saved: {image_filename}")


def extract_plate_text(frame, rect):
    """Extract text from detected region using Tesseract OCR."""
    try:
        x, y, w, h = rect
        region = frame[y:y+h, x:x+w]
        
        if region.size == 0:
            return None, 0
        
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
        
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY, 11, 2)
        
        scale = max(5, int(400 / max(w, h)))
        upscaled = cv2.resize(binary, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        upscaled = cv2.fastNlMeansDenoising(upscaled, h=10)
        
        config = '--psm 8 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        text = pytesseract.image_to_string(upscaled, config=config, timeout=5).strip().upper()
        
        if text and len(text) >= 3:
            confidence = min(100, len(text) * 15)
            return text, confidence
    except Exception as e:
        pass
    
    return None, 0


def is_likely_plate(text):
    """Check if text looks like a license plate."""
    if not text or len(text) < 3:
        return False
    
    has_letter = any(c.isalpha() for c in text)
    has_digit = any(c.isdigit() for c in text)
    
    return has_letter and has_digit


def draw_ui_overlay(frame, detection_count, is_scanning, detected_rectangles, valid_plates):
    """Draw UI overlay with status information and detection rectangles."""
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
    
    scan_status = "[SCANNING]" if is_scanning else "[READY]"
    status_text = f"Detection #{detection_count} {scan_status}"
    cv2.putText(display_frame, status_text, (10, 22), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
    
    return display_frame


def capture_and_analyze():
    """Capture and analyze frames."""
    global frame_buffer
    
    cap = cv2.VideoCapture(CAMERA_INDEX)
    
    if not cap.isOpened():
        print(f"Error: Cannot access camera at index {CAMERA_INDEX}")
        return
    
    print(f"Camera opened. Capturing every {CAPTURE_INTERVAL} seconds...")
    print(f"Web server running at http://localhost:{HTTP_PORT}")
    print(f"Images saved to: {IMAGES_DIR}/\n")
    
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
            is_scanning = (current_time - last_capture_time) >= CAPTURE_INTERVAL
            detected_rectangles = []
            valid_plates = []
            
            if is_scanning:
                last_capture_time = current_time
                detection_count += 1
                
                try:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    gray = cv2.bilateralFilter(gray, 11, 17, 17)
                    edges = cv2.Canny(gray, 30, 200)
                    
                    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
                    edges = cv2.dilate(edges, kernel, iterations=3)
                    
                    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                    
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Detection #{detection_count}: Found {len(contours)} contours", end="")
                    
                    detections_found = False
                    
                    for contour in contours:
                        x, y, w, h = cv2.boundingRect(contour)
                        
                        if w < 20 or h < 10:
                            continue
                        
                        ratio = w / h if h > 0 else 0
                        
                        if 2 < ratio < 5 and w > 30 and h > 10:
                            area = w * h
                            contour_area = cv2.contourArea(contour)
                            fill_ratio = contour_area / area if area > 0 else 0
                            
                            if 0.4 < fill_ratio < 0.95:
                                detected_rectangles.append((x, y, w, h))
                                
                                plate_text, ocr_conf = extract_plate_text(frame, (x, y, w, h))
                                
                                if plate_text:
                                    print(f" -> Found: '{plate_text}'", end="")
                                
                                if plate_text and is_likely_plate(plate_text) and ocr_conf >= CONFIDENCE_THRESHOLD:
                                    detections_found = True
                                    valid_plates.append((x, y, w, h, plate_text, ocr_conf))
                                    
                                    if plate_text != last_detected_plate or (current_time - last_detection_time) > 5:
                                        log_plate(plate_text, ocr_conf, frame, (x, y, w, h))
                                        last_detected_plate = plate_text
                                        last_detection_time = current_time
                    
                    if not detections_found:
                        print(" [no valid plates]", end="")
                    
                    print()
                    
                    # Update stats
                    with stats_lock:
                        latest_stats["detection_count"] = detection_count
                        latest_stats["detected_boxes"] = len(detected_rectangles)
                        latest_stats["valid_plates"] = len(valid_plates)
                    
                except Exception as e:
                    print(f"Detection error: {e}", file=sys.stderr)
                    continue
            
            # Draw overlay and store for streaming
            display_frame = draw_ui_overlay(frame, detection_count, is_scanning, detected_rectangles, valid_plates)
            
            with frame_lock:
                frame_buffer = display_frame.copy()
    
    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cap.release()
        print(f"Results saved to {OUTPUT_FILE}")


def generate_frames():
    """Generate MJPEG frames for streaming."""
    while True:
        with frame_lock:
            if frame_buffer is not None:
                ret, buffer = cv2.imencode('.jpg', frame_buffer)
                if ret:
                    frame = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n'
                           b'Content-Length: ' + str(len(frame)).encode() + b'\r\n\r\n' + frame + b'\r\n')
        
        time.sleep(0.033)  # ~30 FPS


@app.route('/')
def index():
    """Serve main HTML page."""
    return render_template_string(HTML_TEMPLATE)


@app.route('/video_feed')
def video_feed():
    """Stream video as MJPEG."""
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/stats')
def get_stats():
    """Get current statistics as JSON."""
    with stats_lock:
        return {
            "detection_count": latest_stats["detection_count"],
            "last_plate": latest_stats["last_plate"],
            "detected_boxes": latest_stats["detected_boxes"],
            "valid_plates": latest_stats["valid_plates"]
        }


if __name__ == "__main__":
    # Start capture thread
    capture_thread = threading.Thread(target=capture_and_analyze, daemon=True)
    capture_thread.start()
    
    # Start Flask server
    app.run(host='0.0.0.0', port=HTTP_PORT, debug=False, use_reloader=False)
