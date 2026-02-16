# AGENTS.md

## Overview
The **PAT** repository is a full‑stack personal assistant. The backend (Python/FastAPI) provides ingestion, search and LLM services; the frontend (Swift) offers a macOS/iOS UI. This file gives agentic coding agents commands, style guidelines and a high‑level plan for extending the system with LangChain + LlamaHub.


# Shared guardrails
READ ~/Projects/agent-scripts/AGENTS.MD BEFORE ANYTHING
## Build Commands

### Backend (Python)
```bash
# Start all services with Docker Compose (backend directory)
cd /Users/adamerickson/Projects/PAT/backend && docker compose up --build
```
Or run the API directly:
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### Frontend (Swift)
```bash
# Build the macOS app
cd /Users/adamerickson/Projects/PAT/frontend/PATapp/swiftclient && swift build
```
Run the app:
```bash
swift run PATApp
```

## Lint Commands

### Backend (Python)
The project uses `black` and `flake8`. Install them if missing:
```bash
pip install black flake8
```
Run linting and auto‑formatting:
```bash
black backend/ && flake8 backend/
```

### Frontend (Swift)
If `swiftlint` is installed, run:
```bash
swiftlint autocorrect && swiftlint
```
No `.swiftlint.yml` is present; create one if you want custom rules.

## Test Commands

### Backend (Python)
Run all tests:
```bash
pytest backend/tests/
```
Run a single test file or marker:
```bash
pytest backend/tests/test_health.py -k health
```

### Frontend (Swift)
```bash
swift test PATAppTests
```

## Code Style Guidelines

### Python
- Follow PEP‑8; use `black` for formatting.
- Import statements sorted alphabetically, grouped by standard library, third‑party, local modules.
- Use type hints everywhere; `Optional[T]` for nullable values.
- Raise custom exceptions with meaningful messages.
- Log at `INFO` or higher; avoid printing to stdout.

### Swift
- Imports sorted alphabetically, grouped by framework.
- Use `guard let` for optional binding; avoid force unwraps.
- Prefer SwiftUI over UIKit where possible.
- Keep file size < 200 lines; split large files into logical components.
- Use `async/await` for network calls; fallback to Combine if needed.
- Document public APIs with comments and SwiftDoc style.

## LangChain + LlamaHub Integration Plan

1. **Data Sources**  
   - PDFs, emails, notes stored on iCloud (use `icloudpy` or AppleScript).  
   - Each file will be processed by the ingestion service and stored in PostgreSQL with pgvector.

2. **Ingestion Service Enhancements**  
   - Add support for iCloud sync: a background task that watches the iCloud folder and triggers ingestion.  
   - Use LlamaHub connectors: `llama_hub.file`, `llama_hub.email`.  
   - Chunking with LangChain’s `RecursiveCharacterTextSplitter` (chunk_size=1000, chunk_overlap=200).  
   - Embed with chosen model (`text-embedding-ada-002` or local `bge-m3`).  
   - Store embeddings in pgvector; attach metadata (source, timestamp, size).

3. **Search API**  
   - Expose `/search` endpoint in the ingestion service that accepts `query`, optional `domain`.  
   - Use vector similarity search (pgvector) to retrieve top‑k results.  
   - Return JSON with snippet, source path, relevance score.

4. **RAG Service**  
   - Wrap the search API and LLM generation (Ollama or OpenAI) into a LangChain chain.  
   - Provide `/chat` endpoint that accepts user prompt, retrieves context via search, and generates response.  
   - Store conversation history in SwiftData for offline usage.

5. **Frontend Integration**  
   - Add `IngestClient.swift` and `SearchClient.swift`.  
   - UI: “Ingest Now” button in MenuBar; chat view uses `SearchClient` to fetch context before sending prompt.  
   - Show ingestion status and search results in a sidebar.

6. **Testing & Monitoring**  
   - Unit tests for ingestion, search, and RAG endpoints.  
   - Prometheus metrics exposed by each service; Grafana dashboards in `docker-compose.enterprise.yml`.  
   - Log ingestion events to a dedicated table for audit.

## Environment & Secrets
- Store API keys (OpenAI, Anthropic) in `.env` files or Docker secrets.
- Use `python-dotenv` to load environment variables in the backend.
- For Swift, use a `.xcconfig` file or `KeychainAccess` to store secrets securely.

## CI/CD Pipeline
- GitHub Actions: lint, test, build Docker images, run integration tests.
- Deploy to a staging environment before production.

## TODO List

- [ ] Add `.swiftlint.yml` with custom rules.  
- [ ] Implement iCloud sync in ingestion service.  
- [ ] Create `IngestClient.swift` and `SearchClient.swift`.  
- [ ] Add `/search` endpoint to ingestion service.  
- [ ] Wire RAG chain into BFF for chat API.  
- [ ] Write unit tests for new endpoints.  
- [ ] Update Docker Compose to expose ingestion and search ports.  
- [ ] Document API endpoints in `frontend/web-manager/src/FRONTEND_API_REFERENCE.md`.  
- [ ] Add monitoring dashboards for ingestion latency.  
- [ ] Create feature flag struct `ThinkConfig` in Swift to enable high‑depth mode.  
- [ ] Refactor UI components from `enchanted-main` into PAT client, updating imports.  
- [ ] Ensure all new Swift files compile and run with `swift build`.  
- [ ] Verify that ingestion service logs events to a table and can be queried via `/search`.  
- [ ] Run integration tests against the full stack (backend + frontend).  
