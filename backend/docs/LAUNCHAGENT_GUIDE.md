# macOS LaunchAgent Setup Guide

To run PAT backend services automatically when you log into your Mac, you can set up a macOS LaunchAgent.

## Prerequisites
- Python 3.8+ installed.
- All dependencies installed in system Python or a global venv.
- Docker Desktop running (if using database containers).

## Steps

### 1. Create the LaunchAgent Plist File
Create a file at `~/Library/LaunchAgents/com.pat.backend.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.pat.backend</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>-m</string>
        <string>src.main_pat</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/adamerickson/Projects/PAT/backend</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONPATH</key>
        <string>/Users/adamerickson/Projects/PAT/backend</string>
        <key>LOG_LEVEL</key>
        <string>INFO</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/adamerickson/Projects/PAT/backend/logs/launchagent.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/adamerickson/Projects/PAT/backend/logs/launchagent_error.log</string>
</dict>
</plist>
```

### 2. Load the Agent
```bash
launchctl load ~/Library/LaunchAgents/com.pat.backend.plist
```

### 3. Verify
```bash
launchctl list | grep pat
```

## Using the PAT Command Center App (Alternative)
Instead of manual LaunchAgents, it is recommended to use the **PAT Command Center** macOS application located in `macOS/PATManager`. This app provides a visual interface to start/stop all services and view logs in real-time.
