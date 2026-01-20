FROM python:3.11-slim

WORKDIR /app

# System dependencies FIRST
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    python3-dev \
    tesseract-ocr \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies (PINNED)
RUN pip install --no-cache-dir \
    torch \
    safetensors \
    huggingface_hub==0.19.4 \
    transformers==4.33.3 \
    sentence-transformers==2.2.2 \
    pymupdf \
    pytesseract \
    unstructured \
    psycopg2-binary==2.9.9 \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    pydantic==2.5.0 \
    python-multipart==0.0.6 \
    redis==5.0.1 \
    minio==7.2.7 \
    numpy==1.24.3 \
    PyPDF2==3.0.1 \
    python-docx==1.1.0 \
    huggingface-hub==0.19.4
# Copy application code
COPY . .

# Create runtime directories
RUN mkdir -p /data/uploads /data/documents /data/models

EXPOSE 8000

CMD ["python", "app.py"]