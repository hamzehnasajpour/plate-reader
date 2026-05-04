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

echo "[1/4] Updating system packages..."
sudo apt-get update

echo "[2/4] Installing build dependencies..."
sudo apt-get install -y \
    python3-dev \
    python3-pip \
    python3-venv \
    build-essential \
    cmake \
    git \
    curl \
    wget \
    libcurl4-openssl-dev \
    libtesseract-dev \
    libleptonica-dev \
    libopencv-dev \
    python3-opencv \
    liblog4cplus-dev

echo "[3/4] Installing OpenALPR from source..."
cd /tmp

# Clone OpenALPR repository
if [ ! -d "openalpr" ]; then
    git clone https://github.com/openalpr/openalpr.git
fi

cd openalpr/src
mkdir -p build
cd build

# Build and install OpenALPR
cmake -D CMAKE_BUILD_TYPE=Release ..
make -j$(nproc)
sudo make install

# Install Python bindings from source
cd ../python
sudo python3 setup.py install

# Configure library path
sudo ldconfig

echo "✓ OpenALPR installed successfully"

echo "[4/4] Creating Python virtual environment and installing Python packages..."

# Navigate back to project directory
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

# Install numpy first (required for OpenCV)
pip install numpy==1.23.5

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
