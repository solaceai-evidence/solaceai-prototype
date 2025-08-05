#!/bin/bash
# 
# Startup script for Solace AI with Remote GPU Reranker Architecture
#

# stop at first error
set -e

echo "Solace AI - Hybrid Architecture Startup"
echo "═══════════════════════════════════════════"

# Configuration
export RERANKER_PORT=$(grep '^RERANKER_PORT=' .env | cut -d '=' -f2-)
MAIN_API_PORT=8000
CONFIG_FILE="api/run_configs/default.json"

# Cleanup function
cleanup_and_exit() {
    echo ""
    echo " Cleaning up..."
    kill $RERANKER_PID 2>/dev/null || true
    docker-compose down 2>/dev/null || true
    exit $1
}

echo " Configuration:"
echo "   • Reranker Service: http://0.0.0.0:$RERANKER_PORT (Native Reranker Service)"
echo "   • Main API: http://localhost:$MAIN_API_PORT (Dockerized API)"
echo "   • Config: $CONFIG_FILE"
echo ""

# Step 1
echo "Starting Native GPU Reranker Service..."
if lsof -Pi :$RERANKER_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "   Port $RERANKER_PORT already in use - stopping existing service"
    pkill -f "reranker_service.py" || true
    sleep 2
fi

echo "   Launching reranker service ..."
nohup env PYTHONPATH=api python reranker_service.py > api/logs/reranker_service.log 2>&1 &
RERANKER_PID=$!

# Wait for service to start
echo "   Waiting for reranker service to initialize..."
for i in {1..10}; do
    if curl -s http://0.0.0.0:$RERANKER_PORT/health > /dev/null 2>&1; then
        echo "   Reranker service ready!"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "   Reranker service failed to start"
        exit 1
    fi
    sleep 2
done

# Step 2
echo ""
echo "Step 2: Starting Main API with Docker..."
echo "   📄 Using config: $CONFIG_FILE"

# Make sure we have the config
if [ ! -f "$CONFIG_FILE" ]; then
    echo "   Config file not found: $CONFIG_FILE"
    exit 1
fi

# Start main services with docker-compose
echo "   Starting Docker services..."
docker-compose up --build

# Wait for main API
echo "   Waiting for main API..."
for i in {1..15}; do
    if curl -s http://localhost:$MAIN_API_PORT/health > /dev/null 2>&1; then
        echo "   Main API ready!"
        break
    fi
    if [ $i -eq 15 ]; then
        echo "   Main API failed to start"
        cleanup_and_exit 1
    fi
    sleep 3
done

# Step 3
echo ""
echo " Step 3: Testing Integration..."

# Test reranker service 
echo "   Testing health of reranker service..."
HEALTH_RESPONSE=$(curl -s http://0.0.0.0:$RERANKER_PORT/health || echo "Failed")
echo "   Response: $HEALTH_RESPONSE"

# Test main API 
echo "   Testing main API..."
MAIN_HEALTH=$(curl -s http://localhost:$MAIN_API_PORT/health || echo "Failed")
echo "   Response: $MAIN_HEALTH"

# Step 4: Show status and next steps
echo ""
echo " Startup Complete!"
echo "═══════════════════════"
echo ""
echo " Service Status:"
echo "   • Native Reranker: http://0.0.0.0:$RERANKER_PORT/health"
echo "     - Process ID: $RERANKER_PID"
echo "     - Logs: api/logs/reranker_service.log"
echo ""
echo "   • Main API: http://localhost:$MAIN_API_PORT"
echo ""
echo " Management Commands:"
echo "   • Stop reranker: kill $RERANKER_PID"
echo ""
echo " The architecture is running!"

# Trap signals for cleanup
trap 'cleanup_and_exit 0' SIGINT SIGTERM

# Keep script running or optionally wait for user input
echo ""
echo "Press Ctrl+C to stop all services..."
wait $RERANKER_PID
