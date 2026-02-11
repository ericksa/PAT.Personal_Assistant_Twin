# macOS LaunchAgent Guide for PAT Sync Workers

**Status:** Reference guide created. Implementation is a future project with no planned timeline.

---

## Overview

LaunchAgent is macOS's built-in mechanism for running background services automatically when a user logs in. This guide documents how to set up PAT sync workers to start automatically on boot.

## Prerequisites

- macOS 12+
- Python 3.8+ installed
- PAT sync workers created (`scripts/pat_sync_worker.py`)

## Directory Structure

```
~/Library/LaunchAgents/
├── com.pat.calendar-sync.plist
├── com.pat.email-sync.plist
└── com.pat.reminders-sync.plist
```

## LaunchAgent Property List (.plist) Example

### For Calendar Sync (`com.pat.calendar-sync.plist`)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.pat.calendar-sync</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/Users/adamerickson/Projects/PAT/scripts/pat_sync_worker.py</string>
        <string>--service=calendar</string>
        <string>--interval=3600</string>
    </array>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>StandardOutPath</key>
    <string>/var/log/pat/calendar-worker.log</string>
    
    <key>StandardErrorPath</key>
    <string>/var/log/pat/calendar-worker-error.log</string>
    
    <key>WorkingDirectory</key>
    <string>/Users/adamerickson/Projects/PAT</string>
</dict>
</plist>
```

### For Email Sync (`com.pat.email-sync.plist`)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.pat.email-sync</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/Users/adamerickson/Projects/PAT/scripts/pat_sync_worker.py</string>
        <string>--service=email</string>
        <string>--interval=300</string>
    </array>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>StandardOutPath</key>
    <string>/var/log/pat/email-worker.log</string>
    
    <key>StandardErrorPath</key>
    <string>/var/log/pat/email-worker-error.log</string>
    
    <key>WorkingDirectory</key>
    <string>/Users/adamerickson/Projects/PAT</string>
</dict>
</plist>
```

### For Reminders Sync (`com.pat.reminders-sync.plist`)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.pat.reminders-sync</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/Users/adamerickson/Projects/PAT/scripts/pat_sync_worker.py</string>
        <string>--service=reminders</string>
        <string>--interval=600</string>
    </array>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>StandardOutPath</key>
    <string>/var/log/pat/reminders-worker.log</string>
    
    <key>StandardErrorPath</key>
    <string>/var/log/pat/reminders-worker-error.log</string>
    
    <key>WorkingDirectory</key>
    <string>/Users/adamerickson/Projects/PAT</string>
</dict>
</plist>
```

## Installation Steps (Future Reference)

1. **Create log directory:**
   ```bash
   sudo mkdir -p /var/log/pat
   sudo chown $(whoami):staff /var/log/pat
   ```

2. **Create .plist files:**
   ```bash
   mkdir -p ~/Library/LaunchAgents
   
   # Create each .plist file (use nano or vim)
   nano ~/Library/LaunchAgents/com.pat.calendar-sync.plist
   nano ~/Library/LaunchAgents/com.pat.email-sync.plist
   nano ~/Library/LaunchAgents/com.pat.reminders-sync.plist
   ```

3. **Load LaunchAgents:**
   ```bash
   launchctl load ~/Library/LaunchAgents/com.pat.calendar-sync.plist
   launchctl load ~/Library/LaunchAgents/com.pat.email-sync.plist
   launchctl load ~/Library/LaunchAgents/com.pat.reminders-sync.plist
   ```

4. **Verify running:**
   ```bash
   launchctl list | grep pat-sync
   ```

   Expected output:
   ```
   <PID> - 0 com.pat.calendar-sync
   <PID> - 0 com.pat.email-sync
   <PID> - 0 com.pat.reminders-sync
   ```

## Logging

### Log File Locations

- `/var/log/pat/calendar-worker.log` - Calendar sync output
- `/var/log/pat/email-worker.log` - Email sync output
- `/var/log/pat/reminders-worker.log` - Reminders sync output
- `/var/log/pat/*-worker-error.log` - Error logs

### View Logs

```bash
# Real-time monitoring
tail -f /var/log/pat/calendar-worker.log
tail -f /var/log/pat/email-worker.log
tail -f /var/log/pat/reminders-worker.log

# Recent entries
tail -100 /var/log/pat/calendar-worker.log
```

## Troubleshooting

### Check Status
```bash
launchctl list | grep pat-sync
```

### Restart a Worker
```bash
# Unload
launchctl unload ~/Library/LaunchAgents/com.pat.calendar-sync.plist

# Load again
launchctl load ~/Library/LaunchAgents/com.pat.calendar-sync.plist
```

### Stop All Workers
```bash
launchctl unload ~/Library/LaunchAgents/com.pat.calendar-sync.plist
launchctl unload ~/Library/LaunchAgents/com.pat.email-sync.plist
launchctl unload ~/Library/LaunchAgents/com.pat.reminders-sync.plist
```

### Check for Errors
```bash
# View error logs
cat /var/log/pat/calendar-worker-error.log
cat /var/log/pat/email-worker-error.log
cat /var/log/pat/reminders-worker-error.log
```

### Common Issues

**Workers not starting:**
- Check Python path (update ProgramArguments in .plist)
- Verify sync worker script permissions: `chmod +x scripts/pat_sync_worker.py`
- Check for syntax errors in .plist files

**Sync workers stopped:**
- Run `launchctl list | grep pat-sync` to check status
- Check error logs for failure reason
- Reload LaunchAgent with `launchctl unload` then `launchctl load`

**Permissions denied on logs:**
- Ensure `/var/log/pat` directory owned by user: `sudo chown $(whoami):staff /var/log/pat`

**AppleScript errors:**
- Workers will log errors and continue
- Check macOS System Preferences ▸ Privacy & Security ▸ Automation to ensure PAT has permissions
- Grant Calendar, Mail, Reminders access when prompted

## Configuration Reference

### Sync Worker Intervals

- **Calendar**: 3600 seconds (1 hour) - Hourly sync of calendar events
- **Email**: 300 seconds (5 minutes) - Near real-time email checking
- **Reminders**: 600 seconds (10 minutes) - Frequent task list sync

### Python Path

Update `ProgramArguments` in .xml files if using different Python:
- System default: `/usr/local/bin/python3` (Homebrew)
- Custom virtualenv: `/path/to/venv/bin/python3`

### Working Directory

Must point to PAT project root where `scripts/` directory exists:
- Default: `/Users/adamerickson/Projects/PAT`

## Unload on Uninstall

To permanently remove LaunchAgents:

```bash
# Unload
launchctl unload ~/Library/LaunchAgents/com.pat.calendar-sync.plist
launchctl unload ~/Library/LaunchAgents/com.pat.email-sync.plist
launchctl unload ~/Library/LaunchAgents/com.pat.reminders-sync.plist

# Remove files
rm ~/Library/LaunchAgents/com.pat.calendar-sync.plist
rm ~/Library/LaunchAgents/com.pat.email-sync.plist
rm ~/Library/LaunchAgents/com.pat.reminders-sync.plist
```

## Implementation Checklist (For Future)

- [ ] Ensure `scripts/pat_sync_worker.py` is implemented and tested
- [ ] Create `/var/log/pat` directory with correct permissions
- [ ] Create three .plist files with correct paths and Python interpreter
- [ ] Load all three LaunchAgents
- [ ] Verify all workers are running with `launchctl list`
- [ ] Check log paths are writable
- [ ] Test sync operations from workers
- [ ] Grant macOS permissions for Calendar/Mail/Reminders access
- [ ] Monitor logs for 24 hours to verify stability

## Notes

- Requires write permissions to `/var/log/pat/`
- First run will prompt for Apple Calendar/Mail/Reminders permissions
- Workers implement graceful error handling and will retry on next cycle
- Workers log to both stdout (terminated) and log files (persistent)
- Email notifications are sent only once until error is fixed

## References

- [Apple LaunchAgent Documentation](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdPlist.html)
- [launchctl Command Reference](https://ss64.com/osx/launchctl.html)
- [Property List (plist) Structure](https://developer.apple.com/library/archive/documentation/General/Reference/InfoPlistKeyReference/Introduction/Introduction.html)