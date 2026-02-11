#!/usr/bin/env python3
"""
PAT Teleprompter WebSocket Integration Script
Run this script to start the teleprompter system with WebSocket support
"""

import subprocess
import sys
import time
import asyncio
import websockets
import json
import threading
from pathlib import Path


def start_listening_service():
    """Start the Python listening service"""
    script_path = "/Users/adamerickson/Projects/PAT/backend/services/listening/live_interview_listener.py"
    if not Path(script_path).exists():
        print(f"❌ Listening service not found at: {script_path}")
        return False

    print("🎙️  Starting interview listening service...")
    process = subprocess.Popen(
        ["python3", script_path],
        cwd="/Users/adamerickson/Projects/PAT/backend/services/listening",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Check if started successfully
    time.sleep(3)
    if process.poll() is None:
        print(f"✅ Listening service started (PID: {process.pid})")
        return True
    else:
        print("❌ Listening service failed to start")
        return False


def start_overlay():
    """Start the Swift overlay"""
    overlay_path = "/Users/adamerickson/Projects/PAT/frontend/swiftclient/SwiftOverlay/PATOverlay.app"
    if not Path(overlay_path).exists():
        print(f"❌ Overlay not found at: {overlay_path}")
        return False

    print("🎬 Launching PAT overlay...")
    subprocess.Popen(["open", "-a", overlay_path])
    print("✅ Overlay launched")
    return True


async def websocket_server():
    """Start WebSocket server for real-time communication"""
    print("🌐 Starting WebSocket server on ws://localhost:8765")

    connected_clients = set()

    async def handle_client(websocket, path):
        connected_clients.add(websocket)
        print(f"🌐 Client connected. Total clients: {len(connected_clients)}")

        try:
            # Send welcome message
            await websocket.send(
                json.dumps(
                    {
                        "type": "system",
                        "message": "Connected to PAT Teleprompter",
                        "timestamp": time.time(),
                    }
                )
            )

            # Handle incoming messages
            async for message in websocket:
                data = json.loads(message)
                print(f"📨 Received: {data}")
        except:
            pass
        finally:
            connected_clients.discard(websocket)
            print(
                f"🌐 Client disconnected. Total clients: {len(connected_clients) - 1}"
            )

    async def broadcast_message(message):
        """Broadcast message to all connected clients"""
        if connected_clients:
            message_data = {
                "type": "transcription",
                "text": message,
                "timestamp": time.time(),
            }

            disconnected = set()
            for client in connected_clients:
                try:
                    await client.send(json.dumps(message_data))
                except:
                    disconnected.add(client)

            for client in disconnected:
                connected_clients.discard(client)

            print(
                f"📡 Broadcast to {len(connected_clients)} clients: {message[:50]}..."
            )

    # Start server
    server = await websockets.serve(handle_client, "localhost", 8765)
    print("✅ WebSocket server running on ws://localhost:8765")

    # Keep server running
    try:
        await server.wait_closed()
    except KeyboardInterrupt:
        pass


def main():
    """Main entry point"""
    print("🚀 PAT Teleprompter with WebSocket Integration starting...")
    print("=" * 60)

    # Start listening service
    if not start_listening_service():
        return False

    # Start overlay
    if not start_overlay():
        return False

    # Start WebSocket server in background thread
    print("🌐 Starting WebSocket bridge...")

    def run_websocket():
        asyncio.run(websocket_server())

    websocket_thread = threading.Thread(target=run_websocket, daemon=True)
    websocket_thread.start()

    time.sleep(2)

    print("=" * 60)
    print("✅ PAT Teleprompter is now running!")
    print("   • WebSocket server on ws://localhost:8765")
    print("   • Listening service transcribing audio")
    print("   • Overlay displaying teleprompter")
    print("=" * 60)
    print("💡 Test the WebSocket with:")
    print("   websocat ws://localhost:8765")
    print("=" * 60)
    print("Press Ctrl+C to stop")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping PAT Teleprompter...")

    return True


if __name__ == "__main__":
    print("Starting PAT Teleprompter...")
    if main():
        print("✅ PAT Teleprompter started successfully")
    else:
        print("❌ Failed to start PAT Teleprompter")
