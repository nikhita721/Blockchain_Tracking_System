#!/usr/bin/env python3
"""
Convenience script to run both the blockchain tracker and dashboard
"""

import subprocess
import sys
import time
import signal
import os
from threading import Thread

def run_tracker():
    """Run the main blockchain tracker"""
    print("🔗 Starting Blockchain Tracker...")
    try:
        subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        print("Tracker stopped by user")
    except Exception as e:
        print(f"Tracker error: {e}")

def run_dashboard():
    """Run the web dashboard"""
    print("📊 Starting Web Dashboard...")
    # Wait a bit for the tracker to start and create the database
    time.sleep(3)
    try:
        subprocess.run([sys.executable, "dashboard.py"], check=True)
    except KeyboardInterrupt:
        print("Dashboard stopped by user")
    except Exception as e:
        print(f"Dashboard error: {e}")

def main():
    """Main function to run both components"""
    print("🚀 Blockchain Tracking System")
    print("=" * 50)
    print("Starting both tracker and dashboard...")
    print("Dashboard will be available at: http://localhost:8050")
    print("Press Ctrl+C to stop both services")
    print("=" * 50)
    
    # Create threads for both processes
    tracker_thread = Thread(target=run_tracker, daemon=True)
    dashboard_thread = Thread(target=run_dashboard, daemon=True)
    
    try:
        # Start both threads
        tracker_thread.start()
        dashboard_thread.start()
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Blockchain Tracking System...")
        print("Stopping all services...")
        
        # The daemon threads will be terminated when main thread exits
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
