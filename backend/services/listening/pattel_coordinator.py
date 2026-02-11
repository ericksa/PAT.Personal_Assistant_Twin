#!/usr/bin/env python3
"""
PAT Teleprompter Coordinator with WebSocket Integration
Starts overlay app, listening service, and WebSocket bridge for real-time text pushing
"""

import subprocess
import signal
import sys
import os
import time
import threading
from pathlib import Path
import asyncio
import websockets
import json

# Global references to processes
overlay_process = None
listener_process = None
websocket_server = None
connected_clients = set()


class WebSocketBridge:
    """Bridge between Python listener and Swift overlay via WebSocket"""

    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        self.server = None

    async def register_client(self, websocket):
        """Register a new WebSocket client"""
        connected_clients.add(websocket)
        print(f"🌐 WebSocket client connected. Total clients: {len(connected_clients)}")

    async def unregister_client(self, websocket):
        """Unregister a disconnected client"""
        connected_clients.discard(websocket)
        print(
            f"🌐 WebSocket client disconnected. Total clients: {len(connected_clients)}"
        )

    async def broadcast_message(self, message):
        """Broadcast message to all connected clients"""
        if connected_clients:
            # Prepare message for overlay
            message_data = {
                "type": "transcription",
                "text": message,
                "timestamp": time.time(),
            }

            # Send to all connected clients
            disconnected = set()
            for client in connected_clients:
                try:
                    await client.send(json.dumps(message_data))
                except websockets.exceptions.ConnectionClosed:
                    disconnected.add(client)
                except Exception as e:
                    print(f"❌ Error sending to client: {e}")
                    disconnected.add(client)

            # Clean up disconnected clients
            for client in disconnected:
                connected_clients.discard(client)

            print(
                f"📡 Broadcasted to {len(connected_clients)} clients: {message[:50]}..."
            )

    async def handle_client(self, websocket, path):
        """Handle incoming WebSocket connections"""
        await self.register_client(websocket)
        try:
            async for message in websocket:
                # Handle incoming messages if needed
                data = json.loads(message)
                print(f"📨 Received from client: {data}")
        finally:
            await self.unregister_client(websocket)

    async def start_server(self):
        """Start the WebSocket server"""
        print(f"🌐 Starting WebSocket server on ws://{self.host}:{self.port}")
        self.server = await websockets.serve(self.handle_client, self.host, self.port)
        print(f"✅ WebSocket server running on ws://{self.host}:{self.port}")

    async def stop_server(self):
        """Stop the WebSocket server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            print("🛑 WebSocket server stopped")


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Shutting down PAT Teleprompter components...")
    cleanup()
    sys.exit(0)


def cleanup():
    """Clean up all running processes"""
    global overlay_process, listener_process, websocket_server

    # Stop WebSocket server
    if websocket_server:
        asyncio.run(websocket_server.stop_server())

    # Kill overlay
    if overlay_process and overlay_process.poll() is None:
        print("🛑 Stopping overlay...")
        overlay_process.terminate()
        try:
            overlay_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            overlay_process.kill()

    # Kill listener
    if listener_process and listener_process.poll() is None:
        print("🛑 Stopping listening service...")
        listener_process.terminate()
        try:
            listener_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            listener_process.kill()

    # Kill any remaining processes
    subprocess.run(["pkill", "-f", "PATOverlay"], capture_output=True)
    subprocess.run(["pkill", "-f", "live_interview_listener"], capture_output=True)


def start_teleprompter():
    """Start the complete teleprompter system"""
    global overlay_process, listener_process, websocket_server

    print("🚀 PAT Teleprompter (PATTEL) starting...")
    print("=" * 60)

    # Check if all components exist
    listening_script = "/Users/adamerickson/Projects/PAT/backend/services/listening/live_interview_listener.py"
    overlay_app = "/Users/adamerickson/Projects/PAT/frontend/swiftclient/SwiftOverlayExported/PATOverlay.app"

    if not Path(listening_script).exists():
        print(f"❌ Listening service not found: {listening_script}")
        return False

    if not Path(overlay_app).exists():
        print(f"❌ Overlay app not found: {overlay_app}")
        return False

    # Start WebSocket server in background thread
    print("🌐 Starting WebSocket bridge...")
    websocket_server = WebSocketBridge()

    def run_websocket():
        asyncio.run(websocket_server.start_server())

    ws_thread = threading.Thread(target=run_websocket, daemon=True)
    ws_thread.start()

    # Wait for WebSocket server to start
    time.sleep(1)

    # Start listening service
    print("🎙️  Starting interview listening service...")
    listener_process = subprocess.Popen(
        ["python3", listening_script],
        cwd="/Users/adamerickson/Projects/PAT/backend/services/listening",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Monitor listener output for WebSocket connection
    def monitor_listener():
        for line in iter(listener_process.stdout.readline, ""):
            if "WebSocket" in line or "transcription" in line:
                # Forward transcriptions through WebSocket
                asyncio.run(websocket_server.broadcast_message(line.strip()))

    monitor_thread = threading.Thread(target=monitor_listener, daemon=True)
    monitor_thread.start()

    # Start overlay
    print("🎬 Launching PAT overlay...")
    overlay_process = subprocess.Popen(["open", "-a", overlay_app])

    print("=" * 60)
    print("✅ PAT Teleprompter is now running!")
    print(f"   • WebSocket server on ws://localhost:8765")
    print(f"   • Listening service: Python PID {listener_process.pid}")
    print(f"   • Overlay: PATOverlay.app")
    print("=" * 60)
    print("💡 Ready to receive transcriptions via WebSocket")
    print("📱 You can now push text from PATclient to the teleprompter!")
    print("=" * 60)

    return True


def main():
    """Main entry point"""
    # Setup signal handler
    signal.signal(signal.SIGINT, signal_handler)

    # Start teleprompter
    if not start_teleprompter():
        print("❌ Failed to start PAT Teleprompter")
        cleanup()
        sys.exit(1)

    # Keep main thread alive
    print("💬 Waiting for transcriptions... Press Ctrl+C to stop")
    print("-" * 60)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping PAT Teleprompter...")
    finally:
        cleanup()


if __name__ == "__main__":
    main()
