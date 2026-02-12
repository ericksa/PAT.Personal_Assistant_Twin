# Email Service API Documentation

Complete email management with Apple Mail bi-directional sync and AI-powered email processing.

## Overview

The Email Service provides comprehensive email management with:
- Full CRUD operations for emails and threads
- Bi-directional sync with Apple Mail (macOS only)
- AI-powered email classification, summarization, and reply drafting
- Automatic task and meeting extraction from emails
- Email analytics and statistics

## API Endpoints

### Email CRUD

#### List Emails
```bash
GET /pat/emails?folder={folder}&category={category}&read={bool}&flagged={bool}&limit={limit}
```

**Query Parameters:**
- `folder`: Filter by folder (INBOX, Sent, Drafts, Archive, etc.)
- `category`: Filter by AI category
- `read`: Filter by read status (true/false)
- `flagged`: Filter by flagged status (true/false)
- `limit`: Maximum number of emails to return (default: 50)

**Response:**
```json
{
  "status": "success",
  "emails": [...],
  "count": 42
}
```

#### Get Email
```bash
GET /pat/emails/{email_id}
```

#### Update Email
```bash
PUT /pat/emails/{email_id}
Content-Type: application/json
```

**Body:**
```json
{
  "subject": "Updated Subject",
  "read": true,
  "flagged": true,
  "category": "work",
  "priority": 7,
  "folder": "INBOX"
}
```

#### Delete Email
```bash
DELETE /pat/emails/{email_id}
```

### Sync with Apple Mail

#### Sync All Emails from Apple Mail
```bash
POST /pat/emails/sync?limit={limit}
```

Imports new emails from Apple Mail Inbox into the database.

**Query Parameters:**
- `limit`: Maximum number of emails to sync (default: 100)

**Response:**
```json
{
  "synced": 5,
  "errors": 0,
  "message": "Synced 5 new emails from Mail"
}
```

#### Sync Email from Apple Mail
```bash
GET /pat/emails/{email_id}/sync-from-apple
```

Refreshes email data from Apple Mail (useful if modified outside PAT).

### AI Email Processing

#### Classify Email
```bash
POST /pat/emails/{email_id}/classify
```

AI classification with category and priority.

**Response:**
```json
{
  "status": "success",
  "summary": {
    "category": "work",
    "priority": 8,
    "requires_action": true,
    "reasoning": "Email from client about urgent project deliverables"
  }
}
```

**Categories:**
- `work` - Professional emails
- `personal` - Personal correspondence
- `urgent` - Time-sensitive emails
- `newsletter` - Subscriptions and newsletters
- `spam` - Unwanted emails
- `notification` - System notifications
- `marketing` - Promotional emails
- `social` - Social media updates
- `financial` - Financial transactions
- `travel` - Travel-related emails

#### Summarize Email
```bash
POST /pat/emails/{email_id}/summarize
```

AI-generated concise summary.

**Response:**
```json
{
  "status": "success",
  "summary": {
    "summary": "Client requests meeting next week to discuss project milestone. 3 deliverables mentioned: API integration, testing, and documentation."
  }
}
```

#### Draft Reply
```bash
POST /pat/emails/{email_id}/draft-reply?tone={tone}
```

AI-generated reply draft.

**Query Parameters:**
- `tone`: professional, casual, formal, friendly (default: professional)

**Response:**
```json
{
  "status": "success",
  "draft": {
    "subject": "Re: Meeting Request",
    "body": "Dear [Name],\n\nThank you for reaching out...",
    "tone": "professional"
  }
}
```

#### Extract Tasks from Email
```bash
POST /pat/emails/{email_id}/extract-tasks
```

AI extracts actionable tasks from email content.

**Response:**
```json
{
  "status": "success",
  "tasks": [
    {
      "id": "uuid",
      "title": "Schedule client meeting",
      "description": "Set up meeting for next week",
      "source": "email"
    }
  ],
  "count": 1
}
```

#### Extract Meeting from Email
```bash
POST /pat/emails/{email_id}/extract-meeting
```

AI extracts meeting requests and creates calendar events.

**Response:**
```json
{
  "status": "success",
  "meetings": [
    {
      "id": "uuid",
      "title": "Client Project Review",
      "start_time": "2026-02-15T14:00:00Z",
      "location": "Conference Room A"
    }
  ],
  "count": 1
}
```

#### Batch Classify Recent Emails
```bash
POST /pat/emails/batch-classify?limit={limit}
```

Classify multiple recent unclassified emails.

**Query Parameters:**
- `limit`: Number of emails to classify (default: 20)

**Response:**
```json
{
  "processed": 5,
  "errors": 0,
  "classifications": {
    "uuid1": "work",
    "uuid2": "personal"
  }
}
```

### Special Email Operations

#### Send Email
```bash
POST /pat/emails/send
Content-Type: application/json
```

**Body:**
```json
{
  "recipient": "client@example.com",
  "subject": "Project Update",
  "body": "Dear Client,\n\nHere's the latest update...",
  "cc": ["manager@example.com"]
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Email sent successfully"
}
```

#### Reply to Email
```bash
POST /pat/emails/{email_id}/reply
Content-Type: application/json
```

**Body:**
```json
{
  "body": "Thank you for your email...",
  "reply_all": false
}
```

#### Archive Email
```bash
POST /pat/emails/{email_id}/archive
```

Moves email to Archive folder in both PAT and Apple Mail.

#### Mark as Read
```bash
POST /pat/emails/{email_id}/read
```

Marks email as read in both PAT and Apple Mail.

### Email Filtering

#### Get Unread Emails
```bash
GET /pat/emails/unread?limit={limit}
```

#### Get Flagged Emails
```bash
GET /pat/emails/flagged?limit={limit}
```

### Analytics

#### Get Email Analytics
```bash
GET /pat/emails/analytics
```

**Response:**
```json
{
  "status": "success",
  "analytics": {
    "total_emails": 42,
    "unread_count": 8,
    "flagged_count": 5,
    "urgent_count": 3,
    "categories": {
      "work": 20,
      "personal": 10,
      "newsletter": 8,
      "urgent": 4
    }
  }
}
```

#### Get Email Threads
```bash
GET /pat/emails/threads?limit={limit}
```

Returns email conversation threads with subjects and message counts.

## Email Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Auto | Unique email identifier |
| `external_message_id` | string | No | Apple Mail Message-ID |
| `subject` | string | Yes | Email subject line |
| `sender_email` | string | Yes | Sender email address |
| `sender_name` | string | No | Sender display name |
| `recipient_emails` | array | No | To recipients |
| `cc_emails` | array | No | CC recipients |
| `bcc_emails` | array | No | BCC recipients |
| `received_at` | datetime | Yes | When email was received |
| `sent_at` | datetime | No | When email was sent |
| `body_text` | string | No | Plain text body |
| `body_html` | string | No | HTML body |
| `account_name` | string | Default | Email account (e.g., "Apple Mail") |
| `folder` | string | Default | Email folder (INBOX, Sent, etc.) |
| `read` | boolean | Default false | Whether email has been read |
| `flagged` | boolean | Default false | Whether email is flagged |
| `important` | boolean | Auto | AI-marked as important |
| `category` | enum | Auto | AI classification |
| `priority` | int | Auto | AI priority score (0-10) |
| `summary` | string | Auto | AI-generated summary |
| `requires_action` | boolean | Auto | AI-detected action needed |
| `related_event_id` | UUID | No | Linked calendar event |
| `related_task_ids` | array | No | Linked task IDs |
| `thread_id` | string | No | Thread identifier |
| `ai_processed` | boolean | Auto | Whether AI processed email |
| `ai_classified_at` | datetime | Auto | When AI classified email |
| `ai_suggested_reply` | string | Auto | AI suggested reply text |
| `sync_status` | enum | Default synced | Sync status with Apple Mail |
| `last_synced_at` | datetime | Auto | Last sync timestamp |
| `created_at` | datetime | Auto | Creation timestamp |
| `updated_at` | datetime | Auto | Last update timestamp |
| `metadata` | object | Auto | Additional custom data |

## Email Categories

AI classifies emails into these categories:

| Category | Description |
|----------|-------------|
| `work` | Professional/ business emails |
| `personal` | Personal correspondence |
| `urgent` | Time-sensitive requiring immediate attention |
| `newsletter` | Subscriptions and newsletters |
| `spam` | Unwanted/junk emails |
| `notification` | System/app notifications |
| `marketing` | Promotional emails |
| `social` | Social media updates |
| `financial` | Banking/transactions |
| `travel` | Travel-related emails |

## Priority Levels (0-10)

| Priority | Use Case |
|----------|----------|
| 0 | No priority / unspecified |
| 1-3 | Low priority |
| 4-6 | Medium priority |
| 7-8 | High priority |
| 9-10 | Critical / Urgent |

## Folder Types

| Folder | Description |
|--------|-------------|
| `INBOX` | Incoming emails |
| `Sent` | Sent emails |
| `Drafts` | Draft emails |
| `Archive` | Archived emails |
| `Junk` | Spam/junk |
| `Trash` | Deleted emails |

## Apple Mail Integration (macOS Only)

### Supported Operations

**Import:**
- Import emails from Apple Mail Inbox
- Sync read status, flagged status
- Get sender, subject, body, and timestamp

**Create:**
- Send new emails via Apple Mail
- Reply to existing emails
- Support for CC recipients

**Update:**
- Mark emails as read (syncs to Apple)
- Archive emails (moves to Apple Mail's Archive)
- Flag emails

**Delete:**
- Delete emails from database (Apple email remains)

### Limitations

- Only supports INBOX for import
- HTML body formatting may be simplified
- Attachments not currently supported
- Folder operations limited to syncing status

## Examples

### Example 1: Sync emails from Apple Mail
```bash
curl -X POST http://localhost:8010/pat/emails/sync?limit=50
```

### Example 2: Classify an email with AI
```bash
curl -X POST http://localhost:8010/pat/emails/uuid/classify
```

### Example 3: Draft a professional reply
```bash
curl -X POST http://localhost:8010/pat/emails/uuid/draft-reply?tone=professional
```

### Example 4: Extract tasks from email
```bash
curl -X POST http://localhost:8010/pat/emails/uuid/extract-tasks
```

### Example 5: Get unread urgent emails
```bash
curl "http://localhost:8010/pat/emails?category=urgent&read=false"
```

### Example 6: Batch classify recent emails
```bash
curl -X POST http://localhost:8010/pat/emails/batch-classify?limit=30
```

### Example 7: Send a new email
```bash
curl -X POST http://localhost:8010/pat/emails/send \
  -H "Content-Type: application/json" \
  -d '{
    "recipient": "client@example.com",
    "subject": "Meeting Confirmation",
    "body": "Please join our meeting tomorrow at 2pm...",
    "cc": ["manager@example.com"]
  }'
```

### Example 8: Archive and mark as read
```bash
curl -X POST http://localhost:8010/pat/emails/uuid/read
curl -X POST http://localhost:8010/pat/emails/uuid/archive
```

## AI Features

### Classification

The AI analyzes:
- Subject line keywords
- Sender relationship
- Email content and context
- Time-sensitive language

Prioritizes emails based on urgency and importance.

### Summarization

The AI creates concise summaries (around 200 characters) capturing:
- Main points and action items
- Key dates/times mentioned
- Important details
- Next steps

### Reply Drafting

The AI suggests replies based on:
- Original email tone and context
- Professionalism level requested
- Key points to address
- Appropriate professional etiquette

### Task Extraction

The AI identifies:
- Action items and deliverables
- Deadlines and due dates
- Responsibilities assigned
- Meeting requests

### Meeting Extraction

The AI finds:
- Meeting proposals
- Time and date proposals
- Participants and location
- Agenda items
- Confirmation requests

## Workflows

### Email → Task Workflow

1. Receive email (sync from Apple Mail)
2. AI classifies email
3. Extract tasks automatically
4. Tasks appear in task list
5. Sync to Apple Reminders

### Email → Calendar Workflow

1. Receive meeting request email
2. AI detects meeting details
3. Create calendar event
4. Event syncs to Apple Calendar

### Email → Reply Workflow

1. Receive email requiring response
2. AI analyzes email context
3. Draft reply suggestions
4. Review and edit draft
5. Send via Apple Mail

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

- All emails are associated with a user (currently defaults to single user)
- External message IDs maintain sync with Apple Mail
- AI processing runs asynchronously for batch operations
- Email threads group related conversations
- Rich content in HTML format is preserved when possible

---

*This Email Service provides full email management with seamless Apple Mail integration on macOS and powerful AI-powered email processing.*