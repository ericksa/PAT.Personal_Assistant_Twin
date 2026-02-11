FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code with new src structure
COPY src/ /app/src/

# Set PYTHONPATH to include the src directory
ENV PYTHONPATH=/app:$PYTHONPATH

EXPOSE 8007

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application using module import
CMD ["python", "-m", "src.main"]