# PAT Core API Reference

This document provides a comprehensive API reference for the PAT Core service, which serves as the backend for frontend (BFF) communication with web and mobile applications.

## Base URL
`http://localhost:8010/pat`

## Authentication
Most endpoints require authentication via JWT tokens. Include the token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

## Rate Limiting
Rate limiting applies to all endpoints:
- 100 requests per minute per IP
- 1000 requests per hour per user

## Error Responses
All error responses follow this format:
```json
{
  "error": "error_code",
  "message": "Human readable error message",
  "details": {}
}
```

Common error codes:
- `invalid_request`: Malformed request
- `unauthorized`: Missing or invalid authentication
- `forbidden`: Insufficient permissions
- `not_found`: Resource not found
- `internal_error`: Server error

## Calendar Endpoints

### List Calendar Events
`GET /calendar/events`

Retrieve calendar events with optional filtering.

**Parameters:**
- `start_date` (string, optional): ISO 8601 date to filter events from
- `end_date` (string, optional): ISO 8601 date to filter events to
- `status` (string, optional): Filter by event status (confirmed, tentative, cancelled, declined)
- `event_type` (string, optional): Filter by event type (meeting, call, task, reminder, personal)
- `limit` (integer, optional, default: 50): Maximum number of events to return
- `offset` (integer, optional, default: 0): Offset for pagination

**Response:**
```json
{
  "events": [
    {
      "id": "uuid",
      "external_event_id": "string",
      "title": "string",
      "description": "string",
      "location": "string",
      "start_time": "ISO 8601 datetime",
      "end_time": "ISO 8601 datetime",
      "all_day": "boolean",
      "recurrence_rule": "string",
      "timezone": "string",
      "calendar_name": "string",
      "event_type": "string",
      "status": "string",
      "priority": "integer",
      "travel_time_minutes": "integer",
      "requires_preparation": "boolean",
      "preparation_minutes": "integer",
      "sync_status": "string",
      "ai_processed": "boolean",
      "ai_summary": "string",
      "ai_suggestions": "array",
      "created_at": "ISO 8601 datetime",
      "updated_at": "ISO 8601 datetime"
    }
  ],
  "count": "integer",
  "total": "integer"
}
```

### Get Calendar Event
`GET /calendar/events/{event_id}`

Retrieve a specific calendar event by ID.

**Response:**
Same structure as individual event in list endpoint.

### Create Calendar Event
`POST /calendar/events`

Create a new calendar event.

**Body:**
```json
{
  "title": "string",
  "description": "string",
  "location": "string",
  "start_time": "ISO 8601 datetime",
  "end_time": "ISO 8601 datetime",
  "all_day": "boolean",
  "recurrence_rule": "string",
  "timezone": "string",
  "calendar_name": "string",
  "event_type": "string",
  "status": "string",
  "priority": "integer",
  "travel_time_minutes": "integer",
  "requires_preparation": "boolean",
  "preparation_minutes": "integer"
}
```

**Response:**
```json
{
  "event": {
    "id": "uuid",
    "external_event_id": "string",
    "title": "string",
    "description": "string",
    "location": "string",
    "start_time": "ISO 8601 datetime",
    "end_time": "ISO 8601 datetime",
    "all_day": "boolean",
    "recurrence_rule": "string",
    "timezone": "string",
    "calendar_name": "string",
    "event_type": "string",
    "status": "string",
    "priority": "integer",
    "travel_time_minutes": "integer",
    "requires_preparation": "boolean",
    "preparation_minutes": "integer",
    "sync_status": "string",
    "ai_processed": "boolean",
    "ai_summary": "string",
    "ai_suggestions": "array",
    "created_at": "ISO 8601 datetime",
    "updated_at": "ISO 8601 datetime"
  }
}
```

### Update Calendar Event
`PUT /calendar/events/{event_id}`

Update an existing calendar event.

**Body:**
Same as create, but all fields are optional.

**Response:**
Updated event object.

### Delete Calendar Event
`DELETE /calendar/events/{event_id}`

Delete a calendar event.

**Response:**
```json
{
  "deleted": "boolean"
}
```

### Sync Calendar
`POST /calendar/sync`

Manually trigger calendar synchronization with Apple Calendar.

**Parameters:**
- `calendar_name` (string, optional, default: "PAT-cal"): Name of calendar to sync
- `hours_back` (integer, optional, default: 72): Hours of past events to sync

**Response:**
```json
{
  "synced": "integer",
  "updated": "integer",
  "errors": "integer",
  "conflicts": "integer",
  "details": {}
}
```

## Email Endpoints

### List Emails
`GET /emails`

Retrieve emails with optional filtering.

**Parameters:**
- `folder` (string, optional): Filter by folder (INBOX, Sent, etc.)
- `category` (string, optional): Filter by category (work, personal, urgent, newsletter, spam, notification)
- `read` (boolean, optional): Filter by read status
- `flagged` (boolean, optional): Filter by flagged status
- `requires_action` (boolean, optional): Filter by action requirement
- `limit` (integer, optional, default: 50): Maximum number of emails to return
- `offset` (integer, optional, default: 0): Offset for pagination

**Response:**
```json
{
  "emails": [
    {
      "id": "uuid",
      "external_message_id": "string",
      "subject": "string",
      "sender_email": "string",
      "sender_name": "string",
      "recipient_emails": "array",
      "cc_emails": "array",
      "bcc_emails": "array",
      "received_at": "ISO 8601 datetime",
      "sent_at": "ISO 8601 datetime",
      "body_text": "string",
      "body_html": "string",
      "account_name": "string",
      "folder": "string",
      "read": "boolean",
      "flagged": "boolean",
      "important": "boolean",
      "category": "string",
      "priority": "integer",
      "summary": "string",
      "requires_action": "boolean",
      "related_event_id": "uuid",
      "related_task_ids": "array",
      "thread_id": "uuid",
      "ai_processed": "boolean",
      "ai_classified_at": "ISO 8601 datetime",
      "ai_suggested_reply": "string",
      "sync_status": "string",
      "last_synced_at": "ISO 8601 datetime",
      "created_at": "ISO 8601 datetime",
      "updated_at": "ISO 8601 datetime"
    }
  ],
  "count": "integer",
  "total": "integer"
}
```

### Get Email
`GET /emails/{email_id}`

Retrieve a specific email by ID.

**Response:**
Same structure as individual email in list endpoint.

### Process Email
`POST /emails/{email_id}/process`

Process and classify an email using AI.

**Response:**
```json
{
  "processed": "boolean",
  "classification": "string",
  "priority": "integer",
  "summary": "string",
  "requires_action": "boolean",
  "suggested_reply": "string"
}
```

### Update Email
`PUT /emails/{email_id}`

Update email properties (read status, flags, etc.).

**Body:**
```json
{
  "read": "boolean",
  "flagged": "boolean",
  "category": "string"
}
```

**Response:**
Updated email object.

## Task Endpoints

### List Tasks
`GET /tasks`

Retrieve tasks with optional filtering.

**Parameters:**
- `status` (string, optional): Filter by status (pending, in_progress, completed, cancelled, deferred)
- `priority` (integer, optional): Filter by priority level (0-10)
- `list_name` (string, optional): Filter by task list
- `due_soon` (boolean, optional): Filter for tasks due within 3 days
- `overdue` (boolean, optional): Filter for overdue tasks
- `tag` (string, optional): Filter by tag
- `limit` (integer, optional, default: 50): Maximum number of tasks to return
- `offset` (integer, optional, default: 0): Offset for pagination

**Response:**
```json
{
  "tasks": [
    {
      "id": "uuid",
      "external_task_id": "string",
      "title": "string",
      "description": "string",
      "due_date": "ISO 8601 date",
      "due_time": "ISO 8601 time",
      "priority": "integer",
      "status": "string",
      "completed_at": "ISO 8601 datetime",
      "reminder_date": "ISO 8601 datetime",
      "reminder_sent": "boolean",
      "source": "string",
      "related_email_id": "uuid",
      "related_event_id": "uuid",
      "list_name": "string",
      "ai_generated": "boolean",
      "estimated_duration_minutes": "integer",
      "tags": "array",
      "completion_notes": "string",
      "ai_processed": "boolean",
      "created_at": "ISO 8601 datetime",
      "updated_at": "ISO 8601 datetime"
    }
  ],
  "count": "integer",
  "total": "integer"
}
```

### Get Task
`GET /tasks/{task_id}`

Retrieve a specific task by ID.

**Response:**
Same structure as individual task in list endpoint.

### Create Task
`POST /tasks`

Create a new task.

**Body:**
```json
{
  "title": "string",
  "description": "string",
  "due_date": "ISO 8601 date",
  "due_time": "ISO 8601 time",
  "priority": "integer",
  "status": "string",
  "reminder_date": "ISO 8601 datetime",
  "list_name": "string",
  "estimated_duration_minutes": "integer",
  "tags": "array"
}
```

**Response:**
```json
{
  "task": {
    "id": "uuid",
    // Same structure as task object above
  }
}
```

### Update Task
`PUT /tasks/{task_id}`

Update an existing task.

**Body:**
Same as create, but all fields are optional.

**Response:**
Updated task object.

### Delete Task
`DELETE /tasks/{task_id}`

Delete a task.

**Response:**
```json
{
  "deleted": "boolean"
}
```

### Sync Tasks
`POST /tasks/sync`

Manually trigger task synchronization with Apple Reminders.

**Parameters:**
- `limit` (integer, optional, default: 100): Maximum number of tasks to sync

**Response:**
```json
{
  "synced": "integer",
  "updated": "integer",
  "errors": "integer"
}
```

## AI/LLM Endpoints

### Chat Completion
`POST /chat/completions`

Get AI-powered chat completions using the configured LLM.

**Body:**
```json
{
  "messages": [
    {
      "role": "string", // "system", "user", or "assistant"
      "content": "string"
    }
  ],
  "model": "string", // Optional, defaults to configured model
  "temperature": "number", // Optional, 0.0-2.0
  "max_tokens": "integer" // Optional, maximum response length
}
```

**Response:**
```json
{
  "id": "string",
  "object": "string",
  "created": "integer",
  "model": "string",
  "choices": [
    {
      "index": "integer",
      "message": {
        "role": "assistant",
        "content": "string"
      },
      "finish_reason": "string"
    }
  ],
  "usage": {
    "prompt_tokens": "integer",
    "completion_tokens": "integer",
    "total_tokens": "integer"
  }
}
```

### Test Connection
`POST /chat/test-connection`

Test the connection to the LLM service.

**Response:**
```json
{
  "success": "boolean",
  "message": "string",
  "model": "string"
}
```

## System Endpoints

### Health Check
`GET /health`

Check the health status of the PAT Core service.

**Response:**
```json
{
  "status": "string", // "healthy" or "unhealthy"
  "service": "string", // "pat-core"
  "timestamp": "ISO 8601 datetime",
  "version": "string",
  "dependencies": {
    "database": "string", // "connected" or "disconnected"
    "llm": "string", // "connected" or "disconnected"
    "redis": "string" // "connected" or "disconnected"
  }
}
```

### Metrics
`GET /metrics`

Get system metrics and performance data.

**Response:**
```json
{
  "uptime": "integer", // Seconds since start
  "requests_processed": "integer",
  "average_response_time": "number", // In milliseconds
  "active_connections": "integer",
  "database_queries_per_second": "number",
  "llm_calls_per_minute": "integer"
}
```

## Webhook Endpoints

### Apple Calendar Notification
`POST /webhooks/apple-calendar`

Receive notifications from Apple Calendar about changes.

**Body:**
```json
{
  "event": "string", // "created", "updated", "deleted"
  "calendar_item_identifier": "string",
  "timestamp": "ISO 8601 datetime"
}
```

### Apple Mail Notification
`POST /webhooks/apple-mail`

Receive notifications from Apple Mail about new emails.

**Body:**
```json
{
  "event": "string", // "received"
  "message_id": "string",
  "timestamp": "ISO 8601 datetime"
}
```

### Apple Reminders Notification
`POST /webhooks/apple-reminders`

Receive notifications from Apple Reminders about changes.

**Body:**
```json
{
  "event": "string", // "created", "updated", "completed", "deleted"
  "reminder_id": "string",
  "timestamp": "ISO 8601 datetime"
}
```

## Date and Time Formats

All timestamps use ISO 8601 format:
- Date: `YYYY-MM-DD`
- Time: `HH:MM:SS`
- DateTime: `YYYY-MM-DDTHH:MM:SS` (UTC) or `YYYY-MM-DDTHH:MM:SSZ`
- DateTime with timezone: `YYYY-MM-DDTHH:MM:SS±HH:MM`

## Rate Limits and Quotas

- API requests: 100 per minute
- LLM calls: 1000 per hour
- Database queries: 1000 per minute
- Webhook notifications: 1000 per hour

## Error Codes

- 400: Bad Request - Invalid input or malformed request
- 401: Unauthorized - Missing or invalid authentication
- 403: Forbidden - Insufficient permissions
- 404: Not Found - Resource does not exist
- 429: Too Many Requests - Rate limit exceeded
- 500: Internal Server Error - Unexpected server error
- 503: Service Unavailable - Dependency failure

## Changelog

### v1.0.0 (2026-02-12)
- Initial release of PAT Core API
- Calendar, email, and task management endpoints
- AI/LLM integration endpoints
- Webhook support for Apple applications