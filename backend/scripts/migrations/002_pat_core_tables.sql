-- ============================================================
-- PAT Core Database Migration
-- ============================================================
-- Creates tables for Personal Assistant Twin
-- - Calendar management (PAT-cal)
-- - Email processing
-- - Task management
-- - AI suggestions
-- - Business entities
-- ============================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- Users Table (Single-user setup)
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    timezone VARCHAR(50) DEFAULT 'America/New_York',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- Calendar Events Table
-- ============================================================
CREATE TABLE IF NOT EXISTS calendar_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    apple_event_id VARCHAR(255) UNIQUE,
    calendar_name VARCHAR(255) DEFAULT 'PAT-cal',
    title VARCHAR(500) NOT NULL,
    description TEXT,
    start_date DATE NOT NULL,
    start_time VARCHAR(10),
    end_date DATE NOT NULL,
    end_time VARCHAR(10),
    location VARCHAR(500),
    event_type VARCHAR(50) DEFAULT 'meeting',
    is_all_day BOOLEAN DEFAULT FALSE,
    is_recurring BOOLEAN DEFAULT FALSE,
    recurrence VARCHAR(100),
    source VARCHAR(50) DEFAULT 'manual',
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_calendar_events_user_id ON calendar_events(user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_dates ON calendar_events(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_calendar_events_apple_id ON calendar_events(apple_event_id);

-- ============================================================
-- Calendar Conflicts Table
-- ============================================================
CREATE TABLE IF NOT EXISTS calendar_conflicts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID REFERENCES calendar_events(id) ON DELETE CASCADE,
    conflict_event_id UUID,
    conflict_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    overlap_minutes INTEGER,
    message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conflicts_event_id ON calendar_conflicts(event_id);

-- ============================================================
-- Schedule Preferences Table
-- ============================================================
CREATE TABLE IF NOT EXISTS schedule_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    work_start_time VARCHAR(10) DEFAULT '09:00',
    work_end_time VARCHAR(10) DEFAULT '17:00',
    buffer_minutes INTEGER DEFAULT 15,
    max_back_to_back INTEGER DEFAULT 3,
    break_min_duration INTEGER DEFAULT 15,
    max_daily_meetings INTEGER DEFAULT 8,
    timezone VARCHAR(50) DEFAULT 'America/New_York',
    prefer_morning BOOLEAN DEFAULT FALSE,
    prefer_afternoon BOOLEAN DEFAULT FALSE,
    avoid_friday_afternoon BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- Emails Table
-- ============================================================
CREATE TABLE IF NOT EXISTS emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    apple_id VARCHAR(255) UNIQUE,
    apple_message_id VARCHAR(500),
    thread_id VARCHAR(255),
    subject VARCHAR(1000),
    from_address VARCHAR(255) NOT NULL,
    from_name VARCHAR(255),
    to_addresses TEXT[],
    cc_addresses TEXT[],
    bcc_addresses TEXT[],
    body_preview TEXT,
    body_text TEXT,
    body_html TEXT,
    received_at TIMESTAMP NOT NULL,
    sent_at TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE,
    is_flagged BOOLEAN DEFAULT FALSE,
    folder VARCHAR(100) DEFAULT 'INBOX',
    classification VARCHAR(50),
    sub_classification VARCHAR(50),
    summary TEXT,
    reply_draft TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_emails_user_id ON emails(user_id);
CREATE INDEX IF NOT EXISTS idx_emails_received_at ON emails(received_at);
CREATE INDEX IF NOT EXISTS idx_emails_thread_id ON emails(thread_id);
CREATE INDEX IF NOT EXISTS idx_emails_classification ON emails(classification);
CREATE INDEX IF NOT EXISTS idx_emails_apple_id ON emails(apple_id);

-- ============================================================
-- Email Threads Table
-- ============================================================
CREATE TABLE IF NOT EXISTS email_threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    apple_thread_id VARCHAR(255) UNIQUE,
    subject VARCHAR(1000) NOT NULL,
    participant_count INTEGER DEFAULT 0,
    message_count INTEGER DEFAULT 1,
    is_unread BOOLEAN DEFAULT FALSE,
    last_message_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_threads_user_id ON email_threads(user_id);
CREATE INDEX IF NOT EXISTS idx_threads_apple_thread_id ON email_threads(apple_thread_id);

-- ============================================================
-- Tasks Table
-- ============================================================
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    apple_id VARCHAR(255) UNIQUE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'medium',
    due_date TIMESTAMP,
    due_time VARCHAR(10),
    estimated_duration INTEGER,
    tags TEXT[],
    reminder_minutes INTEGER,
    location VARCHAR(500),
    is_recurring BOOLEAN DEFAULT FALSE,
    recurrence VARCHAR(100),
    is_flagged BOOLEAN DEFAULT FALSE,
    notes TEXT,
    completed_at TIMESTAMP,
    completed_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_tags ON tasks USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_tasks_apple_id ON tasks(apple_id);

-- ============================================================
-- AI Suggestions Table
-- ============================================================
CREATE TABLE IF NOT EXISTS ai_suggestions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    suggestion_type VARCHAR(50) NOT NULL,
    related_entity_id UUID,
    related_entity_type VARCHAR(50),
    suggestion_data JSONB,
    confidence_score DECIMAL(3,2),
    accepted BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_suggestions_user_id ON ai_suggestions(user_id);
CREATE INDEX IF NOT EXISTS idx_suggestions_type ON ai_suggestions(suggestion_type);

-- ============================================================
-- Wearable Data Table (Placeholder for health data)
-- ============================================================
CREATE TABLE IF NOT EXISTS wearable_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    data_type VARCHAR(50) NOT NULL,
    measurement_value DECIMAL(10,2),
    unit VARCHAR(20),
    recorded_at TIMESTAMP NOT NULL,
    source VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_wearable_user_id ON wearable_data(user_id);
CREATE INDEX IF NOT EXISTS idx_wearable_recorded_at ON wearable_data(recorded_at);

-- ============================================================
-- Business Entities Table
-- ============================================================
CREATE TABLE IF NOT EXISTS business_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    entity_name VARCHAR(500) NOT NULL,
    entity_type VARCHAR(50),
    email VARCHAR(255),
    phone VARCHAR(50),
    company VARCHAR(255),
    title VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_entities_user_id ON business_entities(user_id);
CREATE INDEX IF NOT EXISTS idx_entities_email ON business_entities(email);

-- ============================================================
-- Business Documents Table
-- ============================================================
CREATE TABLE IF NOT EXISTS business_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL,
    title VARCHAR(500),
    content TEXT,
    file_path TEXT,
    entity_id UUID REFERENCES business_entities(id) ON DELETE CASCADE,
    tags TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_documents_user_id ON business_documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_type ON business_documents(document_type);

-- ============================================================
-- Insert Default User
-- ============================================================
INSERT INTO users (id, email, full_name, timezone) 
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'erickson.adam.m@gmail.com',
    'Adam Erickson',
    'America/New_York'
) ON CONFLICT (id) DO NOTHING;

-- ============================================================
-- Migration Complete
-- ============================================================
COMMENT ON TABLE users IS 'PAT Core users (single-user setup)';
COMMENT ON TABLE calendar_events IS 'Calendar events synced from PAT-cal';
COMMENT ON TABLE calendar_conflicts IS 'Detected calendar event conflicts';
COMMENT ON TABLE schedule_preferences IS 'User schedule optimization preferences';
COMMENT ON TABLE emails IS 'Emails synced from Apple Mail';
COMMENT ON TABLE email_threads IS 'Email thread grouping';
COMMENT ON TABLE tasks IS 'Tasks synced from Apple Reminders';
COMMENT ON TABLE ai_suggestions IS 'AI-generated suggestions and recommendations';
COMMENT ON TABLE wearable_data IS 'Health and wearable device data';
COMMENT ON TABLE business_entities IS 'Business contact information';
COMMENT ON TABLE business_documents IS 'Business-related documents and contracts';