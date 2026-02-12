# PATclient

**Personal Assistant Twin - macOS Client**

A sleek, modern macOS application that serves as the interface for the PAT (Personal Assistant Twin) backend system. Built with SwiftUI, it provides chat, document management, LLM integration, and teleprompter capabilities.

---

## Features

- **Real-time Chat** - Interactive chat interface with persistent sessions
- **Document Ingestion** - Upload and search documents using RAG
- **LLM Integration** - Multiple models via Ollama and MLX
- **Teleprompter** - Live voice-to-text transcription display
- **Session Management** - Organize chats by date and categories
- **Export Options** - Markdown, JSON, PDF, HTML, Word, Plain Text
- **Service Health** - Real-time status monitoring

---

## Prerequisites

- macOS 26.2 or later
- Xcode 26.2+
- Ollama installed and running
- PAT backend services (Agent, Ingest, Whisper)

---

## Quick Start

1. Open `PATclient.xcodeproj` in Xcode
2. Select `PATclient` target
3. Press ⌘R to build and run
4. Configure service URLs in `Config.swift` if needed
5. Start required backend services (see Backend Setup)

---

## Backend Setup

The PATclient communicates with multiple backend services:

| Service | Port | Purpose |
|---------|------|---------|
| Agent | 8002 | AI brain, RAG, chat processing |
| Ingest | 8001 | Document upload and search |
| Whisper | 8004 | Audio transcription |
| Ollama | 11434 | LLM models |

---

## Features in Detail

### Chat Interface
- Persistent chat sessions
- Message history per session
- Model selection and configuration

### Document Management
- Upload resume (PDF, DOCX)
- Upload documents for RAG search
- Search indexed documents

### Export Options
- Markdown (.md)
- JSON (.json)
- PDF
- HTML (.html)
- Word (.docx)
- Plain Text (.txt)

### Session Organization
- Date-based grouping (days/weeks/months/years)
- Category/project tags
- Drag & drop between groups
- Search sessions

---

## Configuration

Edit `Config.swift` to update service URLs:

```swift
struct Config {
    static let agentBaseURL = "http://127.0.0.1:8002"
    static let ingestBaseURL = "http://127.0.0.1:8001"
    static let whisperBaseURL = "http://127.0.0.1:8004"
    static let ollamaBaseURL = "http://127.0.0.1:11434"
}
```

---

## Troubleshooting

### Service Connection Issues
- Ensure services are running on configured ports
- Check firewall settings
- Verify backend logs for errors

### Model Selection Issues
- Ensure Ollama is running
- Refresh available models in Settings
- Check model availability in `ollama list`

### Document Upload Issues
- Verify Ingest service is running
- Check file permissions
- Ensure documents are supported format

---

## Architecture

**Swift UI Layer**
- `ChatView` - Main chat interface
- `SessionListView` - Session management
- `SettingsView` - App configuration

**Services**
- `AgentService` - Backend communication
- `LLMService` - Ollama integration
- `IngestService` - Document operations

**Data Models**
- `ChatSession` - Chat sessions
- `Message` - Individual messages
- `Source` - Document references

---

## Development

### Project Structure
```
PATclient/
├── PATclientApp.swift      # App entry point
├── Services/               # Backend integrations
├── Views/                  # SwiftUI views
├── ViewModels/             # State management
├── Models/                 # Data models
├── Config.swift           # Service configuration
└── Logger.swift           # Logging infrastructure
```

### Adding Features
1. Add view files to `Views/`
2. Add service files to `Services/`
3. Add models to `Models/`
4. Update `ChatViewModel` for state changes

---

## License

MIT License