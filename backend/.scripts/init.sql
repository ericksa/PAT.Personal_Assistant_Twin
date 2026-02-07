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
-- Insert sample resume data
INSERT INTO documents (filename, content, metadata) VALUES
                                                        ('technical_skills.txt', 'Technology Used: SharePoint, SharePoint Designer, Microsoft Office 365, VMware, GoToAssist, IIS, Windows Server 2016, PowerShell, Kickstart, Windows 2007 & 10, Unix, Linux, Mac OS X, iOS, Android, LAN, WAN, SAN, TCP/IP, HTTP, Wireless, AnyConnect VPN, Switches, Active Directory Domain Controllers, Group Policy Objects, Printers, Projectors.', '{"category": "technical_skills"}'),
                                                        ('cloud_infrastructure.txt', 'Cloud Infrastructure: AWS EC2 S3 Lambda Redshift EKS GovCloud, Docker, VMware ESXi, Kubernetes. DevSecOps: Jenkins, GitLab CI/CD, Maven, Gradle, SonarQube, Fortify, Splunk, Jira, Git.', '{"category": "cloud_infrastructure"}');