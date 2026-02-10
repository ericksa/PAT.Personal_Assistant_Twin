# PAT Usage Guide - Personal Assistant Twin

## 🎯 System Overview

PAT is your AI-powered interview assistant that helps you answer questions smoothly using your résumé and technical knowledge.

**Live Services:**
- 📡 **Agent Service** (8002) - AI brain with RAG from your documents
- 📥 **Ingest Service** (8001) - Document processing and embeddings  
- 🎤 **Whisper Service** (8004) - Audio transcription (interview questions)
- 📺 **Teleprompter** (8005) - On-screen display for answers
- 🗄️ **PostgreSQL + Redis + MinIO** - Data storage

## 🚀 How to Use

### 1. Upload Your Documents
Upload your résumé and technical docs to build your knowledge base:
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
curl -X POST http://localhost:8002/interview/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "What is your experience with Python?"}'
```

### 4. OpenWebUI Interface
For a full chat interface:
```bash
open http://localhost:3000
```

## 🎙️ Workflow: Actual Interview Scenario

1. **Interviewer asks question** → Whisper transcribes audio
2. **Agent Service** searches your documents (RAG)
3. **Agent generates answer** using your DeepSeek LLM
4. **Teleprompter displays answer** → You read it confidently

## 🔧 Technical Features

### DeepSeek Integration
- Uses your local DeepSeek-V3.1 model via Ollama
- No external API calls - completely private
- Fast responses using your powerful local model

### RAG System
- Searches your uploaded résumé and documents
- Provides personalized, accurate answers
- Real-time retrieval using pgvector embeddings

### On-Screen Teleprompter
- Professional interface optimized for reading
- Large, clear text display
- WebSocket real-time updates
- Responsive design (works on laptop/tablet)

## 📁 Project Structure

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

## 🚀 Next Steps

1. **Upload your actual résumé** to personalize the system
2. **Test with actual tech questions** you expect in interviews
3. **Customize the teleprompter appearance** if needed
4. **Add more technical documents** for better RAG coverage

Your PAT system is now ready for serious interview preparation! 🦞