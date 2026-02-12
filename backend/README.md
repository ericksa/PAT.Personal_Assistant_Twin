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

### What's New (Feb 2026)

- ✅ **MCP Server** - Multi-Chain Planning + ReAct + RAG reasoning stack
- ✅ **PAT Core API** - Complete personal assistant with calendar, email, and task management
- ✅ **Apple Integration** - macOS sync workers for Calendar, Mail, and Reminders
- ✅ **Llama 3.2 3B** - Fast local LLM optimized for personal tasks
- ✅ **iOS Client** - Swift/SwiftUI mobile app for PAT Core
- ✅ **Comprehensive Testing** - Automated API test suite for all services
- ✅ **Enhanced Documentation** - Complete developer docs and API references

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

#### 3. Start Enterprise Services (Optional)
For advanced business capabilities, start the enterprise services:
```bash
# Start enterprise services
docker-compose -f docker-compose.enterprise.yml up -d

# Verify enterprise services are running
docker ps | grep enterprise
```

#### 4. Setup PAT Core Database (NEW)
```bash
# Run PAT Core database migration
docker-compose exec postgres psql -U llm -d llm -f scripts/migrations/002_add_pat_core_tables.sql
```

#### 5. Install Ollama Models (UPDATED)
```bash
# Install Ollama from https://ollama.com if not already installed

# Pull required models
ollama pull deepseek-v3.1:671b-cloud
ollama pull nomic-embed-text
ollama pull llama3.2:3b  # NEW - for PAT Core personal assistant features

# Verify models
ollama list
```

#### 6. Start PAT Core API (NEW - macOS Only)
```bash
# Navigate to PAT Core source directory
cd src

# Start PAT Core API server
python3 main_pat.py

# PAT Core API will be available at http://localhost:8010
# Access Swagger UI: http://localhost:8010/docs
```

#### 7. Start Sync Workers (NEW - macOS Only)
```bash
# Run start script from backend root
./scripts/start_sync_workers.sh

# This starts background workers for:
# - Calendar sync (PAT-cal)
# - Email sync (Mail)
# - Reminders sync

# Stop workers when done
./scripts/stop_sync_workers.sh
```

#### 8. Verify Installation
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
- **MCP Server**: http://localhost:8003
- **OpenWebUI**: http://localhost:3000
- **n8n Workflows**: http://localhost:5678
- **MinIO Console**: http://localhost:9001

PAT Core (NEW):
- **PAT Core API**: http://localhost:8010
- **Swagger UI**: http://localhost:8010/docs
- **ReDoc**: http://localhost:8010/redoc

Enterprise Services:
- **GraphQL API**: http://localhost:8020/graphql
- **APAT Service**: http://localhost:8010
- **RAG Scoring**: http://localhost:8030

iOS Client (NEW):
- Swift/SwiftUI iOS app available in `frontend/swiftclient/PATclient/`

## 📖 Usage Guide

### Interview Assistant Usage

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

---

### Personal Assistant (PAT Core) Usage

NEW - Feb 2026: PAT Core provides comprehensive personal assistant capabilities including calendar, email, and task management with AI intelligence.

#### Testing PAT Core API

```bash
# Test LLM connection
curl -X POST http://localhost:8010/pat/chat/test-connection

# Check system info
curl http://localhost:8010/pat/info
```

#### Calendar Management

```bash
# Create a new calendar event
curl -X POST http://localhost:8010/pat/calendar/events \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Team Standup",
    "description": "Weekly team sync",
    "location": "Conference Room A",
    "start_time": "2024-02-13T09:00:00",
    "end_time": "2024-02-13T09:30:00",
    "priority": 5
  }'

# List all events
curl http://localhost:8010/pat/calendar/events

# Detect conflicts
curl http://localhost:8010/pat/calendar/conflicts

# Get free slots
curl "http://localhost:8010/pat/calendar/free-slots?start=2024-02-13&end=2024-02-14"

# Smart rescheduling with AI
curl -X POST http://localhost:8010/pat/calendar/events/{event_id}/reschedule \
  -H "Content-Type: application/json" \
  -d '{"reason": "Client meeting changed"}'

# Sync with Apple Calendar (macOS only)
curl -X POST http://localhost:8010/pat/calendar/sync/apple
```

#### Email Processing

```bash
# Classify an email
curl -X POST http://localhost:8010/pat/emails/classify \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Team Meeting Tomorrow",
    "sender": "client@example.com",
    "body": "We should meet tomorrow to discuss the project deliverables. Let me know what times work for you."
  }'

# Summarize an email
curl -X POST http://localhost:8010/pat/emails/summarize \
  -H "Content-Type: application/json" \
  -d '{"subject": "...", "sender": "...", "body": "..."}'

# Draft a reply
curl -X POST http://localhost:8010/pat/emails/draft-reply \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Re: Meeting Tomorrow",
    "sender": "client@example.com",
    "body": "We should meet tomorrow to discuss the project deliverables.",
    "tone": "professional"
  }'

# Extract tasks from email
curl -X POST http://localhost:8010/pat/emails/extract-tasks \
  -H "Content-Type: application/json" \
  -d '{"subject": "...", "body": "..."}'

# Extract meeting details
curl -X POST http://localhost:8010/pat/emails/extract-meeting \
  -H "Content-Type: application/json" \
  -d '{"subject": "...", "body": "..."}'
```

#### Task Management

```bash
# List tasks (via API - full implementation pending)
curl http://localhost:8010/pat/tasks

# Create task (via API - full implementation pending)
curl -X POST http://localhost:8010/pat/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Follow up with client", "priority": "high"}'
```

#### Chat with LLM

```bash
# Send a chat message
curl -X POST http://localhost:8010/pat/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "What should I focus on today?"}
    ]
  }'
```

#### Background Sync Workers

```bash
# Start all sync workers (macOS only)
./scripts/start_sync_workers.sh

# Stop all sync workers
./scripts/stop_sync_workers.sh

# Workers will:
# - Sync calendar events with Apple Calendar
# - Process and classify emails from Apple Mail
# - Sync tasks with Apple Reminders
```

## 🔧 Advanced Features

### MCP Server (Multi-Chain Planning + ReAct + RAG)

```bash
# Search documents via RAG
curl -X POST http://localhost:8003/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "rag_search",
    "arguments": {
      "query": "Python experience",
      "top_k": 5,
      "threshold": 0.2
    }
  }'

# Create a multi-step plan with ReAct
curl -X POST http://localhost:8003/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "create_plan",
    "arguments": {
      "goal": "Prepare for a technical interview",
      "context": "Position requires Python and React experience"
    }
  }'

# List available tools
curl http://localhost:8003/tools

# List tool categories
curl http://localhost:8003/categories
```

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

### API Testing (NEW)

```bash
# Run comprehensive API test suite
./scripts/test_pat_api.sh
```

## 🛠️ Development

### Project Structure
```
PAT/backend/
├── services/
│   ├── agent/              # AI brain with RAG
│   ├── ingest/             # Document processing
│   ├── teleprompter/       # On-screen display
│   ├── whisper/            # Audio transcription
│   ├── mcp/                # MCP Server (ReAct + RAG reasoning stack)
│   ├── apat/               # Automation Prompt & Analytics Toolkit
│   ├── bff/                # Backend for Frontend GraphQL API
│   ├── rag-scoring/        # RAG scoring engine
│   ├── market-ingest/      # Market data ingestion
│   ├── doc-generation/     # Document generation
│   └── push-notifications/ # Push notification service
├── src/                   # PAT Core API (NEW)
│   ├── api/                # PAT Core API routes (calendar, email, task, chat)
│   ├── models/             # Pydantic models for PAT Core
│   ├── repositories/       # Database repositories
│   ├── services/           # Business logic services
│   ├── config/             # Configuration (LLM, logging)
│   └── utils/              # Utility classes (AppleScript managers)
├── scripts/               # Helper scripts
│   ├── migrations/         # Database migrations
│   ├── pat_sync_worker.py  # Background sync workers (NEW)
│   ├── start_sync_workers.sh
│   ├── stop_sync_workers.sh
│   └── test_pat_api.sh     # API test suite (NEW)
├── data/                  # Uploaded documents and models
├── docs/                  # Documentation
├── logs/                  # Application logs (NEW)
├── docker-compose.yml     # Core service orchestration
└── docker-compose.enterprise.yml  # Enterprise service orchestration
```

### Making Changes

#### Interview Assistant Services
1. **Agent Service**: Modify `services/agent/app.py` for AI logic
2. **Teleprompter**: Modify `services/teleprompter/app.py` for display
3. **Whisper Service**: Modify `services/whisper/app.py` for transcription
4. **Ingest Service**: Modify `services/ingest/app.py` for document processing
5. **Rebuild**: `docker-compose build [service-name]`

#### PAT Core (NEW)
1. **API Routes**: Modify `src/api/pat_routes.py` for endpoints
2. **Services**: Modify `src/services/` for business logic
3. **Models**: Update `src/models/` for data structures
4. **Restart**: Stop `python3 main_pat.py` and restart

### Testing Individual Components

#### Interview Assistant Tests

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

# Test MCP server
curl http://localhost:8003/health
curl http://localhost:8003/tools
```

#### PAT Core Tests (NEW)

```bash
# Test PAT Core health
curl http://localhost:8010/pat/health

# Test PAT Core info
curl http://localhost:8010/pat/info

# Test LLM connection
curl -X POST http://localhost:8010/pat/chat/test-connection

# Test calendar events
curl http://localhost:8010/pat/calendar/events

# Test email classification
curl -X POST http://localhost:8010/pat/emails/classify \
  -H "Content-Type: application/json" \
  -d '{"subject": "Test", "sender": "test@test.com", "body": "Test body"}'

# Run comprehensive test suite
./scripts/test_pat_api.sh
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

#### 5. PAT Core Not Starting (NEW)
```bash
# Check if PAT Core is running
ps aux | grep main_pat.py

# Check PAT Core logs
tail -f logs/pat_core.log

# Test database connection
docker exec postgres psql -U llm -d llm -c "\dt"

# Verify database tables exist
docker exec postgres psql -U llm -d llm -c "\d users"
```

#### 6. Apple Integration Issues (NEW - macOS Only)
```bash
# Test AppleScript access
osascript -e 'tell application "Calendar" to get name of calendars'

# Check for running sync workers
ps aux | grep pat_sync_worker

# View sync worker logs
tail -f logs/calendar_sync.log
tail -f logs/email_sync.log
tail -f logs/reminders_sync.log
```

### Health Checks

```bash
# Interview Assistant Services
curl http://localhost:8002/health  # Agent
curl http://localhost:8004/health  # Whisper
curl http://localhost:8005/health  # Teleprompter
curl http://localhost:8003/health  # MCP Server

# PAT Core Services (NEW)
curl http://localhost:8010/pat/health  # PAT Core
curl http://localhost:8010/pat/info     # System info
curl http://localhost:8010/docs         # Swagger UI

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

- [Master Documentation Index](docs/MASTER_DOCUMENTATION_INDEX.md) - Central map of all project documentation
- [Architecture Details](docs/ARCHITECTURE.md) - System architecture and component diagram
- [Implementation Status](PAT_CORE_IMPLEMENTATION_STATUS.md) - Latest development updates
- [Backend Todo List](BACKEND_TODO.md) - Active development tasks
- [Frontend API Reference](FRONTEND_API_REFERENCE.md) - PAT Core API specification for clients
- [Infrastructure Setup](INFRASTRUCTURE.md) - Metrics, logging, and observability details
- [Enterprise Features Guide](docs/ENTERPRISE_GUIDE.md) - Advanced business intelligence features
- [Contributing Guidelines](docs/CONTRIBUTING.md) - How to develop and extend PAT
- [Future Roadmap](docs/FUTURE_ENHANCEMENTS.md) - Upcoming features and integrations
- [MCP Server Docs](services/mcp/README.md) - Details on the planning reasoning stack

## 🚀 Future Plans

### Short-term (Next 1-2 months)
- **Real-time Microphone Integration** - Direct audio input processing for interviews
- **Enhanced Document Processing** - Support for DOCX, PPTX, and image-based documents
- **Mobile-Responsive Teleprompter** - Better mobile and tablet support
- **Basic Analytics Dashboard** - Track interview performance and improvement
- **Complete Email Service** - Full email repository with Apple Mail integration
- **Complete Task Service** - Full task repository with Apple Reminders integration

### Mid-term (3-6 months)
- **Behavioral Interview Templates** - Pre-built responses for common behavioral questions
- **Voice Analysis Features** - Tone, pace, and confidence recommendations
- **Team Collaboration Tools** - Share documents and answers with colleagues
- **Advanced RAG Improvements** - Semantic chunking and hybrid search
- **Full Workflow Orchestration** - End-to-end automation (email → calendar → tasks)
- **Native Mobile Applications** - iOS and Android apps

### Long-term (6+ months)
- **Enterprise Deployment Options** - Kubernetes-ready configurations
- **AI-Powered Interview Coaching** - Real-time feedback and suggestions
- **Industry-Specific Customization** - Tailored models for different domains
- **Advanced Analytics & Reporting** - Detailed performance metrics and insights
- **Multi-language Support** - Internationalization and localization
- **Cloud Deployment Options** - Hybrid local/cloud architecture for enterprise users

For detailed information on planned features, see [docs/FUTURE_ENHANCEMENTS.md](docs/FUTURE_ENHANCEMENTS.md).

## 👥 Support

For issues and feature requests:
1. Check GitHub Issues
2. Run diagnostic: `docker-compose logs --tail=100`
3. Include system specs and error messages
4. Open a new issue with reproduction steps

---

*Last Updated: February 12, 2026*