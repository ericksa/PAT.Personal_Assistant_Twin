# PAT - Personal Assistant Twin

![PAT Logo](docs/pat-logo.png)

**Your AI-powered interview assistant that helps you answer questions smoothly using your résumé and technical knowledge.**

## 🎯 System Overview

PAT (Personal Assistant Twin) is a privacy-focused AI system designed to help professionals excel in technical interviews. It combines document retrieval, local LLM processing, and real-time teleprompter display to provide instant, personalized answers to interview questions.

### Live Services
- 📡 **Agent Service** (8002) - AI brain with RAG from your documents
- 📥 **Ingest Service** (8001) - Document processing and embeddings
- 🎤 **Whisper Service** (8004) - Audio transcription (interview questions)
- 📺 **Teleprompter** (8005) - On-screen display for answers
- 🗄️ **PostgreSQL + Redis + MinIO** - Data storage

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Ollama (for local LLM processing)
- Python 3.8+

### Installation

1. **Start the core services:**
```bash
docker-compose up -d
```

2. **Install Ollama and required models:**
```bash
# Install Ollama from https://ollama.com
ollama pull deepseek-v3.1:671b
ollama pull nomic-embed-text
```

3. **Verify services are running:**
```bash
curl http://localhost:8002/health
curl http://localhost:8004/health
curl http://localhost:8005/health
```

4. **Access the interfaces:**
- Teleprompter: http://localhost:8005
- OpenWebUI: http://localhost:3000

## 📖 Usage Guide

### 1. Upload Your Documents
Build your knowledge base with your résumé and technical documents:
```bash
curl -X POST http://localhost:8001/upload \
  -F "file=@/path/to/your-resume.pdf"
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
Send a test question to see RAG in action:
```bash
curl -X POST http://localhost:8002/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is your experience with Python?", "user_id": "default"}'
```

### 4. Full Interview Workflow
1. **Interviewer asks question** → Whisper transcribes audio
2. **Agent Service** searches your documents (RAG)
3. **Agent generates answer** using your DeepSeek LLM
4. **Teleprompter displays answer** → You read it confidently

## 🛠️ Development

### Project Structure
```
PAT/backend/
├── services/
│   ├── agent/           # AI brain with RAG
│   ├── ingest/          # Document processing
│   ├── teleprompter/    # On-screen display
│   └── whisper/         # Audio transcription
├── data/               # Uploaded documents
└── docker-compose.yml  # Service orchestration
```

### Making Changes

1. **Agent Service**: Modify `services/agent/app.py` for AI logic
2. **Teleprompter**: Modify `services/teleprompter/app.py` for display
3. **Whisper Service**: Modify `services/whisper/app.py` for transcription
4. **Rebuild**: `docker-compose build [service-name]`

### Testing

Run the quick test script:
```bash
python3 pat_quick_test.py
```

Or test individual components:
```bash
# Test agent service
curl -X POST http://localhost:8002/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello", "user_id": "default"}'

# Test teleprompter
curl -X POST http://localhost:8005/broadcast \
  -H "Content-Type: application/json" \
  -d '{"message": "Test message"}'
```

## 🔧 Troubleshooting

### Common Issues

1. **Ollama Connection Errors**
   - Ensure Ollama is running: `ollama serve`
   - Check model availability: `ollama list`
   - Verify model name matches: `deepseek-v3.1:671b-cloud`

2. **Service Not Responding**
   - Check Docker containers: `docker ps`
   - View logs: `docker logs [service-name]`
   - Restart services: `docker-compose restart`

3. **Teleprompter Not Updating**
   - Check WebSocket connection in browser console
   - Verify Whisper service is sending to correct endpoint
   - Confirm agent service is returning proper response format

### Health Checks
```bash
# Check all services
curl http://localhost:8002/health  # Agent
curl http://localhost:8004/health  # Whisper
curl http://localhost:8005/health  # Teleprompter
```

## 📈 Future Enhancements

See [FUTURE_ENHANCEMENTS.md](FUTURE_ENHANCEMENTS.md) for planned features.

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

## 👥 Support

For issues and feature requests, please open a GitHub issue.