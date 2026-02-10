-- init.sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create documents table
CREATE TABLE IF NOT EXISTS documents (
                                         id UUID PRIMARY KEY,
                                         filename VARCHAR(255),
    content TEXT,
    embedding VECTOR(768),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

-- Create index
CREATE INDEX IF NOT EXISTS idx_documents_embedding
    ON documents USING ivfflat (embedding vector_cosine_ops);

-- Job search tables
-- Job listings storage
CREATE TABLE IF NOT EXISTS job_listings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    location VARCHAR(100),
    agency VARCHAR(50), -- VA, DHA, DoD, DOT
    clearance_required BOOLEAN DEFAULT FALSE,
    salary_range VARCHAR(100),
    description TEXT,
    requirements TEXT,
    url TEXT NOT NULL,
    match_score DECIMAL(3,2) DEFAULT 0.0,
    agency_score INTEGER DEFAULT 0, -- Priority: VA=4, DHA=3, DoD=2, DOT=1
    posted_date DATE,
    found_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(50) DEFAULT 'linkedin',
    status VARCHAR(20) DEFAULT 'new', -- new, reviewed, interested, applied
    scraped_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Job applications tracking
CREATE TABLE IF NOT EXISTS job_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_listing_id UUID REFERENCES job_listings(id) ON DELETE CASCADE,
    applied_date TIMESTAMP,
    status VARCHAR(50) DEFAULT 'interested', -- interested, applied, interview, rejected, offer
    application_method VARCHAR(100), -- direct, email, recruiter
    notes TEXT,
    follow_up_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Resume versions tracking
CREATE TABLE IF NOT EXISTS resume_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_listing_id UUID REFERENCES job_listings(id) ON DELETE CASCADE,
    original_document_ids UUID[], -- Array of PAT document IDs used
    custom_resume_path VARCHAR(500), -- Path to generated resume file
    generated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    match_score DECIMAL(3,2) DEFAULT 0.0, -- How well resume matches job
    ats_score DECIMAL(3,2) DEFAULT 0.0, -- ATS compatibility score
    revisions INTEGER DEFAULT 1,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for job search
CREATE INDEX IF NOT EXISTS idx_job_listings_agency ON job_listings(agency);
CREATE INDEX IF NOT EXISTS idx_job_listings_clearance ON job_listings(clearance_required);
CREATE INDEX IF NOT EXISTS idx_job_listings_score ON job_listings(match_score DESC);
CREATE INDEX IF NOT EXISTS idx_job_listings_status ON job_listings(status);
CREATE INDEX IF NOT EXISTS idx_job_listings_date ON job_listings(posted_date DESC);
CREATE INDEX IF NOT EXISTS idx_job_applications_status ON job_applications(status);
CREATE INDEX IF NOT EXISTS idx_resume_versions_score ON resume_versions(match_score DESC);
