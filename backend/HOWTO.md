# PAT System HOWTO Guide

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Initial Setup](#initial-setup)
5. [Basic Usage](#basic-usage)
6. [Document Management](#document-management)
7. [Interview Simulation](#interview-simulation)
8. [Teleprompter Operation](#teleprompter-operation)
9. [Advanced Features](#advanced-features)
10. [Troubleshooting](#troubleshooting)
11. [Maintenance](#maintenance)

## 🎯 System Overview

PAT (Personal Assistant Twin) is an AI-powered interview preparation system that helps you answer technical interview questions using your personal documents and local AI models.

**Core Components:**
- Agent Service (8002): AI brain with RAG capabilities
- Ingest Service (8001): Document processing and embedding
- Whisper Service (8004): Audio transcription
- Teleprompter Service (8005): Real-time answer display
- Supporting Services: PostgreSQL, Redis, MinIO, n8n

## 📋 Prerequisites

### Required Software
- Docker and Docker Compose (v2.0+)
- Ollama (latest version)
- Python 3.8+ (for testing scripts)
- Git (for cloning repository)

### Hardware Requirements
- Minimum 16GB RAM (32GB recommended)
- 20GB free disk space
- Modern CPU with 4+ cores

### Supported Operating Systems
- macOS 12+
- Ubuntu 20.04+
- Windows 11 with WSL2

## 🚀 Installation

### 1. Clone Repository
```bash
git clone [repository-url]
cd PAT/backend
```

### 2. Start Core Services
```bash
# Start all services in detached mode
docker-compose up -d

# Verify services are running
docker ps | grep backend
```

### 3. Install Ollama Models
```bash
# Install Ollama if not already installed
# Visit https://ollama.com for installation instructions

# Pull required models
ollama pull deepseek-v3.1:671b-cloud
ollama pull nomic-embed-text

# Verify models are available
ollama list
```

### 4. Verify Installation
```bash
# Check service health endpoints
curl -s http://localhost:8002/health | jq '.'
curl -s http://localhost:8004/health | jq '.'
curl -s http://localhost:8005/health | jq '.'
```

Expected output:
```json
{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "ingest": "healthy",
    "llm_provider": "ollama"
  }
}
```

## ⚙️ Initial Setup

### 1. Access Web Interfaces
- **Teleprompter**: http://localhost:8005
- **OpenWebUI**: http://localhost:3000
- **n8n Workflows**: http://localhost:5678

### 2. Configure Environment Variables
Create `.env` file if it doesn't exist:
```bash
cp .env.example .env  # if example exists
# Or create manually with required variables
```

### 3. Test Basic Functionality
```bash
# Test agent service
curl -X POST http://localhost:8002/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello", "user_id": "default"}'

# Test teleprompter
curl -X POST http://localhost:8005/broadcast \
  -H "Content-Type: application/json" \
  -d '{"message": "System is ready!"}'
```

## 📖 Basic Usage

### Quick Test Script
Run the automated test to verify everything works:
```bash
python3 pat_quick_test.py
```

### Manual Testing
```bash
# Simple query test
curl -X POST http://localhost:8002/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Python?", "user_id": "default"}'

# Complex query test
curl -X POST http://localhost:8002/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain the difference between Python lists and tuples", "user_id": "default"}'
```

## 📄 Document Management

### Upload Documents
```bash
# Upload a single document
curl -X POST http://localhost:8001/upload \
  -F "file=@/path/to/your-resume.pdf"

# Upload multiple documents
curl -X POST http://localhost:8001/upload \
  -F "file1=@/path/to/resume.pdf" \
  -F "file2=@/path/to/portfolio.docx"
```

### View Uploaded Documents
```bash
# List all documents
curl -X GET http://localhost:8001/documents

# Get specific document info
curl -X GET http://localhost:8001/documents/[document-id]
```

### Delete Documents
```bash
# Delete specific document
curl -X DELETE http://localhost:8001/documents/[document-id]

# Delete all documents (careful!)
curl -X DELETE http://localhost:8001/documents
```

## 🎙️ Interview Simulation

### Text-Based Simulation (Recommended for Testing)
```bash
# Process a text question (simulates transcription)
curl -X POST http://localhost:8004/process-question \
  -H "Content-Type: application/json" \
  -d '{"question": "What experience do you have with Python programming?"}'
```

### Audio-Based Simulation
```bash
# Record audio using system tools (QuickTime, Audacity, etc.)
# Save as WAV file, then:
curl -X POST http://localhost:8004/transcribe \
  -F "file=@your-recording.wav"
```

### Real Interview Workflow
1. **Prepare**: Open teleprompter in browser (http://localhost:8005)
2. **Ask**: Pose interview question verbally or via text
3. **Process**: System transcribes → analyzes → generates answer
4. **Display**: Answer appears automatically on teleprompter

## 📺 Teleprompter Operation

### Access Teleprompter
Open browser to: http://localhost:8005

### Manual Message Broadcasting
```bash
# Send custom message to teleprompter
curl -X POST http://localhost:8005/broadcast \
  -H "Content-Type: application/json" \
  -d '{"message": "Your custom message here"}'
```

### Teleprompter Features
- Real-time WebSocket updates
- Automatic answer display during interviews
- Manual message broadcasting
- Health status monitoring

## ⚡ Advanced Features

### Resume Generation
```bash
# Generate customized resume for specific job
curl -X POST http://localhost:8002/generate-resume \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Senior Python Developer",
    "template_type": "chronological"
  }'
```

### Custom Queries
```bash
# Use advanced query parameters
curl -X POST http://localhost:8002/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain your cloud experience",
    "user_id": "default",
    "tools": ["web_search"],
    "stream": false
  }'
```

### n8n Workflow Integration
Access workflows at: http://localhost:5678
- Create custom automation flows
- Integrate with external services
- Schedule regular document updates

## 🛠️ Troubleshooting

### Common Issues and Solutions

#### 1. Services Not Starting
```bash
# Check Docker status
docker ps

# View service logs
docker-compose logs [service-name]

# Restart specific service
docker-compose restart [service-name]

# Rebuild with fresh images
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

#### 2. Ollama Connection Issues
```bash
# Check Ollama status
ollama serve  # if not running

# Verify models
ollama list

# Test model directly
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "deepseek-v3.1:671b-cloud", "prompt": "Hello", "stream": false}'
```

#### 3. Slow Response Times
```bash
# Check system resources
docker stats

# Increase timeouts in service configurations
# Edit services/whisper/app.py timeout value

# Monitor GPU usage if available
nvidia-smi
```

#### 4. Teleprompter Not Updating
```bash
# Check WebSocket connection in browser console
# Verify Whisper service logs
docker logs whisper-service

# Test manual broadcast
curl -X POST http://localhost:8005/broadcast \
  -H "Content-Type: application/json" \
  -d '{"message": "Test"}'
```

### Diagnostic Commands
```bash
# Check all service health
./scripts/health-check.sh

# View system resources
docker stats

# Check disk usage
docker system df

# Clean up unused resources
docker system prune -a
```

## 🔧 Maintenance

### Regular Maintenance Tasks

#### 1. Update Services
```bash
# Pull latest changes
git pull origin main

# Rebuild services
docker-compose build --no-cache

# Restart services
docker-compose down
docker-compose up -d
```

#### 2. Backup Data
```bash
# Backup PostgreSQL data
docker exec postgres pg_dump -U llm llm > backup.sql

# Backup MinIO data
# Access MinIO console at http://localhost:9001
```

#### 3. Monitor Performance
```bash
# Check resource usage
docker stats

# View logs for specific service
docker logs [service-name] --tail 100

# Monitor Ollama
ollama list
ollama ps
```

#### 4. Clean Up
```bash
# Remove unused Docker images
docker image prune -a

# Clean build cache
docker builder prune

# Remove stopped containers
docker container prune
```

### Scheduled Tasks
Consider setting up cron jobs for:
- Weekly backups
- Daily health checks
- Monthly dependency updates
- Quarterly model updates

## 📈 Performance Optimization

### Memory Management
- Monitor container memory limits
- Adjust Docker resource allocation
- Use lightweight models when possible

### Model Selection
- `deepseek-v3.1:671b-cloud`: High quality, slower
- `llama3.2:3b`: Faster, good quality
- Choose based on your hardware and speed requirements

### Network Optimization
- Use local network for service communication
- Minimize external API calls
- Enable compression for large responses

## 🔒 Security Best Practices

### Data Privacy
- All processing happens locally
- No data leaves your machine
- Documents stored encrypted in MinIO

### Access Control
- Use strong passwords for n8n
- Limit network exposure
- Regular security audits

### Updates
- Keep Docker updated
- Update Ollama regularly
- Monitor for security advisories

## 📞 Support

For issues not covered in this guide:

1. **Check GitHub Issues**: Search existing issues
2. **View Logs**: `docker-compose logs --tail=100`
3. **Community Support**: Join Discord/Slack community
4. **Professional Support**: Contact support team

### Reporting Bugs
Include:
- System specifications
- Error messages and logs
- Steps to reproduce
- Expected vs actual behavior

---
*Last Updated: February 10, 2026*