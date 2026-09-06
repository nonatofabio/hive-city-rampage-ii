#!/bin/bash
# Local build script for Hive City Rampage
# Tests PyInstaller build before pushing to CI/CD

set -e  # Exit on error

echo "🔨 Building Hive City Rampage..."
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Creating one..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install/upgrade dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install "pygame>=2.6.0" "pyinstaller>=6.0.0"

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/

# Run PyInstaller
echo "⚙️  Running PyInstaller..."
pyinstaller hive_city_rampage.spec

# Check if build succeeded
if [ -f "dist/HiveCityRampage" ] || [ -d "dist/HiveCityRampage.app" ] || [ -f "dist/HiveCityRampage.exe" ]; then
    echo ""
    echo "✅ Build successful!"
    echo ""
    echo "📁 Build output location:"
    ls -lh dist/
    echo ""
    echo "🎮 To test the build:"
    if [ -d "dist/HiveCityRampage.app" ]; then
        echo "   open dist/HiveCityRampage.app"
    elif [ -f "dist/HiveCityRampage.exe" ]; then
        echo "   dist/HiveCityRampage.exe"
    else
        echo "   cd dist && ./HiveCityRampage"
    fi
else
    echo ""
    echo "❌ Build failed! Check the output above for errors."
    exit 1
fi
