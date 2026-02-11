FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /data/models /data/documents /data/data /data/docs

# Set PYTHONPATH to include the current directory
ENV PYTHONPATH=/app

EXPOSE 8000

# Run directly
CMD ["python", "app.py"]
