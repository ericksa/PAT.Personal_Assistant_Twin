# Service configurations matching docker-compose.yml
import os

PYTHON_SERVICES = {
    "core": {
        "name": "Core API",
        "description": "PAT Core API - Calendar, Email, Tasks, Chat",
        "type": "python",
        "module": None,
        "script": "src.main_pat",
        "port": 8010,
        "health_url": "http://localhost:8010/pat/health",
    },
    "sync": {
        "name": "Sync Worker",
        "description": "Background Apple Mail/Reminders sync",
        "type": "python",
        "module": None,
        "script": "scripts/pat_sync_worker.py",
        "port": None,
        "health_url": None,
    },
    "listening": {
        "name": "Interview Listener",
        "description": "Live audio capture and transcription",
        "type": "python",
        "module": None,
        "script": "services/listening/live_interview_listener.py",
        "port": None,
        "health_url": None,
    },
}

DOCKER_SERVICES = {
    "postgres": {
        "name": "PostgreSQL",
        "description": "Vector database with pgvector extension",
        "container_name": "pgvector",
        "compose_service": "postgres",
        "port": 5432,
        "depends_on": [],
    },
    "redis": {
        "name": "Redis",
        "description": "Cache and agent memory",
        "container_name": "redis",
        "compose_service": "redis",
        "port": 6379,
        "depends_on": [],
    },
    "minio": {
        "name": "MinIO",
        "description": "Object storage (S3 API + Console)",
        "container_name": "minio",
        "compose_service": "minio",
        "port": 9000,
        "depends_on": [],
    },
    "n8n": {
        "name": "n8n",
        "description": "Workflow orchestration",
        "container_name": "n8n",
        "compose_service": "n8n",
        "port": 5678,
        "depends_on": ["postgres"],
    },
    "ingest-service": {
        "name": "Ingest Service",
        "description": "Document processing and embeddings",
        "container_name": "ingest-service",
        "compose_service": "ingest-service",
        "port": 8001,
        "depends_on": ["postgres", "redis", "minio"],
    },
    "agent-service": {
        "name": "Agent Service",
        "description": "RAG from documents and LLM routing",
        "container_name": "agent-service",
        "compose_service": "agent-service",
        "port": 8002,
        "depends_on": ["postgres", "redis"],
    },
    "mcp-server": {
        "name": "MCP Server",
        "description": "Multi-Chain Planning + ReAct + RAG",
        "container_name": "mcp-server",
        "compose_service": "mcp-server",
        "port": 8003,
        "depends_on": ["postgres", "redis", "ingest-service", "agent-service"],
    },
    "teleprompter-app": {
        "name": "Teleprompter",
        "description": "On-screen display service",
        "container_name": "interview-teleprompter",
        "compose_service": "teleprompter-app",
        "port": 8005,
        "depends_on": ["agent-service"],
    },
    "whisper-service": {
        "name": "Whisper Service",
        "description": "Voice transcription",
        "container_name": "whisper-service",
        "compose_service": "whisper-service",
        "port": 8004,
        "depends_on": ["agent-service"],
    },
    "job-search-service": {
        "name": "Job Search",
        "description": "Automated job crawling",
        "container_name": "job-search-service",
        "compose_service": "job-search-service",
        "port": 8007,
        "depends_on": ["postgres"],
    },
    "prometheus": {
        "name": "Prometheus",
        "description": "Metrics collection",
        "container_name": "prometheus",
        "compose_service": "prometheus",
        "port": 9090,
        "depends_on": ["job-search-service"],
    },
    "grafana": {
        "name": "Grafana",
        "description": "Visualization dashboards",
        "container_name": "grafana",
        "compose_service": "grafana",
        "port": 3001,
        "depends_on": ["prometheus"],
    },
}

# Merge all services
ALL_SERVICES = {**PYTHON_SERVICES, **DOCKER_SERVICES}

# Startup order
START_ORDER = [
    "postgres",
    "redis",
    "minio",
    "n8n",
    "ingest-service",
    "agent-service",
    "core",
    "mcp-server",
    "whisper-service",
    "teleprompter-app",
    "job-search-service",
    "prometheus",
    "grafana",
    "sync",
    "listening",
]
