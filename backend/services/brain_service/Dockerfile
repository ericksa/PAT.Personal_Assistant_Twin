# ---------- 1️⃣ Base ----------
FROM python:3.12-slim

# ---------- 2️⃣ System deps (optional) ----------
RUN apt-get update && apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# ---------- 3️⃣ Working directory ----------
WORKDIR /app

# ---------- 4️⃣ Install Python deps ----------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------- 5️⃣ Copy source ----------
# Explicit copy avoids accidental .dockerignore exclusion
COPY main.py ./brain_service/
COPY main.py .
# (If you have other top‑level files you want, copy them too)
COPY . .

# ---------- 6️⃣ Make sure the package is importable ----------
# WORKDIR is already on PYTHONPATH, but setting it explicitly never hurts
ENV PYTHONPATH=/app

# ---------- 7️⃣ Expose port ----------
EXPOSE 8000

# ---------- 8️⃣ Run the app ----------
# Adjust if your FastAPI instance lives in a different module
CMD ["python", "main.py"]