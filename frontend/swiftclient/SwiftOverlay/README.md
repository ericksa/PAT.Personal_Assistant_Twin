# PAT Interview Overlay

A translucent macOS overlay app for displaying PAT (Personal Assistant Twin) interview responses.

## Features

- **Translucent Design**: Semi-transparent overlay that stays on top of other windows
- **Real-time Updates**: Connects to PAT backend via WebSocket to display live responses
- **Customizable**: Adjustable opacity and font size
- **Draggable**: Move the overlay anywhere on your screen
- **Hide/Show**: Quickly hide the window when not needed

## Requirements

- macOS 12.0 or later
- PAT backend services running (agent, teleprompter, etc.)

## Installation

### Option 1: Build with Swift Package Manager

```bash
cd SwiftOverlay
./build.sh
```

### Option 2: Open in Xcode

1. Open `PATOverlay.xcodeproj` in Xcode
2. Select your development team (if signing is required)
3. Build and run the project

## Usage

1. Start your PAT backend services:
   ```bash
   docker-compose up -d
   ```

2. Run the PAT Overlay app
3. The app will automatically connect to `ws://localhost:8005/ws`
4. Adjust opacity and font size using the sliders
5. Use the eye icon to hide the window temporarily
6. Use "Float on Top" from the menu to keep it above other windows

## Customization

- **Opacity**: Adjust transparency level (0.3 to 1.0)
- **Font Size**: Change text size (12pt to 48pt)
- **Position**: Drag the window to reposition

## Troubleshooting

- If WebSocket connection fails, ensure PAT services are running
- Check that `http://localhost:8005` is accessible
- Verify firewall settings if connection issues persist

## Integration with PAT System

The overlay app integrates seamlessly with the PAT interview system:

1. Live interview listener captures audio
2. Whisper transcribes speech to text
3. Agent service processes questions and generates responses
4. Teleprompter service broadcasts responses via WebSocket
5. Overlay app displays responses in real-time

For best results during Google Meet interviews:
- Position the overlay where you can easily see it
- Adjust opacity so it's visible but not distracting
- Keep font size large enough to read comfortably