FROM python:3.10.14-slim-bullseye

WORKDIR /app

# Update system packages to address vulnerabilities
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY reranker_service.py .

CMD ["uvicorn", "reranker_service:app", "--host", "0.0.0.0", "--port", "8001"]