# PAT - Personal Assistant Twin

**Your AI-powered personal assistant that helps you ace interviews, manage your calendar, process emails, and handle tasks intelligently.**

## 🎯 System Overview

PAT (Personal Assistant Twin) is a privacy-focused AI system designed to help professionals excel in technical interviews while also managing daily productivity tasks. It combines document retrieval, local LLM processing, real-time teleprompter display, calendar management, email processing, and task automation to provide a comprehensive personal assistant.

### Architecture

PAT uses a microservice architecture with the following components:

Core Services:
- **📡 Agent Service** (port 8002) - AI brain with RAG from your documents
- **📥 Ingest Service** (port 8001) - Document processing and embeddings
- **🎤 Whisper Service** (port 8004) - Audio transcription (interview questions)
- **📺 Teleprompter** (port 8005) - On-screen display for answers
- **📋 MCP Server** (port 8003) - Multi-Chain Planning + ReAct + RAG reasoning stack
- **🗄️ PostgreSQL** - Vector database for embeddings and PAT data
- **⚡ Redis** - Cache and session storage
- **☁️ MinIO** - Object storage for documents

PAT Core Services (NEW - Feb 2026):
- **🤖 PAT Core API** (port 8010) - Central personal assistant with calendar, email, and task management
  - **Calendar Management**: Smart scheduling, conflict detection, AI-powered optimization
  - **Email Processing**: Auto-classification, summarization, reply drafting, task extraction
  - **Task Management**: AI prioritization, Apple Reminders integration
  - **Apple Integration**: macOS AppleScript bridge for Calendar, Mail, Reminders
- **🔄 Sync Workers** - Background workers for bi-directional sync with Apple apps
  - Calendar sync worker (`PAT-cal`)
  - Email sync worker (`Mail`)
  - Reminders sync worker

Enterprise Services (Optional):
- **🌐 BFF Service** (port 8020) - Backend for Frontend GraphQL API
- **📊 RAG Scoring** (port 8030) - Market opportunity scoring engine
- **📈 Market Ingest** (port 8040) - Market data ingestion service
- **📄 Doc Generation** (port 8050) - Document generation service
- **🔔 Push Notifications** (port 8060) - Real-time alert service

### Key Features

Interview Assistant Features:
- 🔒 **100% Local Processing** - No data leaves your machine
- 🤖 **DeepSeek-V3.1 Integration** - Powerful local LLM via Ollama
- 📚 **RAG System** - Retrieves relevant info from your documents
- 📺 **Real-time Teleprompter** - Professional answer display
- 🎙️ **Whisper Transcription** - Converts speech to text

Personal Assistant (PAT Core) Features (NEW - Feb 2026):
- 📅 **Smart Calendar** - AI-powered scheduling, conflict detection, Apple Calendar sync
- 📧 **Email Intelligence** - Auto-classification, summarization, reply drafting, task extraction
- ✅ **Task Management** - AI prioritization, Apple Reminders integration
- 🍎 **Apple Integration** - Seamless sync with macOS Calendar, Mail, and Reminders via AppleScript
- 🧠 **Llama 3.2 3B** - Fast, efficient local LLM for personal tasks
- 🔗 **MCP Reasoning Stack** - Multi-Chain Planning + ReAct + RAG for complex tasks
- 🔄 **Background Sync** - Automated bidirectional sync workers

Enterprise Features:
- 🏢 **Business Intelligence** - Market opportunity analysis with RAG scoring
- 📄 **Document Generation** - Business plans, SOWs, RFPs with LLM assistance
- 📊 **Analytics Dashboard** - GraphQL API for business insights
- 🔔 **Push Notifications** - Real-time alerts for opportunities and updates

Frontend & Mobile:
- 📱 **iOS Client** - Swift/SwiftUI mobile app for on-the-go access
- 📡 **GraphQL API** - Unified backend for frontend applications

## 🚀 Quick Start

### Prerequisites

#### Required Software
- Docker and Docker Compose v2.0+
- Ollama (latest version)
- Python 3.8+ (for testing scripts)

#### Hardware Requirements
- Minimum 16GB RAM (32GB recommended)
- 20GB free disk space
- Modern CPU with 4+ cores

#### Supported Platforms
- macOS 12+
- Ubuntu 20.04+
- Windows 11 with WSL2

### Installation

#### 1. Clone and Setup
```bash
git clone <repository-url>
cd PAT/backend

# Copy environment template
cp .env.example .env
# Edit .env with your configuration
```

#### 2. Start Core Services
```bash
# Start all services in detached mode
docker-compose up -d

# Verify services are running
docker ps | grep backend
```

#### 4. Install Ollama Models
```bash
# Install Ollama from https://ollama.com if not already installed

# Pull required models
ollama pull deepseek-v3.1:671b-cloud
ollama pull nomic-embed-text
ollama pull llama3.2:3b  # NEW - for PAT Core personal assistant features

# Verify models
ollama list
```

#### 3. Install Ollama Models
```bash
# Install Ollama from https://ollama.com if not already installed

# Pull required models
ollama pull deepseek-v3.1:671b
ollama pull nomic-embed-text

# Verify models
ollama list
```

#### 4. Verify Installation
```bash
# Check service health
curl -s http://localhost:8002/health | jq '.'
curl -s http://localhost:8004/health | jq '.'
curl -s http://localhost:8005/health | jq '.'

# Run automated test
python3 pat_quick_test.py
```

### Access Points

Core Services:
- **Teleprompter**: http://localhost:8005
- **OpenWebUI**: http://localhost:3000
- **n8n Workflows**: http://localhost:5678
- **MinIO Console**: http://localhost:9001

Enterprise Services:
- **GraphQL API**: http://localhost:8020/graphql
- **APAT Service**: http://localhost:8010
- **RAG Scoring**: http://localhost:8030

## 📖 Usage Guide

### 1. Upload Your Documents

Build your knowledge base with your résumé and technical documents:

```bash
# Upload single document
curl -X POST http://localhost:8001/upload \
  -F "file=@/path/to/your-resume.pdf"

# Upload multiple documents
curl -X POST http://localhost:8001/upload \
  -F "file1=@/path/to/resume.pdf" \
  -F "file2=@/path/to/portfolio.docx"

# List uploaded documents
curl -X GET http://localhost:8001/documents
```

### 2. Test the Teleprompter

Open your browser to see the teleprompter:
```bash
open http://localhost:8005
```

Test broadcasting a message:
```bash
curl -X POST http://localhost:8005/broadcast \
  -H "Content-Type: application/json" \
  -d '{"message": "This is a test answer from your PAT system"}'
```

### 3. Simulate an Interview Question

#### Text-Based (Recommended for Testing)
```bash
# Simple query
curl -X POST http://localhost:8002/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is your experience with Python?", "user_id": "default"}'

# Complex query with RAG
curl -X POST http://localhost:8002/interview/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Explain the difference between Python lists and tuples"}'
```

#### Audio-Based (Real Interview Mode)
```bash
# Record audio using system tools, save as WAV, then:
curl -X POST http://localhost:8004/transcribe \
  -F "file=@your-recording.wav"
```

### 4. Full Interview Workflow

1. **Prepare**: Open teleprompter in browser (http://localhost:8005)
2. **Ask**: Interviewer poses question (verbally or via text)
3. **Process**: System transcribes → analyzes → generates answer using your documents
4. **Display**: Answer appears automatically on teleprompter
5. **Respond**: You read and respond confidently

## 🔧 Advanced Features

### Resume Generation
```bash
curl -X POST http://localhost:8002/generate-resume \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Senior Python Developer",
    "template_type": "chronological"
  }'
```

### n8n Workflow Integration
Access workflows at http://localhost:5678
- Create custom automation flows
- Integrate with external services
- Schedule regular document updates

## 🛠️ Development

### Project Structure
```
PAT/backend/
├── services/
│   ├── agent/              # AI brain with RAG
│   ├── ingest/             # Document processing
│   ├── teleprompter/       # On-screen display
│   ├── whisper/            # Audio transcription
│   ├── apat/               # Automation Prompt & Analytics Toolkit
│   ├── bff/                # Backend for Frontend GraphQL API
│   ├── rag-scoring/        # RAG scoring engine
│   ├── market-ingest/      # Market data ingestion
│   ├── doc-generation/     # Document generation
│   └── push-notifications/ # Push notification service
├── data/                  # Uploaded documents and models
├── scripts/               # Helper scripts
├── docs/                  # Documentation
├── docker-compose.yml     # Core service orchestration
└── docker-compose.enterprise.yml  # Enterprise service orchestration
```

### Making Changes

1. **Agent Service**: Modify `services/agent/app.py` for AI logic
2. **Teleprompter**: Modify `services/teleprompter/app.py` for display
3. **Whisper Service**: Modify `services/whisper/app.py` for transcription
4. **Ingest Service**: Modify `services/ingest/app.py` for document processing
5. **Rebuild**: `docker-compose build [service-name]`

### Testing Individual Components

```bash
# Test agent service
curl -X POST http://localhost:8002/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello", "user_id": "default"}'

# Test teleprompter
curl -X POST http://localhost:8005/broadcast \
  -H "Content-Type: application/json" \
  -d '{"message": "Test message"}'

# Test ingest service
curl -X GET http://localhost:8001/documents

# Test whisper service
curl -X GET http://localhost:8004/health
```

## 🔧 Troubleshooting

### Common Issues

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

#### 3. Teleprompter Not Updating
```bash
# Check WebSocket connection in browser console
# Verify Whisper service logs
docker logs whisper-service

# Test manual broadcast
curl -X POST http://localhost:8005/broadcast \
  -H "Content-Type: application/json" \
  -d '{"message": "Test"}'
```

#### 4. Slow Response Times
```bash
# Check system resources
docker stats

# Monitor GPU usage if available
nvidia-smi
```

### Health Checks

```bash
# Check all services
curl http://localhost:8002/health  # Agent
curl http://localhost:8004/health  # Whisper
curl http://localhost:8005/health  # Teleprompter

# View system resources
docker stats

# Check disk usage
docker system df
```

### Diagnostic Commands
```bash
# Clean up unused resources
docker system prune -a

# View logs for specific service
docker logs [service-name] --tail 100

# Monitor Ollama
ollama list
ollama ps
```

## 🔧 Maintenance

### Regular Updates
```bash
# Pull latest changes
git pull origin main

# Rebuild services
docker-compose build --no-cache

# Restart services
docker-compose down
docker-compose up -d
```

### Backup Data
```bash
# Backup PostgreSQL
docker exec postgres pg_dump -U llm llm > backup.sql

# MinIO data backup (via console at http://localhost:9001)
```

### Performance Optimization

#### Memory Management
- Monitor container memory limits: `docker stats`
- Adjust Docker resource allocation in Docker Desktop
- Use lighter models when possible

#### Model Selection Trade-offs
- `deepseek-v3.1:671b-cloud`: Highest quality, slower responses
- `llama3.2:3b`: Faster, good quality for most use cases
- Choose based on hardware and speed requirements

## 🔒 Security

### Data Privacy
- All processing happens locally
- No data leaves your machine
- Documents stored encrypted in MinIO

### Best Practices
- Use strong passwords for n8n (configured in .env)
- Keep Docker and Ollama updated
- Monitor for security advisories
- Regular backups of important data

## 📈 Performance

### System Requirements
| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 16GB | 32GB |
| Storage | 20GB | 50GB |
| CPU Cores | 4 | 8+ |
| GPU | Optional | NVIDIA with 8GB+ VRAM |

### Optimization Tips
- Use local network for service communication
- Minimize external API calls
- Enable compression for large responses
- Monitor with `docker stats` during interviews

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

## 📚 Documentation

- [CONTRIBUTING.md](docs/CONTRIBUTING.md) - Development guidelines
- [docs/FUTURE_ENHANCEMENTS.md](docs/FUTURE_ENHANCEMENTS.md) - Planned features
- [CHANGES.md](docs/CHANGES.md) - Version history
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture details
- [docs/new_capabilities.md](docs/new_capabilities.md) - New enterprise capabilities
- [docs/ENTERPRISE_GUIDE.md](docs/ENTERPRISE_GUIDE.md) - Enterprise features guide

## 👥 Support

For issues and feature requests:
1. Check GitHub Issues
2. Run diagnostic: `docker-compose logs --tail=100`
3. Include system specs and error messages
4. Open a new issue with reproduction steps

---

*Last Updated: February 10, 2026*