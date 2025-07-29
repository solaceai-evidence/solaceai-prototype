# RemoteReranker Microservice

## Build and Push

docker build -t <your-dockerhub-username>/reranker-service:latest .
docker push <your-dockerhub-username>/reranker-service:latest

## Deploy to Kubernetes

kubectl apply -f deployment.yaml

## Local Test

docker run -p 8001:8001 reranker-service:latest
curl -X POST http://localhost:8001/rerank -H "Content-Type: application/json" -d '{"query": "test", "passages": ["a", "b"]}'
