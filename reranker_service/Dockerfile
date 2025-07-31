FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the high-performance reranker service
COPY reranker.py .

# Expose port
EXPOSE 8002

# Environment variables
ENV PYTHONPATH=/app
ENV PORT=8002

# Health check with longer startup time for model loading
HEALTHCHECK --interval=30s --timeout=15s --start-period=180s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Run the high-performance reranker
CMD ["python", "reranker.py"]
