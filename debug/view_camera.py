#!/usr/bin/env python3
"""
Camera viewer with mobile-like zoom
- Arrow keys to move zoom region
- +/- keys to zoom in/out
- Shows only the zoomed area (cropped)
- Saves/loads zoom settings
"""

import cv2
import sys
import json
import os

CAMERA_INDEX = 0
ZOOM_MIN = 1.0
ZOOM_MAX = 5.0
ZOOM_STEP = 0.5
MOVE_STEP = 20  # pixels per arrow key press
CONFIG_FILE = "zoom_config.json"

def load_config():
    """Load zoom settings from file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
    return None

def save_config(config):
    """Save zoom settings to file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save config: {e}")

def main():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    
    if not cap.isOpened():
        print(f"❌ Error: Cannot access camera at index {CAMERA_INDEX}")
        return
    
    # Set to maximum resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    
    # Get actual resolution
    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"📷 Camera opened at {CAMERA_INDEX}")
    print(f"   Resolution: {actual_width}×{actual_height}")
    print("\nControls:")
    print("  ↑↓←→ : Move zoom region")
    print("  +/- : Zoom in/out")
    print("  q   : Quit (saves settings)\n")
    
    cv2.namedWindow("Camera Feed", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Camera Feed", 960, 720)
    
    frame_count = 0
    
    # Load previous zoom settings or use defaults
    saved_config = load_config()
    if saved_config and saved_config.get('width') == actual_width and saved_config.get('height') == actual_height:
        zoom_level = saved_config.get('zoom_level', 1.0)
        zoom_region_x = saved_config.get('zoom_region_x', 0)
        zoom_region_y = saved_config.get('zoom_region_y', 0)
        print(f"✓ Loaded previous zoom settings: {zoom_level:.1f}x")
    else:
        zoom_level = 1.0
        zoom_region_width = int(actual_width / zoom_level)
        zoom_region_height = int(actual_height / zoom_level)
        zoom_region_x = (actual_width - zoom_region_width) // 2
        zoom_region_y = (actual_height - zoom_region_height) // 2
    
    try:
        while True:
            ret, frame = cap.read()
            
            if not ret:
                print("❌ Failed to capture frame")
                break
            
            frame_count += 1
            
            # Calculate zoom region dimensions
            zoom_region_width = int(actual_width / zoom_level)
            zoom_region_height = int(actual_height / zoom_level)
            
            # Extract zoom region
            x1 = max(0, zoom_region_x)
            y1 = max(0, zoom_region_y)
            x2 = min(actual_width, zoom_region_x + zoom_region_width)
            y2 = min(actual_height, zoom_region_y + zoom_region_height)
            
            cropped = frame[y1:y2, x1:x2]
            
            # Resize cropped region to display size (720p)
            display_frame = cv2.resize(cropped, (960, 720))
            
            # Add overlay info - show resolution, zoom, and scope
            info_text = f"Res: {actual_width}×{actual_height} | Zoom: {zoom_level:.1f}x | Scope: {x2-x1}×{y2-y1}"
            cv2.putText(display_frame, info_text, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 200), 2)
            cv2.putText(display_frame, f"Frame: {frame_count} | Pos: ({x1}, {y1})", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 200, 255), 1)
            cv2.putText(display_frame, "Arrows: Move | +/-: Zoom | q: Quit", (10, 700),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            cv2.imshow("Camera Feed", display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                # Save settings before quitting
                config = {
                    'width': actual_width,
                    'height': actual_height,
                    'zoom_level': zoom_level,
                    'zoom_region_x': zoom_region_x,
                    'zoom_region_y': zoom_region_y
                }
                save_config(config)
                print(f"\n✓ Saved zoom settings: {zoom_level:.1f}x at ({zoom_region_x}, {zoom_region_y})")
                print("✓ Stopped")
                break
            elif key == ord('+') or key == ord('='):
                # Zoom in - decrease region size
                zoom_level = min(ZOOM_MAX, zoom_level + ZOOM_STEP)
                old_width = zoom_region_width
                old_height = zoom_region_height
                zoom_region_width = int(actual_width / zoom_level)
                zoom_region_height = int(actual_height / zoom_level)
                # Keep center of region
                zoom_region_x += (old_width - zoom_region_width) // 2
                zoom_region_y += (old_height - zoom_region_height) // 2
                print(f"🔍 Zoom: {zoom_level:.1f}x")
            elif key == ord('-') or key == ord('_'):
                # Zoom out - increase region size
                zoom_level = max(ZOOM_MIN, zoom_level - ZOOM_STEP)
                old_width = zoom_region_width
                old_height = zoom_region_height
                zoom_region_width = int(actual_width / zoom_level)
                zoom_region_height = int(actual_height / zoom_level)
                # Keep center of region
                zoom_region_x += (old_width - zoom_region_width) // 2
                zoom_region_y += (old_height - zoom_region_height) // 2
                print(f"🔍 Zoom: {zoom_level:.1f}x")
            elif key == 82:  # Up arrow
                zoom_region_y = max(0, zoom_region_y - MOVE_STEP)
            elif key == 84:  # Down arrow
                zoom_region_y = min(actual_height - zoom_region_height, zoom_region_y + MOVE_STEP)
            elif key == 81:  # Left arrow
                zoom_region_x = max(0, zoom_region_x - MOVE_STEP)
            elif key == 83:  # Right arrow
                zoom_region_x = min(actual_width - zoom_region_width, zoom_region_x + MOVE_STEP)
    
    except KeyboardInterrupt:
        print("\n✓ Stopped")
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
    
    try:
        while True:
            ret, frame = cap.read()
            
            if not ret:
                print("❌ Failed to capture frame")
                break
            
            frame_count += 1
            
            # Extract zoom region
            x1 = max(0, zoom_region_x)
            y1 = max(0, zoom_region_y)
            x2 = min(actual_width, zoom_region_x + zoom_region_width)
            y2 = min(actual_height, zoom_region_y + zoom_region_height)
            
            cropped = frame[y1:y2, x1:x2]
            
            # Resize cropped region to display size (720p)
            display_frame = cv2.resize(cropped, (960, 720))
            
            # Add overlay info
            info_text = f"Frame: {frame_count} | Zoom: {zoom_level:.1f}x | Viewing: {x2-x1}×{y2-y1}"
            cv2.putText(display_frame, info_text, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 200), 2)
            cv2.putText(display_frame, "Arrows: Move | +/-: Zoom | q: Quit", (10, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
            
            cv2.imshow("Camera Feed", display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\n✓ Stopped")
                break
            elif key == ord('+') or key == ord('='):
                # Zoom in - decrease region size
                zoom_level = min(ZOOM_MAX, zoom_level + ZOOM_STEP)
                old_width = zoom_region_width
                old_height = zoom_region_height
                zoom_region_width = int(actual_width / zoom_level)
                zoom_region_height = int(actual_height / zoom_level)
                # Keep center of region
                zoom_region_x += (old_width - zoom_region_width) // 2
                zoom_region_y += (old_height - zoom_region_height) // 2
                print(f"🔍 Zoom: {zoom_level:.1f}x")
            elif key == ord('-') or key == ord('_'):
                # Zoom out - increase region size
                zoom_level = max(ZOOM_MIN, zoom_level - ZOOM_STEP)
                old_width = zoom_region_width
                old_height = zoom_region_height
                zoom_region_width = int(actual_width / zoom_level)
                zoom_region_height = int(actual_height / zoom_level)
                # Keep center of region
                zoom_region_x += (old_width - zoom_region_width) // 2
                zoom_region_y += (old_height - zoom_region_height) // 2
                print(f"🔍 Zoom: {zoom_level:.1f}x")
            elif key == 82:  # Up arrow
                zoom_region_y = max(0, zoom_region_y - MOVE_STEP)
            elif key == 84:  # Down arrow
                zoom_region_y = min(actual_height - zoom_region_height, zoom_region_y + MOVE_STEP)
            elif key == 81:  # Left arrow
                zoom_region_x = max(0, zoom_region_x - MOVE_STEP)
            elif key == 83:  # Right arrow
                zoom_region_x = min(actual_width - zoom_region_width, zoom_region_x + MOVE_STEP)
    
    except KeyboardInterrupt:
        print("\n✓ Stopped")
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
