-- ============================================
-- PAT ENTERPRISE PLATFORM DATABASE SCHEMA
-- ============================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================
-- MARKET OPPORTUNITIES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS market_opportunities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    tam DECIMAL(15,2), -- Total Addressable Market
    growth_rate DECIMAL(5,4), -- Growth rate (e.g., 0.25 for 25%)
    competitor_count INTEGER DEFAULT 0,
    rag_status VARCHAR(10) NOT NULL CHECK (rag_status IN ('RED', 'AMBER', 'GREEN')),
    rag_score INTEGER NOT NULL CHECK (rag_score >= 0 AND rag_score <= 100),
    market_trends JSONB DEFAULT '[]',
    risk_factors JSONB DEFAULT '[]',
    source_data JSONB DEFAULT '{}',
    funding_total DECIMAL(15,2),
    employee_count INTEGER,
    revenue DECIMAL(15,2),
    valuation DECIMAL(15,2),
    market_maturity INTEGER CHECK (market_maturity >= 0 AND market_maturity <= 100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_market_opportunities_rag_status ON market_opportunities(rag_status);
CREATE INDEX IF NOT EXISTS idx_market_opportunities_rag_score ON market_opportunities(rag_score DESC);
CREATE INDEX IF NOT EXISTS idx_market_opportunities_growth_rate ON market_opportunities(growth_rate DESC);
CREATE INDEX IF NOT EXISTS idx_market_opportunities_tam ON market_opportunities(tam DESC);
CREATE INDEX IF NOT EXISTS idx_market_opportunities_created_at ON market_opportunities(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_market_opportunities_name_trgm ON market_opportunities USING gin(name gin_trgm_ops);

-- ============================================
-- DOCUMENTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_type VARCHAR(50) NOT NULL CHECK (document_type IN ('business_plan', 'sow', 'rfp', 'proposal')),
    title VARCHAR(255) NOT NULL,
    content TEXT,
    pdf_path VARCHAR(500),
    overall_rag_status VARCHAR(10) CHECK (overall_rag_status IN ('RED', 'AMBER', 'GREEN')),
    job_id VARCHAR(100), -- Reference to generation job
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'generating', 'completed', 'failed')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_rag_status ON documents(overall_rag_status);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at DESC);

-- ============================================
-- DOCUMENT SECTIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS document_sections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    section_name VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    rag_status VARCHAR(10) CHECK (rag_status IN ('RED', 'AMBER', 'GREEN')),
    section_order INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_document_sections_document_id ON document_sections(document_id);
CREATE INDEX IF NOT EXISTS idx_document_sections_name ON document_sections(section_name);

-- ============================================
-- MARKET INSIGHTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS market_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    summary TEXT NOT NULL,
    source VARCHAR(100) NOT NULL,
    rag_status VARCHAR(10) CHECK (rag_status IN ('RED', 'AMBER', 'GREEN')),
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    industry VARCHAR(100),
    tags JSONB DEFAULT '[]',
    source_data JSONB DEFAULT '{}',
    published_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_market_insights_industry ON market_insights(industry);
CREATE INDEX IF NOT EXISTS idx_market_insights_rag_status ON market_insights(rag_status);
CREATE INDEX IF NOT EXISTS idx_market_insights_published_at ON market_insights(published_at DESC);

-- ============================================
-- RAG SCORING RULES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS rag_scoring_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_name VARCHAR(100) NOT NULL,
    rule_type VARCHAR(50) NOT NULL, -- 'threshold', 'multiplier', 'penalty'
    field_name VARCHAR(100) NOT NULL,
    operator VARCHAR(10) NOT NULL, -- '>', '>=', '<', '<='
    value DECIMAL(15,4) NOT NULL,
    impact_score INTEGER NOT NULL, -- Positive or negative score contribution
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_rag_scoring_rules_active ON rag_scoring_rules(is_active);
CREATE INDEX IF NOT EXISTS idx_rag_scoring_rules_type ON rag_scoring_rules(rule_type);

-- ============================================
-- GENERATION JOBS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS generation_jobs (
    id VARCHAR(100) PRIMARY KEY,
    job_type VARCHAR(50) NOT NULL, -- 'document', 'ingestion', 'scoring'
    document_type VARCHAR(50), -- If job_type is 'document'
    template_name VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'completed', 'failed', 'cancelled')),
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_generation_jobs_status ON generation_jobs(status);
CREATE INDEX IF NOT EXISTS idx_generation_jobs_type ON generation_jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_generation_jobs_created_at ON generation_jobs(created_at DESC);

-- ============================================
-- COMPANIES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    website VARCHAR(500),
    linkedin_url VARCHAR(500),
    crunchbase_id VARCHAR(100),
    founded_year INTEGER,
    employee_count INTEGER,
    industry VARCHAR(100),
    location VARCHAR(200),
    funding_stage VARCHAR(50),
    total_funding DECIMAL(15,2),
    last_funding_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name);
CREATE INDEX IF NOT EXISTS idx_companies_industry ON companies(industry);
CREATE INDEX IF NOT EXISTS idx_companies_funding_stage ON companies(funding_stage);
CREATE INDEX IF NOT EXISTS idx_companies_name_trgm ON companies USING gin(name gin_trgm_ops);

-- ============================================
-- MARKET TRENDS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS market_trends (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    industry VARCHAR(100) NOT NULL,
    growth_rate DECIMAL(5,4),
    market_size DECIMAL(15,2),
    key_trends JSONB DEFAULT '[]',
    growth_drivers JSONB DEFAULT '[]',
    barriers JSONB DEFAULT '[]',
    competitive_intensity VARCHAR(20) CHECK (competitive_intensity IN ('low', 'medium', 'high')),
    data_source VARCHAR(100),
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_market_trends_industry ON market_trends(industry);
CREATE INDEX IF NOT EXISTS idx_market_trends_collected_at ON market_trends(collected_at DESC);

-- ============================================
-- NOTIFICATION QUEUE TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS notification_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    notification_type VARCHAR(50) NOT NULL, -- 'red_alert', 'reminder', 'summary'
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    recipient_id UUID, -- User ID if applicable
    opportunity_id UUID REFERENCES market_opportunities(id),
    priority VARCHAR(10) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'critical')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed', 'cancelled')),
    scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_notification_queue_status ON notification_queue(status);
CREATE INDEX IF NOT EXISTS idx_notification_queue_scheduled_at ON notification_queue(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_notification_queue_opportunity_id ON notification_queue(opportunity_id);

-- ============================================
-- VIEWS FOR COMMON QUERIES
-- ============================================

-- View for RAG metrics
CREATE OR REPLACE VIEW rag_metrics AS
SELECT 
    COUNT(*) as total_opportunities,
    SUM(CASE WHEN rag_status = 'GREEN' THEN 1 ELSE 0 END) as green_count,
    SUM(CASE WHEN rag_status = 'AMBER' THEN 1 ELSE 0 END) as amber_count,
    SUM(CASE WHEN rag_status = 'RED' THEN 1 ELSE 0 END) as red_count,
    ROUND(AVG(rag_score), 1) as avg_rag_score,
    COUNT(CASE WHEN rag_status = 'RED' THEN 1 END) as red_count
FROM market_opportunities;

-- View for document overview
CREATE OR REPLACE VIEW document_overview AS
SELECT 
    d.id,
    d.document_type,
    d.title,
    d.overall_rag_status,
    d.status,
    d.created_at,
    COUNT(ds.id) as section_count,
    STRING_AGG(ds.section_name, ', ' ORDER BY ds.section_order) as sections
FROM documents d
LEFT JOIN document_sections ds ON d.id = ds.document_id
GROUP BY d.id, d.document_type, d.title, d.overall_rag_status, d.status, d.created_at;

-- ============================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to relevant tables
CREATE TRIGGER update_market_opportunities_updated_at BEFORE UPDATE ON market_opportunities FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_document_sections_updated_at BEFORE UPDATE ON document_sections FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_generation_jobs_updated_at BEFORE UPDATE ON generation_jobs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- SAMPLE DATA
-- ============================================

-- Insert default RAG scoring rules
INSERT INTO rag_scoring_rules (rule_name, rule_type, field_name, operator, value, impact_score, description) VALUES
('High Growth Rate', 'threshold', 'growth_rate', '>', 0.15, 25, 'Growth rate above 15%'),
('Medium Growth Rate', 'threshold', 'growth_rate', '>', 0.05, 10, 'Growth rate above 5%'),
('Low Growth Rate', 'threshold', 'growth_rate', '<=', 0.05, -20, 'Growth rate at or below 5%'),
('Large Market Size', 'threshold', 'tam', '>', 1000000000, 25, 'Total addressable market above $1B'),
('Medium Market Size', 'threshold', 'tam', '>', 100000000, 10, 'Total addressable market above $100M'),
('High Funding', 'threshold', 'funding_total', '>', 10000000, 20, 'Funding above $10M'),
('Regulatory Risk', 'penalty', 'risk_factors', 'contains', -20, -25, 'Regulatory risk factor present'),
('Funding Gap Risk', 'penalty', 'risk_factors', 'contains', -25, -25, 'Funding gap risk factor present'),
('Low Competitive Density', 'threshold', 'competitor_count', '<', 10, 15, 'Less than 10 competitors'),
('High Competitive Density', 'threshold', 'competitor_count', '>', 20, -10, 'More than 20 competitors');

-- Insert sample market opportunities
INSERT INTO market_opportunities (name, description, tam, growth_rate, competitor_count, rag_status, rag_score, market_trends, risk_factors) VALUES
('AI-Powered Financial Analytics', 'Advanced AI solutions for financial data analysis and prediction', 2500000000.00, 0.35, 12, 'GREEN', 85, '["AI adoption", "Regulatory compliance", "Data security"]', '[]'),
('Sustainable Energy Storage', 'Next-generation battery technology for renewable energy storage', 1500000000.00, 0.28, 18, 'AMBER', 65, '["Green energy transition", "Climate concerns", "Technology advancement"]', '["Regulatory approval", "Manufacturing complexity"]'),
('Telemedicine Platform', 'Comprehensive healthcare delivery platform for remote consultations', 800000000.00, 0.15, 25, 'RED', 45, '["Healthcare digitization", "Aging population", "Cost reduction"]', '["Regulatory compliance", "Privacy concerns", "Technology adoption"]'),
('Blockchain Supply Chain', 'Blockchain-based solutions for supply chain transparency and tracking', 3000000000.00, 0.42, 8, 'GREEN', 90, '["Supply chain visibility", "ESG requirements", "Trust verification"]', '[]'),
('Smart Agriculture IoT', 'IoT sensors and AI for precision agriculture and crop optimization', 1200000000.00, 0.22, 15, 'AMBER', 70, '["Food security", "Climate change", "Technology adoption"]', '["Market education", "Infrastructure requirements"]');

-- Insert sample companies
INSERT INTO companies (name, description, website, industry, employee_count, funding_stage, total_funding, founded_year) VALUES
('TechCorp Analytics', 'AI-powered financial data analysis company', 'https://techcorp-analytics.com', 'Financial Technology', 150, 'Series B', 25000000.00, 2019),
('GreenEnergy Solutions', 'Sustainable energy storage technology developer', 'https://greenenergy-solutions.com', 'Clean Technology', 85, 'Series A', 12000000.00, 2020),
('HealthLink Digital', 'Telemedicine and digital health platform', 'https://healthlink-digital.com', 'Healthcare Technology', 200, 'Series C', 45000000.00, 2018),
('ChainTrack Systems', 'Blockchain supply chain solutions provider', 'https://chaintrack-systems.com', 'Blockchain Technology', 75, 'Series B', 18000000.00, 2021),
('FarmSense IoT', 'Smart agriculture IoT sensor company', 'https://farmsense-iot.com', 'Agricultural Technology', 120, 'Series A', 8000000.00, 2020);

-- Insert sample market trends
INSERT INTO market_trends (industry, growth_rate, market_size, key_trends, growth_drivers, barriers, competitive_intensity) VALUES
('Artificial Intelligence', 0.35, 15000000000.00, '["Machine learning adoption", "Automation", "AI ethics"]', '["Digital transformation", "Data availability", "Computing power"]', '["Regulatory uncertainty", "Talent shortage", "Ethics concerns"]', 'high'),
('Renewable Energy', 0.25, 8000000000.00, '["Battery technology", "Grid modernization", "Energy storage"]', '["Climate change", "Government incentives", "Cost reduction"]', '["Grid infrastructure", "Energy storage costs", "Policy changes"]', 'medium'),
('Healthcare Technology', 0.20, 12000000000.00, '["Telemedicine", "AI diagnostics", "Digital therapeutics"]', '["Aging population", "Cost pressures", "Technology adoption"]', '["Regulatory approval", "Privacy concerns", "Integration challenges"]', 'high'),
('Blockchain', 0.30, 5000000000.00, '["DeFi growth", "NFT markets", "Enterprise adoption"]', '["Financial innovation", "Trust requirements", "Decentralization"]', '["Regulatory uncertainty", "Energy consumption", "Scalability"]', 'medium'),
('Agricultural Technology', 0.18, 3000000000.00, '["Precision farming", "Drone technology", "AI crop monitoring"]', '["Food security", "Climate change", "Resource efficiency"]', '["Market education", "Infrastructure", "Technology adoption"]', 'low');

-- Insert sample market insights
INSERT INTO market_insights (title, summary, source, rag_status, confidence_score, industry, tags) VALUES
('AI Market Shows 35% Annual Growth', 'Artificial intelligence market continues robust expansion with strong enterprise adoption', 'Industry Report', 'GREEN', 0.92, 'Artificial Intelligence', '["growth", "AI", "enterprise"]'),
('Renewable Energy Storage Challenges', 'Battery technology advancement faces manufacturing and regulatory hurdles', 'Market Analysis', 'AMBER', 0.78, 'Renewable Energy', '["battery", "storage", "challenges"]'),
('Healthcare Data Privacy Concerns', 'Increasing regulatory scrutiny affects telemedicine platform development', 'Regulatory Update', 'RED', 0.85, 'Healthcare Technology', '["privacy", "regulation", "telemedicine"]'),
('Blockchain Enterprise Adoption Rising', 'Major corporations increasingly implementing blockchain for supply chain transparency', 'Corporate Survey', 'GREEN', 0.88, 'Blockchain', '["blockchain", "enterprise", "adoption"]'),
('Agricultural IoT Market Education Gap', 'Farmers require more education about IoT technology benefits and implementation', 'Farmer Survey', 'AMBER', 0.73, 'Agricultural Technology', '["IoT", "education", "agriculture"]');

COMMIT;