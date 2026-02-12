# PAT MCP Server

**Multi-Chain Planning (MCP) + ReAct + RAG Stack** for the Personal Assistant Twin project.

## 🎯 Overview

The MCP Server implements an advanced AI reasoning stack that combines:

- **MCP (Multi-Chain Planning)**: Generate and execute multiple reasoning branches
- **ReAct (Reasoning + Acting)**: Chain of thought with tool use
- **RAG (Retrieval-Augmented Generation)**: Ground responses in indexed documents
- **Memory Management**: Short-term and long-term memory persistence

This creates a sophisticated agent capable of handling complex, multi-step interviews and knowledge retrieval tasks.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      MCP Server (Port 8003)                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ RAG Tools   │  │  ReAct      │  │   Memory Handlers   │  │
│  │             │  │  Tools      │  │                     │  │
│  │ - Search    │  │ - Reason    │  │ - Store             │  │
│  │ - Upload    │  │ - Plan      │  │ - Retrieve          │  │
│  │ - List      │  │ - Execute   │  │ - Search            │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
└─────────┼────────────────┼─────────────────────┼────────────┘
          │                │                     │
          ▼                ▼                     ▼
    ┌──────────┐    ┌──────────┐        ┌──────────┐
    │ Ingest   │    │ Agent    │        │   Redis  │
    │ Service  │    │ Service  │        │   Cache  │
    └──────────┘    └──────────┘        └──────────┘
```

## 🛠️ Available Tools

### RAG Tools (Retrieval Augmented Generation)
| Tool | Description |
|------|-------------|
| `rag_search` | Search through uploaded documents (resume, technical docs) |
| `rag_upload` | Upload a new document to the knowledge base |
| `rag_list_docs` | List all documents in the RAG system |

### ReAct Tools (Reasoning + Acting)
| Tool | Description |
|------|-------------|
| `reason_step` | Perform a single reasoning step with the LLM |
| `create_plan` | Create a multi-step plan for complex tasks |
| `execute_plan_step` | Execute a specific step in a multi-step plan |

### Memory Tools
| Tool | Description |
|------|-------------|
| `memory_store` | Store information in short-term memory |
| `memory_retrieve` | Retrieve information from memory |
| `memory_search` | Search through stored memories |

### Action Tools
| Tool | Description |
|------|-------------|
| `agent_query` | Query the PAT agent service with RAG |
| `interview_process` | Process an interview question through full pipeline |
| `teleprompter_broadcast` | Send message to teleprompter for display |
| `web_search` | Perform web search for current information |

## 🚀 Quick Start

### Installation

1. **Pull dependencies and build**:
```bash
cd backend
docker-compose build mcp-server
```

2. **Start the MCP server**:
```bash
docker-compose up -d mcp-server
```

3. **Verify the server is running**:
```bash
curl http://localhost:8003/health
```

### Usage Examples

#### 1. RAG Document Search
```bash
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
```

#### 2. Create a Multi-Step Plan
```bash
curl -X POST http://localhost:8003/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "create_plan",
    "arguments": {
      "goal": "Prepare for a technical interview",
      "context": "Position requires Python and React experience"
    }
  }'
```

#### 3. Process Interview Question
```bash
curl -X POST http://localhost:8003/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "interview_process",
    "arguments": {
      "question": "What is your experience with machine learning?",
      "source": "interviewer"
    }
  }'
```

#### 4. Store and Retrieve Memory
```bash
# Store memory
curl -X POST http://localhost:8003/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "memory_store",
    "arguments": {
      "key": "interview_progress",
      "value": "Discussed Python, moving to next question"
    }
  }'

# Retrieve memory
curl -X POST http://localhost:8003/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "memory_retrieve",
    "arguments": {
      "key": "interview_progress"
    }
  }'
```

## 🔌 MCP Client Integration

The server supports the standard MCP protocol. You can use it with any MCP-compatible client:

### Using MCP Python Client
```python
from mcp.client import Client

async with Client("pat-mcp") as mcp:
    # List available tools
    tools = await mcp.list_tools()
    print(f"Available tools: {tools}")

    # Call a tool
    result = await mcp.call_tool(
        "rag_search",
        {"query": "Python experience", "top_k": 5}
    )
    print(f"Result: {result}")
```

## 📊 Architecture Components

### 1. Tool Registry
- Centralized tool definitions with JSON schemas
- Categorized by functionality (RAG, ReAct, Memory, Action)
- Handlers map to appropriate service calls

### 2. RAG Handlers
- Connect to Ingest Service for document search
- Support for various file formats (PDF, TXT, DOCX)
- Vector similarity search with configurable thresholds

### 3. ReAct Handlers
- Multi-step planning with dependency tracking
- Reasoning step execution with LLM integration
- Plan persistence for conversation continuity

### 4. Memory Handlers
- Redis-backed short-term memory
- TTL support for expiring memories
- Full-text search across stored memories

### 5. Action Handlers
- Integration with existing PAT services
- Web search capabilities (DuckDuckGo)
- Teleprompter broadcast for interview mode

## 🔧 Configuration

Environment variables (set in `.env` or `docker-compose.yml`):

```bash
# Service URLs
INGEST_SERVICE_URL=http://ingest-service:8000
AGENT_SERVICE_URL=http://agent-service:8000
TELEPROMPTER_URL=http://teleprompter-app:8000
WHISPER_URL=http://whisper-service:8000

# Database & Cache
DATABASE_URL=postgresql://llm:llm@postgres:5432/llm
REDIS_URL=redis://redis:6379/0

# LLM Configuration
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

## 🧪 Testing

### Test MCP Server Health
```bash
curl http://localhost:8003/health
```

### List Available Tools
```bash
curl http://localhost:8003/tools
```

### List Tool Categories
```bash
curl http://localhost:8003/categories
```

### Execute a Tool
```bash
curl -X POST http://localhost:8003/execute \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "rag_search", "arguments": {"query": "test"}}'
```

## 📚 Advanced Features

### Multi-Chain Planning (MCP)
- Create complex plans with dependencies
- Execute steps in correct order
- Track progress and failures
- Backtrack and explore alternatives

### ReAct Reasoning
- Chain-of-thought prompting
- Tool use for factual accuracy
- Grounded in real-world data
- Reduces hallucinations

### RAG Grounding
- Retrieve from indexed documents
- Up-to-date information
- Source attribution
- Configurable similarity thresholds

### Memory Augmentation
- Maintain conversation state
- Store preferences and context
- Searchable memory store
- TTL-based expiration

## 🚨 Troubleshooting

### Server Won't Start
```bash
# Check logs
docker logs mcp-server

# Verify dependencies are running
docker ps
```

### Connection to Redis Fails
```bash
# Check Redis connection
docker exec mcp-server python -c "from redis import Redis; r = Redis('redis'); print(r.ping())"
```

### RAG Search Returns No Results
```bash
# Check if documents are indexed
curl http://localhost:8001/documents

# Lower threshold
curl -X POST http://localhost:8003/execute \
  -d '{"tool_name": "rag_search", "arguments": {"query": "test", "threshold": 0.1}}'
```

## 📈 Performance Optimization

- **Redis Caching**: Reuse memory across sessions
- **Async Operations**: Non-blocking I/O for better throughput
- **Connection Pooling**: Reuse HTTP connections
- **Vector Indexing**: Fast document retrieval with similarity search

## 🔒 Security

- All data stays within the Docker network
- No external API calls (except configured web search)
- Service-to-service communication only
- Environment-based configuration

## 📖 References

- [MCP Protocol](https://modelcontextprotocol.io/)
- [ReAct Paper](https://arxiv.org/abs/2210.03629)
- [LangGraph](https://python.langchain.com/docs/langgraph)
- [RAG Best Practices](https://www.anthropic.com/index/retrieval-augmented-generation)

## 🤝 Contributing

Add new tools by:
1. Defining in `tools.py` registry
2. Implementing handler in `handlers/`
3. Adding to `app.py` invocation logic
4. Updating documentation

## 📄 License

MIT License - See LICENSE file for details.

---

*Part of the Personal Assistant Twin (PAT) Project*
*Built with MCP + ReAct + RAG Stack*