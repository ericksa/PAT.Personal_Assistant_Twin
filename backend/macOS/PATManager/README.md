# PAT Command Center (macOS)

A native macOS application to manage your Personal Assistant Twin (PAT) backend services.

## Features

- **Service Orchestration**: One-click start/stop for all PAT microservices.
- **Real-time Monitoring**: Visual status indicators (Green/Yellow/Red) and PID tracking.
- **Unified Logging**: Streamed logs from all Python processes into a single console.
- **Menu Bar Integration**: Quick-access tray icon for controlling PAT from any app.
- **Voice Assistant**: Built-in audio listener that connects directly to your local Whisper service.
- **Browser Integration**: Native buttons to launch the Teleprompter, Grafana, and n8n.

## Prerequisites

- macOS 14.0 (Sonoma) or later.
- Python 3.8+ installed at `/usr/bin/python3`.
- Backend code located at `/Users/adamerickson/Projects/PAT/backend`.

## Installation

1. Open `PATManager.xcodeproj` in **Xcode**.
2. Ensure your backend directory path is correct in `ProcessManager.swift`.
3. Press `Cmd + R` to build and run.

## Usage

### Managing Services
Click the **Start** or **Stop** buttons next to any service in the Dashboard. Use **Start All** in the toolbar to spin up the entire stack at once.

### Voice Commands
Click the **Microphone** button to start recording. Click again to stop. The app will automatically transcribe the audio using Whisper and forward the command to PAT Core.

### Logs
Switch to the **Console Logs** tab to see real-time output from all running services. You can filter logs by keyword to debug specific issues.

## Development

The app is built using **SwiftUI 6.0** and uses native `Process` objects to manage background tasks. Logs are captured via `Pipe` and handled asynchronously.
