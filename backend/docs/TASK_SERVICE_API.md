# Task Service API Documentation

Complete task management with Apple Reminders bi-directional sync.

## Overview

The Task Service provides comprehensive task management with:
- Full CRUD operations for tasks
- Bi-directional sync with Apple Reminders (macOS only)
- AI-powered priority suggestions
- Focus task filtering (overdue, today)
- Task analytics and statistics

## API Endpoints

### Task CRUD

#### List Tasks
```bash
GET /pat/tasks?status={status}&limit={limit}
```

**Query Parameters:**
- `status`: Filter by status (pending, in_progress, completed, cancelled, deferred)
- `limit`: Maximum number of tasks to return (default: 50)

**Response:**
```json
{
  "status": "success",
  "tasks": [...],
  "count": 42
}
```

#### Create Task
```bash
POST /pat/tasks
Content-Type: application/json
```

**Body:**
```json
{
  "title": "Follow up with client",
  "description": "Discuss project milestones",
  "due_date": "2026-03-01",
  "due_time": "14:00",
  "priority": 7,
  "status": "pending",
  "list_name": "Work",
  "tags": ["client", "project"],
  "source": "pat"
}
```

**Response:**
```json
{
  "status": "success",
  "task": {
    "id": "uuid",
    "title": "Follow up with client",
    "description": "...",
    "priority": 7,
    "status": "pending",
    "created_at": "2026-02-12T10:00:00Z"
  }
}
```

#### Get Task
```bash
GET /pat/tasks/{task_id}
```

#### Update Task
```bash
PUT /pat/tasks/{task_id}
Content-Type: application/json
```

**Body:**
```json
{
  "status": "in_progress",
  "priority": 9,
  "description": "Updated description"
}
```

#### Delete Task
```bash
DELETE /pat/tasks/{task_id}?delete_from_apple={true|false}
```

**Query Parameters:**
- `delete_from_apple`: Set to `true` to also delete from Apple Reminders (default: false)

### Special Task Operations

#### Create and Sync to Apple Reminders
```bash
POST /pat/tasks/create-and-sync
```

Creates a task locally and automatically syncs it to Apple Reminders.

**Body:** Same as Create Task

**Additional Fields Synced:**
- `external_task_id`: Apple Reminders ID will be populated
- The reminder will appear in Apple Reminders app

#### Complete Task
```bash
POST /pat/tasks/{task_id}/complete
```

Marks task as completed. Includes optional notes.

**Body:**
```json
{
  "notes": "Task completed successfully"
}
```

Automatically syncs to Apple Reminders if task originated from there.

#### Get Focus Tasks
```bash
GET /pat/tasks/focus?limit={limit}
```

Returns overdue tasks + tasks due today, sorted by priority.

**Response:**
```json
{
  "status": "success",
  "tasks": [...],
  "count": 5
}
```

#### Get Overdue Tasks
```bash
GET /pat/tasks/overdue
```

Returns all overdue tasks (due date < today, status != completed).

#### Get Today's Tasks
```bash
GET /pat/tasks/today
```

Returns tasks due today.

### Sync with Apple Reminders

#### Sync All Tasks from Apple Reminders
```bash
POST /pat/tasks/sync?limit={limit}
```

Imports new reminders from Apple Reminders into the database.

**Query Parameters:**
- `limit`: Maximum number of reminders to sync (default: 100)

**Response:**
```json
{
  "synced": 5,
  "errors": 0,
  "message": "Synced 5 new reminders"
}
```

#### Sync Task to Apple Reminders
```bash
POST /pat/tasks/{task_id}/sync-to-apple
```

Sends an existing task to Apple Reminders.

**Response:**
```json
{
  "status": "success",
  "apple_id": "x-apple-reminder-id"
}
```

#### Sync Task from Apple Reminders
```bash
POST /pat/tasks/{task_id}/sync-from-apple
```

Refreshes task data from Apple Reminders (useful if modified outside PAT).

### AI Features

#### Get Priority Suggestions
```bash
POST /pat/tasks/prioritize
```

AI-powered suggestions for prioritizing pending tasks.

**Response:**
```json
{
  "status": "success",
  "suggestions": [
    {
      "task_id": "uuid",
      "title": "Follow up with client",
      "suggested_priority": 8,
      "reason": "AI suggested higher priority based on content"
    }
  ]
}
```

### Analytics

#### Get Task Analytics
```bash
GET /pat/tasks/analytics
```

**Response:**
```json
{
  "status": "success",
  "analytics": {
    "total_tasks": 42,
    "completed_tasks": 15,
    "overdue_tasks": 3,
    "today_tasks": 5,
    "pending_tasks": 24,
    "by_status": {
      "pending": 24,
      "completed": 15,
      "in_progress": 3
    },
    "by_priority": {
      "7": 5,
      "5": 10,
      "0": 15
    },
    "by_source": {
      "pat": 20,
      "apple_reminders": 15,
      "email": 5,
      "calendar": 2
    }
  }
}
```

## Task Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Auto | Unique task identifier |
| `external_task_id` | string | No | Apple Reminders ID |
| `title` | string | Yes | Task title (1-500 chars) |
| `description` | string | No | Detailed description |
| `due_date` | date | No | Due date (YYYY-MM-DD) |
| `due_time` | string | No | Due time (HH:MM) |
| `priority` | int | No | Priority 0-10 (default: 0) |
| `status` | enum | No | pending, in_progress, completed, cancelled, deferred |
| `reminder_date` | datetime | No | When to remind |
| `reminder_sent` | boolean | Auto | Whether reminder was sent |
| `source` | enum | Default | pat, apple_reminders, email, calendar, manual |
| `related_email_id` | UUID | No | Linked email ID |
| `related_event_id` | UUID | No | Linked calendar event ID |
| `list_name` | string | No | List name in Apple Reminders (default: "Reminders") |
| `ai_generated` | boolean | Auto | Whether AI created this task |
| `estimated_duration_minutes` | int | No | Estimated time to complete |
| `tags` | array | No | Task tags |
| `completion_notes` | string | No | Notes when completing |
| `ai_processed` | boolean | Auto | Whether AI has processed this task |
| `created_at` | datetime | Auto | Creation timestamp |
| `updated_at` | datetime | Auto | Last update timestamp |
| `metadata` | object | No | Additional custom data |

## Task Priorities (0-10)

| Priority | Use Case |
|----------|----------|
| 0 | No priority / unspecified |
| 1-3 | Low priority |
| 4-6 | Medium priority |
| 7-8 | High priority |
| 9-10 | Critical / Urgent |

## Task Status Workflow

```
pending → in_progress → completed
   ↓
cancelled
   ↓
deferred → pending
```

## Apple Reminders Integration

### Supported Operations (macOS Only)

**Create:**
- Tasks created in PAT can be synced to Apple Reminders
- Due dates, priority, notes, and list name are synced

**Read:**
- Import existing reminders from Apple Reminders
- View reminder details in PAT

**Update:**
- Changes in PAT sync back to Apple Reminders
- Completions are synced automatically
- Priority and due date changes sync

**Delete:**
- Tasks can be deleted from both PAT and Apple Reminders
- Optional with `delete_from_apple=true`

### Apple Reminder Priority Mapping

| Apple Priority | PAT Priority (0-10) |
|----------------|---------------------|
| None (9) | 0 |
| Low (3) | 2 |
| Medium (2) | 5 |
| High (1) | 8 |

## Examples

### Example 1: Create a task with due date and priority
```bash
curl -X POST http://localhost:8010/pat/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Submit project proposal",
    "description": "Complete and send proposal to client",
    "due_date": "2026-02-15",
    "due_time": "17:00",
    "priority": 9,
    "tags": ["work", "urgent"]
  }'
```

### Example 2: Get today's focus tasks
```bash
curl http://localhost:8010/pat/tasks/focus
```

### Example 3: Create and sync to Apple Reminders
```bash
curl -X POST http://localhost:8010/pat/tasks/create-and-sync \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Buy groceries",
    "description": "Milk, eggs, bread",
    "due_date": "2026-02-13",
    "list_name": "Personal"
  }'
```

### Example 4: Complete a task
```bash
curl -X POST http://localhost:8010/pat/tasks/uuid/complete \
  -H "Content-Type: application/json" \
  -d '{"notes": "Task completed successfully"}'
```

### Example 5: Get analytics
```bash
curl http://localhost:8010/pat/tasks/analytics
```

## Error Responses

All endpoints return error responses in this format:

```json
{
  "status": "error",
  "detail": "Error message description"
}
```

**Common HTTP Status Codes:**
- `200`: Success
- `400`: Bad request (invalid input)
- `404`: Resource not found
- `500`: Internal server error

## Notes

- All tasks are associated with a user (currently defaults to single user)
- External task IDs maintain sync with Apple Reminders
- Tasks are sorted by priority (desc) and due date (asc) by default
- Tags can be used for custom categorization
- Duration estimates help with time management

---

*This Task Service provides full task management with seamless Apple Reminders integration on macOS.*