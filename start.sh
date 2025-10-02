#!/bin/bash

# Blockchain Tracking System Startup Script

echo "🔗 Blockchain Tracking System"
echo "=============================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if pip is available
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    echo "❌ pip is required but not installed."
    exit 1
fi

# Install dependencies if requirements.txt exists and packages aren't installed
if [ -f "requirements.txt" ]; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    echo ""
fi

# Create log directory if it doesn't exist
mkdir -p logs

echo "🚀 Starting Blockchain Tracker..."
echo "📊 Dashboard will be available at: http://localhost:8050"
echo ""
echo "Press Ctrl+C to stop the system"
echo "=============================="

# Start the application
python3 run.py
