#!/bin/bash
#
# Dependency Installation Script for Plate Reader
# This script installs all required system and Python dependencies
# Uses YOLOv8 + EasyOCR for license plate detection and OCR
#

set -e

echo "=========================================="
echo "Plate Reader - Dependency Installation"
echo "=========================================="
echo ""

echo "[1/2] Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    python3-dev \
    python3-pip \
    python3-venv \
    build-essential \
    libatlas-base-dev \
    libjasper-dev \
    libtiff5 \
    libjasper1 \
    libharfbuzz0b \
    libwebp6 \
    libtiff5 \
    libjasper1 \
    libharfbuzz0b \
    libwebp6

echo "[2/2] Creating Python virtual environment and installing Python packages..."

# Navigate to project directory
cd /home/hamzeh/dev/plate-reader

# Remove existing venv to ensure clean installation
if [ -d "venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf venv
fi

# Create fresh virtual environment
python3 -m venv venv
echo "✓ Virtual environment created"

# Activate virtual environment
source venv/bin/activate

# Upgrade pip, setuptools, and wheel
pip install --upgrade pip setuptools wheel

# Install Python dependencies
echo "Installing Python packages (this may take a few minutes)..."
pip install -r requirements.txt

# Download YOLO model on first install
echo "Downloading YOLO model..."
python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

echo ""
echo "=========================================="
echo "✓ Installation Complete!"
echo "=========================================="
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To start the plate reader, run:"
echo "  python3 main.py"
echo ""

