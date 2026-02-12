# PAT Core API Reference for Frontend Developers

## Base URL
- Development: `http://localhost:8010`
- Documentation (Swagger): `http://localhost:8010/docs`
- Documentation (ReDoc): `http://localhost:8010/redoc`

## WebSocket

### Connection
- **URL**: `ws://localhost:8010/pat/ws`
- **Purpose**: Real-time updates for calendar events, email notifications, and task reminders.

### Message Format
All WebSocket messages are JSON-formatted:
```json
{
  "type": "message_type",
  "data": { ... }
}
```

### Message Types
| Type                     | Description                          | Data Example                                                                                     |
|--------------------------|--------------------------------------|--------------------------------------------------------------------------------------------------|
| `calendar_event`         | Calendar event updates               | `{"type": "created", "event": {...}}`                                                     |
| `optimization_suggestion`| AI schedule optimization suggestions  | `{"date": "2026-02-12", "suggested_changes": [...], "reasoning": "..."}`              |
| `email_notification`     | New email or classification          | `{"subject": "...", "sender": "...", "summary": "...", "classification": "..."}` |
| `task_reminder`          | Task reminders or updates            | `{"title": "...", "due_date": "...", "priority": "..."}`                            |

## Authentication
Currently: None (single-user setup)
User ID: `00000000-0000-0000-0000-000000000001`

## Response Format
All endpoints return JSON:
```json
{
  "status": "success", 
  "data": { ... }
}
```
Error format:
```json
{
  "status": "error",
  "message": "Error description"
}
```

---

## Calendar Endpoints

### Create Event
**POST** `/pat/calendar/events`

Request:
```json
{
  "title": "Team Meeting",
  "description": "Weekly sync",
  "start_date": "2026-02-12",
  "start_time": "10:00",
  "end_date": "2026-02-12",
  "end_time": "11:00",
  "location": "Office",
  "event_type": "meeting"
}
```

### List Events
**GET** `/pat/calendar/events?limit=50&offset=0`

Response:
```json
{
  "status": "success",
  "events": [
    {
      "id": "uuid",
      "title": "Team Meeting",
      "start_date": "2026-02-12",
      "end_date": "2026-02-12",
      "start_time": "10:00",
      "end_time": "11:00"
    }
  ],
  "count": 10
}
```

### Get Event
**GET** `/pat/calendar/events/{event_id}`

### Update Event
**PUT** `/pat/calendar/events/{event_id}`

Request (all fields optional):
```json
{
  "title": "Updated Meeting",
  "location": "Conference Room B"
}
```

### Delete Event
**DELETE** `/pat/calendar/events/{event_id}`

### Sync from Apple Calendar
**POST** `/pat/calendar/sync?calendar_name=PAT-cal&hours_back=72`

Response:
```json
{
  "synced": 15,
  "updated": 5,
  "errors": 0,
  "message": "Synced 15 new events, updated 5"
}
```

### Smart Reschedule (AI)
**POST** `/pat/calendar/events/{event_id}/reschedule`

Response:
```json
{
  "suggested_time": {
    "date": "2026-02-14",
    "time": "14:00",
    "reason": "Low conflict with existing schedule"
  },
  "alternatives": [...]
}
```

### Detect Conflicts
**GET** `/pat/calendar/conflicts?start_date=2026-02-12`

### Get Free Slots
**GET** `/pat/calendar/free-slots?date=2026-02-12&duration_minutes=30`

---

## Task Endpoints

### Create Task
**POST** `/pat/tasks`

Request:
```json
{
  "title": "Complete report",
  "description": "Q1 report for stakeholders",
  "priority": "high",
  "tags": ["work", "project"]
}
```

Priority values: `urgent`, `high`, `medium`, `low`

### List Tasks
**GET** `/pat/tasks?status=pending&priority=high&limit=50`

Response:
```json
{
  "status": "success",
  "tasks": [
    {
      "id": "uuid",
      "title": "Complete report",
      "status": "pending",
      "priority": "high"
    }
  ],
  "count": 5
}
```

### Get Focus Tasks
**GET** `/pat/tasks/focus`

Returns top 5 tasks for current session (overdue + today, prioritized)

### Complete Task
**POST** `/pat/tasks/{task_id}/complete`

Request:
```json
{
  "notes": "Delivered on time"
}
```

### Sync from Apple Reminders
**POST** `/pat/tasks/sync`

### Batch Create Tasks
**POST** `/pat/tasks/batch-create`

Request:
```json
{
  "task_descriptions": [
    "Client call on Friday at 2pm",
    "Update slides by Monday"
  ]
}
```

AI will parse descriptions and create structured tasks.

---

## Email Endpoints

### Classify Email (AI)
**POST** `/pat/emails/classify`

Request:
```json
{
  "subject": "Meeting Request",
  "body": "Can we meet tomorrow?"
}
```

Response:
```json
{
  "category": "work",
  "priority": "medium",
  "requires_action": true,
  "reasoning": "Contains meeting-related keywords"
}
```

### Summarize Email (AI)
**POST** `/pat/emails/summarize`

Request:
```json
{
  "subject": "Project Update",
  "body": "...long content..."
}
```

Response:
```json
{
  "summary": "2-3 sentence summary",
  "key_points": [
    "point1",
    "point2"
  ]
}
```

### Draft Reply (AI)
**POST** `/pat/emails/draft-reply`

Request:
```json
{
  "subject": "Re: Meeting Tomorrow",
  "sender": "client@example.com",
  "body": "We should meet tomorrow.",
  "tone": "professional"
}
```

Tone values: `professional`, `casual`, `formal`, `friendly`

### Extract Tasks from Text (AI)
**POST** `/pat/emails/extract-tasks`

Request:
```json
{
  "text": "Remember to update the report and email the client."
}
```

Response:
```json
{
  "tasks": [
    {
      "title": "Update the report",
      "priority": "medium"
    },
    {
      "title": "Email the client",
      "priority": "high"
    }
  ]
}
```

### Extract Meeting from Text (AI)
**POST** `/pat/emails/extract-meeting`

Request:
```json
{
  "text": "Meeting tomorrow at 2pm for 1 hour in Conference Room A"
}
```

Response:
```json
{
  "title": "Meeting",
  "start_date": "2026-02-12",
  "start_time": "14:00",
  "end_time": "15:00",
  "location": "Conference Room A"
}
```

---

## Chat/LLM Endpoints

### Chat Completion
**POST** `/pat/chat/completions`

Request:
```json
{
  "messages": [
    {"role": "user", "content": "Help me plan my day"}
  ],
  "temperature": 0.7
}
```

Response:
```json
{
  "response": "Here's a suggested daily plan..."
}
```

### Test LLM Connection
**POST** `/pat/chat/test-connection`

Response:
```json
{
  "status": "success",
  "model": "llama3.2:3b"
}
```

---

## System Endpoints

### Health Check
**GET** `/pat/health`

Response:
```json
{
  "status": "healthy",
  "service": "pat-core",
  "model": "llama3.2:3b",
  "features": {
    "calendar": true,
    "ai_llm": true,
    "applescript": true
  }
}
```

### System Info
**GET** `/pat/info`

Response:
```json
{
  "name": "PAT - Personal Assistant Twin",
  "version": "1.0.0",
  "features": [...],
  "integrations": {
    "ollama": "llama3.2:3b",
    "apple_calendar": "PAT-cal (via AppleScript)",
    "apple_mail": "local (via AppleScript)",
    "apple_reminders": "local (via AppleScript)"
  }
}
```

---

## Frontend Integration Notes

### Error Handling
- All endpoints return HTTP 200 with JSON
- Check `"status"` field for error/success
- Implement retry logic for failed requests

### Rate Limiting
- None currently (single-user setup)
- Consider frontend debouncing for repeated calls

### Real-time Updates
- Current: Polling required
- Future: WebSocket support (backend TODO)

### Date/Time Format
- Dates: `YYYY-MM-DD` (ISO 8601)
- Times: `HH:MM` (24-hour format)
- Timestamps: ISO 8601 string: `2026-02-12T10:00:00Z`

### Validation Recommendations (Frontend)
- Validate date format before sending
- Truncate long text fields (subject: 255 chars, description: 1000 chars)
- Default values: priority="medium", event_type="meeting"

---

## Data Models

### Calendar Event
```json
{
  "id": "uuid",
  "title": "string (required, max 500)",
  "description": "string (optional)",
  "start_date": "YYYY-MM-DD (required)",
  "start_time": "HH:MM (optional)",
  "end_date": "YYYY-MM-DD (required)",
  "end_time": "HH:MM (optional)",
  "location": "string (optional, max 500)",
  "event_type": "string (default: meeting)",
  "priority": "integer (0-10, optional)"
}
```

### Task
```json
{
  "id": "uuid",
  "title": "string (required, max 500)",
  "description": "string (optional)",
  "status": "pending|completed|cancelled (default: pending)",
  "priority": "urgent|high|medium|low (default: medium)",
  "due_date": "ISO timestamp (optional)",
  "tags": ["string array (optional)"]
}
```

---

## Recent Changes

See `CHANGELOG.md` for full change history.

### 2026-02-11
- Calendar name updated from "Adam" to "PAT-cal"
- asyncpg dependency updated to ~=0.30.0
- Database migration applied (10/11 tables created)
- PAT Core API launched with 30+ endpoints