# services/tool_proxy/Dockerfile
# -------------------------------------------------
# Small Alpine‑based image that runs the FastAPI proxy.
# -------------------------------------------------
FROM python:3.12-slim

# 1️⃣ Set a safe, non‑root user (optional but recommended)
RUN useradd -m -u 1000 appuser
WORKDIR /app

# 2️⃣ Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY tool_proxy.py .

# 4️⃣ Run as the non‑root user
USER appuser

# 5️⃣ Expose the port FastAPI will listen on
EXPOSE 8000

# 6️⃣ Start the server
CMD ["uvicorn", "tool_proxy:app", "--host", "0.0.0.0", "--port", "8000"]