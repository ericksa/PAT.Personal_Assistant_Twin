-- scripts/migrations/002_add_pat_core_tables.sql
-- Core PAT Tables for Calendar, Email, Tasks with Llama 3.2 Integration
-- Migration for Personal Assistant Twin (PAT) Core Infrastructure

-- Enable extensions if not exists
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- USER & PREFERENCES
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(255) DEFAULT 'Local User',
    email VARCHAR(255),
    timezone VARCHAR(50) DEFAULT 'America/New_York',
    preferences JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- CALENDAR EVENTS
-- ============================================
CREATE TABLE IF NOT EXISTS calendar_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) DEFAULT '00000000-0000-0000-0000-000000000001',
    external_event_id VARCHAR(255), -- Apple Calendar persistent ID
    title VARCHAR(500) NOT NULL,
    description TEXT,
    location VARCHAR(500),
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    all_day BOOLEAN DEFAULT FALSE,
    recurrence_rule VARCHAR(255), -- iCal RRULE format stored as string
    timezone VARCHAR(50),
    calendar_name VARCHAR(255) DEFAULT 'Adam', -- Which Apple calendar
    event_type VARCHAR(50) DEFAULT 'meeting', -- meeting, call, task, reminder, personal
    status VARCHAR(20) DEFAULT 'confirmed', -- confirmed, tentative, cancelled, declined
    priority INTEGER DEFAULT 0, -- AI-determined: 0-10
    travel_time_minutes INTEGER DEFAULT 0,
    requires_preparation BOOLEAN DEFAULT FALSE,
    preparation_minutes INTEGER DEFAULT 15,
    sync_status VARCHAR(20) DEFAULT 'synced', -- synced, pending, error, conflicted
    last_synced_at TIMESTAMP,
    ai_processed BOOLEAN DEFAULT FALSE,
    ai_summary TEXT,
    ai_suggestions JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- CALENDAR CONFLICTS
-- ============================================
CREATE TABLE IF NOT EXISTS calendar_conflicts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event1_id UUID REFERENCES calendar_events(id) ON DELETE CASCADE,
    event2_id UUID REFERENCES calendar_events(id) ON DELETE CASCADE,
    conflict_type VARCHAR(50) DEFAULT 'overlap', -- overlap, travel_time, preparation
    severity VARCHAR(20) DEFAULT 'medium', -- low, medium, high, critical
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_action TEXT,
    resolved_at TIMESTAMP,
    ai_suggested_resolution TEXT
);

-- ============================================
-- SCHEDULE PREFERENCES
-- ============================================
CREATE TABLE IF NOT EXISTS schedule_preferences (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE PRIMARY KEY,
    work_start_time TIME DEFAULT '09:00',
    work_end_time TIME DEFAULT '17:00',
    break_start_time TIME DEFAULT '12:00',
    break_end_time TIME DEFAULT '13:00',
    preferred_meeting_days INTEGER[] DEFAULT ARRAY[1,2,3,4,5]::INTEGER[], -- Mon-Fri
    avoid_meetings_first_last_hours BOOLEAN DEFAULT TRUE,
    travel_time_buffer_minutes INTEGER DEFAULT 15,
    preferred_meeting_length_minutes INTEGER DEFAULT 60,
    min_time_between_meetings_minutes INTEGER DEFAULT 15,
    max_meetings_per_day INTEGER DEFAULT 8,
    peak_productivity_hours INTEGER[] DEFAULT ARRAY[9,10,11,14,15,16,17]::INTEGER[],
    deep_work_blocks JSONB DEFAULT '[{"day": [1,2,3,4,5], "start": "09:00", "end": "11:00"}]'::jsonb,
    meeting_free_afternoons BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- EMAILS
-- ============================================
CREATE TABLE IF NOT EXISTS emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) DEFAULT '00000000-0000-0000-0000-000000000001',
    external_message_id VARCHAR(500), -- Apple Mail Message-ID
    subject TEXT,
    sender_email VARCHAR(255),
    sender_name VARCHAR(255),
    recipient_emails TEXT[], -- Array of recipients
    cc_emails TEXT[],
    bcc_emails TEXT[],
    received_at TIMESTAMP WITH TIME ZONE,
    sent_at TIMESTAMP WITH TIME ZONE,
    body_text TEXT,
    body_html TEXT,
    account_name VARCHAR(100) DEFAULT 'Apple Mail',
    folder VARCHAR(100) DEFAULT 'INBOX',
    read BOOLEAN DEFAULT FALSE,
    flagged BOOLEAN DEFAULT FALSE,
    important BOOLEAN DEFAULT FALSE,
    category VARCHAR(50), -- AI classified: work, personal, urgent, newsletter, spam, notification
    priority INTEGER DEFAULT 0, -- AI determined: 0-10
    summary TEXT, -- Llama 3.2 generated summary ~200 chars
    requires_action BOOLEAN DEFAULT FALSE,
    related_event_id UUID REFERENCES calendar_events(id),
    related_task_ids UUID[] DEFAULT ARRAY[]::UUID[],
    thread_id UUID REFERENCES email_threads(id),
    ai_processed BOOLEAN DEFAULT FALSE,
    ai_classified_at TIMESTAMP,
    ai_suggested_reply DRAFT,
    sync_status VARCHAR(20) DEFAULT 'synced',
    last_synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- EMAIL THREADS
-- ============================================
CREATE TABLE IF NOT EXISTS email_threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) DEFAULT '00000000-0000-0000-0000-000000000001',
    thread_id VARCHAR(255) UNIQUE, -- Apple Mail thread identifier
    subject TEXT,
    last_message_at TIMESTAMP WITH TIME ZONE,
    message_count INTEGER DEFAULT 0,
    participants TEXT[], -- Email addresses
    ai_summary TEXT, -- Thread summary from Llama 3.2
    context JSONB DEFAULT '{}'::jsonb, -- Conversation context, entities extracted
    status VARCHAR(20) DEFAULT 'active', -- active, resolved, needs_followup
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TASKS (Reminders + PAT Tasks)
-- ============================================
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) DEFAULT '00000000-0000-0000-0000-000000000001',
    external_task_id VARCHAR(500), -- Apple Reminders ID
    title VARCHAR(500) NOT NULL,
    description TEXT,
    due_date DATE,
    due_time TIME,
    priority INTEGER DEFAULT 0, -- AI suggested: 0-10
    status VARCHAR(20) DEFAULT 'pending', -- pending, in_progress, completed, cancelled, deferred
    completed_at TIMESTAMP,
    reminder_date TIMESTAMP WITH TIME ZONE,
    reminder_sent BOOLEAN DEFAULT FALSE,
    source VARCHAR(50) DEFAULT 'pat', -- pat, apple_reminders, email, calendar, manual
    related_email_id UUID REFERENCES emails(id),
    related_event_id UUID REFERENCES calendar_events(id),
    list_name VARCHAR(100) DEFAULT 'Reminders',
    ai_generated BOOLEAN DEFAULT FALSE,
    estimated_duration_minutes INTEGER,
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    completion_notes TEXT,
    ai_processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- AI SUGGESTIONS & PREDICTIONS
-- ============================================
CREATE TABLE IF NOT EXISTS ai_suggestions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) DEFAULT '00000000-0000-0000-0000-000000000001',
    suggestion_type VARCHAR(50), -- meeting_time, task_prioritization, email_response, schedule_optimization
    related_entity_type VARCHAR(50), -- event, email, task, thread
    related_entity_id UUID,
    suggestion TEXT,
    original_data JSONB, -- What data was this based on
    confidence DECIMAL(3,2) DEFAULT 0.50, -- 0.00-1.00 from Llama 3.2
    accepted BOOLEAN,
    applied BOOLEAN DEFAULT FALSE,
    feedback TEXT,
    reason TEXT, -- AI's reasoning for suggestion
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- WEARABLE DATA (Placeholder for Future)
-- ============================================
CREATE TABLE IF NOT EXISTS wearable_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) DEFAULT '00000000-0000-0000-0000-000000000001',
    data_type VARCHAR(50), -- heart_rate, sleep, steps, energy_level, activity
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    value JSONB,
    source VARCHAR(50) DEFAULT 'placeholder', -- future: apple_health, garmin
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- BUSINESS ENTITIES
-- ============================================
CREATE TABLE IF NOT EXISTS business_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50), -- company, organization, project, client
    name VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    website VARCHAR(500),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    contact_person VARCHAR(255),
    relationship_type VARCHAR(50), -- client, vendor, partner, competitor
    status VARCHAR(20) DEFAULT 'active', -- active, inactive, archived
    ai_summarized BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- BUSINESS DOCUMENTS (SOPs, RFQs, RFPs)
-- ============================================
CREATE TABLE IF NOT EXISTS business_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) DEFAULT '00000000-0000-0000-0000-000000000001',
    title VARCHAR(500) NOT NULL,
    document_type VARCHAR(50), -- sop, rfq, rfp, template, contract, proposal
    content TEXT,
    file_path VARCHAR(500),
    status VARCHAR(20) DEFAULT 'draft', -- draft, active, archived, approved
    related_entity_id UUID REFERENCES business_entities(id),
    version INTEGER DEFAULT 1,
    ai_generated BOOLEAN DEFAULT FALSE,
    ai_scored BOOLEAN DEFAULT FALSE,
    fit_score DECIMAL(3,2), -- AI score for RFQ/RFP fit
    extracted_entities JSONB DEFAULT '{}'::jsonb, -- People, dates, requirements
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

-- Calendar indexes
CREATE INDEX IF NOT EXISTS idx_calendar_events_user_id ON calendar_events(user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_dates ON calendar_events(start_time, end_time DESC);
CREATE INDEX IF NOT EXISTS idx_calendar_events_type ON calendar_events(event_type);
CREATE INDEX IF NOT EXISTS idx_calendar_events_status ON calendar_events(status);
CREATE INDEX IF NOT EXISTS idx_calendar_events_sync_status ON calendar_events(sync_status);
CREATE INDEX IF NOT EXISTS idx_calendar_events_external_id ON calendar_events(external_event_id);

-- Conflicts indexes
CREATE INDEX IF NOT EXISTS idx_conflicts_event1 ON calendar_conflicts(event1_id);
CREATE INDEX IF NOT EXISTS idx_conflicts_event2 ON calendar_conflicts(event2_id);
CREATE INDEX IF NOT EXISTS idx_conflicts_resolved ON calendar_conflicts(resolved);

-- Email indexes
CREATE INDEX IF NOT EXISTS idx_emails_user_id ON emails(user_id);
CREATE INDEX IF NOT EXISTS idx_emails_received_at ON emails(received_at DESC);
CREATE INDEX IF NOT EXISTS idx_emails_category ON emails(category);
CREATE INDEX IF NOT EXISTS idx_emails_unread ON emails(read) WHERE read = FALSE;
CREATE INDEX IF NOT EXISTS idx_emails_flagged ON emails(flagged) WHERE flagged = TRUE;
CREATE INDEX IF NOT EXISTS idx_emails_requires_action ON emails(requires_action) WHERE requires_action = TRUE;
CREATE INDEX IF NOT EXISTS idx_emails_thread_id ON emails(thread_id);
CREATE INDEX IF NOT EXISTS idx_emails_folder ON emails(folder);
CREATE INDEX IF NOT EXISTS idx_emails_external_id ON emails(external_message_id);

-- Thread indexes
CREATE INDEX IF NOT EXISTS idx_email_threads_user_id ON email_threads(user_id);
CREATE INDEX IF NOT EXISTS idx_email_threads_last_message ON email_threads(last_message_at DESC);

-- Task indexes
CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date) WHERE status != 'completed';
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_source ON tasks(source);
CREATE INDEX IF NOT EXISTS idx_tasks_external_id ON tasks(external_task_id);
CREATE INDEX IF NOT EXISTS idx_tasks_list_name ON tasks(list_name);

-- AI suggestions indexes
CREATE INDEX IF NOT EXISTS idx_ai_suggestions_user_id ON ai_suggestions(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_suggestions_type ON ai_suggestions(suggestion_type);
CREATE INDEX IF NOT EXISTS idx_ai_suggestions_entity ON ai_suggestions(related_entity_type, related_entity_id);
CREATE INDEX IF NOT EXISTS idx_ai_suggestions_accepted ON ai_suggestions(accepted) WHERE accepted IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ai_suggestions_created ON ai_suggestions(created_at DESC);

-- Business indexes
CREATE INDEX IF NOT EXISTS idx_business_documents_user_id ON business_documents(user_id);
CREATE INDEX IF NOT EXISTS idx_business_documents_type ON business_documents(document_type);
CREATE INDEX IF NOT EXISTS idx_business_documents_status ON business_documents(status);
CREATE INDEX IF NOT EXISTS idx_business_entities_type ON business_entities(entity_type);

-- Wearable indexes
CREATE INDEX IF NOT EXISTS idx_wearable_user_id ON wearable_data(user_id);
CREATE INDEX IF NOT EXISTS idx_wearable_timestamp ON wearable_data(timestamp DESC);

-- ============================================
-- DEFAULT USER SETUP (Single-User Mode)
-- ============================================

-- Create default user for single-user setup
INSERT INTO users (id, full_name, email, timezone)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'Local User',
    'local@pat.local',
    'America/New_York'
)
ON CONFLICT (id) DO NOTHING;

-- Create default schedule preferences
INSERT INTO schedule_preferences (user_id)
VALUES ('00000000-0000-0000-0000-000000000001')
ON CONFLICT (user_id) DO NOTHING;