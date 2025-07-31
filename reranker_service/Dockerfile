FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements_simple.txt .
RUN pip install --no-cache-dir -r requirements_simple.txt

# Copy application code
COPY simple_onnx_service.py .
COPY convert_simple.py .

# Convert model on first run (downloads from HuggingFace)
RUN python3 convert_simple.py || echo "Model conversion will happen at runtime"

# Expose port
EXPOSE 8002

# Environment variables
ENV PYTHONPATH=/app
ENV PORT=8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Run the application
CMD ["python", "simple_onnx_service.py"]
