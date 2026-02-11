#!/usr/bin/env python3
"""
PAT Teleprompter Coordinator
Starts both the Swift overlay and the Python listening service together
"""

import subprocess
import signal
import sys
import os
import time
from pathlib import Path


def signal_handler(sig, frame):
    print("\n🛑 Shutting down PAT teleprompter components...")
    sys.exit(0)


def main():
    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, signal_handler)

    print("🚀 Starting PAT Teleprompter...")

    # Get script directory
    script_dir = Path(__file__).parent
    listening_service_path = script_dir / "live_interview_listener.py"

    # Check if listening service exists
    if not listening_service_path.exists():
        print(f"❌ Listening service not found at: {listening_service_path}")
        return

    processes = []

    try:
        # Start listening service
        print("🎙️  Starting interview listening service...")
        listening_process = subprocess.Popen(
            ["python3", str(listening_service_path)], cwd=script_dir
        )
        processes.append(listening_process)

        print("🎬 Starting Swift overlay...")
        overlay_path = "../SwiftOverlayExported/PATOverlay.app"
        if Path(overlay_path).exists():
            overlay_process = subprocess.Popen(["open", overlay_path])
            processes.append(overlay_process)
        else:
            print(f"⚠️  Overlay not found at: {overlay_path}")

        print("✅ All components started successfully!")
        print("💡 Press Ctrl+C to stop all components")

        # Wait for processes
        for process in processes:
            process.wait()

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        # Clean up processes
        for process in processes:
            try:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
            except Exception as e:
                print(f"Error stopping process: {e}")


if __name__ == "__main__":
    main()
