# services/agent/config.py
import logging
import os
from logging.handlers import RotatingFileHandler

# --- ENV VARS ---
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://llm:llm@postgres:5432/llm")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
INGEST_SERVICE_URL = "http://ingest-service:8000"

# Change this line
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
# --- RAG SETTINGS ---
TOP_K_INTERVIEW = int(os.getenv("TOP_K_INTERVIEW", "8"))
SCORE_THRESHOLD_INTERVIEW = float(os.getenv("SCORE_THRESHOLD_INTERVIEW", "0.15"))
TOP_K_GENERAL = int(os.getenv("TOP_K_GENERAL", "5"))
SCORE_THRESHOLD_GENERAL = float(os.getenv("SCORE_THRESHOLD_GENERAL", "0.2"))

# --- LLM MODEL ---
LLM_MODEL_INTERVIEW = os.getenv("LLM_MODEL_INTERVIEW", "glm-4.7:cloud")
LLM_MODEL_GENERAL = os.getenv("LLM_MODEL_GENERAL", "deepseek-v3.1:671b-cloud")

# --- TELEPROMPTER ---
TELEPROMPTER_ENABLED = os.getenv("TELEPROMPTER_ENABLED", "true").lower() == "true"

# --- LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        RotatingFileHandler("agent.log", maxBytes=10*1024*1024, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)