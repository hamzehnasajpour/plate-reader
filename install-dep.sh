#!/bin/bash
#
# Dependency Installation Script for Plate Reader
# This script installs all required system and Python dependencies
#

set -e

echo "=========================================="
echo "Plate Reader - Dependency Installation"
echo "=========================================="
echo ""

# Check if running on Linux
if [[ ! "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Warning: This script is designed for Linux. macOS users should use Homebrew."
fi

echo "[1/3] Updating system packages..."
sudo apt-get update

echo "[2/3] Installing system dependencies..."
sudo apt-get install -y \
    openalpr \
    openalpr-daemon \
    libopenalpr-dev \
    python3-dev \
    python3-pip \
    python3-venv \
    build-essential \
    cmake \
    git

echo "[3/3] Creating Python virtual environment and installing Python packages..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install Python dependencies
pip install -r requirements.txt

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
