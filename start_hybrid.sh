#!/bin/bash
# 
# Startup script for Solace AI with Remote GPU Reranker Architecture
#

# stop at first error
set -e

# Ensure common binary paths are in PATH (for Docker, Homebrew, etc.)
# Only add directories that exist and aren't already in PATH
for dir in /usr/local/bin /opt/homebrew/bin /usr/bin /bin /usr/sbin /sbin; do
    if [ -d "$dir" ] && [[ ":$PATH:" != *":$dir:"* ]]; then
        export PATH="$dir:$PATH"
    fi
done

echo "Solace AI - Hybrid Architecture Startup"
echo "═══════════════════════════════════════════"

# Python Environment Setup
setup_python_environment() {
    echo "Checking Python environment..."
    
    if command -v conda >/dev/null 2>&1; then
        # Conda is available - use conda environment
        if conda env list | grep -q "solaceai"; then
            echo "    Found conda environment 'solaceai'"
        else
            echo "    Creating conda environment 'solaceai'..."
            conda create -n solaceai python=3.11 -y
            echo "    Conda environment 'solaceai' created"
        fi
        
        # Activate conda environment
        echo "    Activating conda environment 'solaceai'..."
        export CONDA_ENV_ACTIVATED=true
        export PYTHON_CMD="conda run -n solaceai python"
        export PIP_CMD="conda run -n solaceai pip"
        
    elif command -v python3 >/dev/null 2>&1; then
        # No conda - use venv
        if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
            echo "    Found virtual environment 'venv'"
        else
            echo "    Creating virtual environment 'venv'..."
            python3 -m venv venv
            echo "    Virtual environment 'venv' created"
        fi
        
        # Activate venv environment
        echo "    Activating virtual environment 'venv'..."
        source venv/bin/activate
        export PYTHON_CMD="python"
        export PIP_CMD="pip"
        
    else
        echo "    Neither conda nor python3 found. Please install Python 3.11+"
        echo "    Install options:"
        echo "      - Anaconda/Miniconda: https://docs.conda.io/en/latest/miniconda.html"
        echo "      - Python: https://www.python.org/downloads/"
        exit 1
    fi
}

# Install dependencies in the environment
install_dependencies() {
    local reranker_mode=$1
    
    if [ "$reranker_mode" = "modal" ]; then
        echo "Installing Modal AI dependencies..."
        
        # Install Modal SDK
        echo "   Installing Modal SDK..."
        $PIP_CMD install modal > /dev/null 2>&1 || {
            echo "     Failed to install Modal SDK"
            echo "    You may need to install manually: $PIP_CMD install modal"
        }
        
        # Install API package (needed for Modal integration)
        if [ -f "api/pyproject.toml" ]; then
            echo "   Installing API package..."
            $PIP_CMD install -e api/ > /dev/null 2>&1 || {
                echo "     Failed to install API package"
                echo "    You may need to install manually: $PIP_CMD install -e api/"
            }
        fi
        
        echo "    Modal AI dependencies installed"
        echo "    Note: Reranking will run on Modal's cloud GPU"
    else
        echo "Installing dependencies for native reranker (not via docker)..."
        
        # Install PyTorch first (required for GPU acceleration)
        echo "   Installing PyTorch..."
        if [[ "$CONDA_ENV_ACTIVATED" == "true" ]]; then
            # Use conda for PyTorch installation when using conda environment
            conda run -n solaceai pip install torch torchvision torchaudio > /dev/null 2>&1 || {
                echo "     Failed to install PyTorch via conda"
            }
        else
            # Use pip for PyTorch installation when using venv
            $PIP_CMD install torch torchvision torchaudio > /dev/null 2>&1 || {
                echo "     Failed to install PyTorch via pip"
            }
        fi
        
        # Install reranker requirements (needed for native GPU reranker service)
        if [ -f "api/reranker_requirements.txt" ]; then
            echo "   Installing reranker requirements..."
            $PIP_CMD install -r api/reranker_requirements.txt > /dev/null 2>&1 || {
                echo "     Failed to install reranker requirements"
                echo "    You may need to install manually: $PIP_CMD install -r api/reranker_requirements.txt"
            }
        fi
        
        # Install API package (needed for reranker imports: from api.solaceai.rag.reranker...)
        if [ -f "api/pyproject.toml" ]; then
            echo "   Installing API package..."
            $PIP_CMD install -e api/ > /dev/null 2>&1 || {
                echo "     Failed to install API package"
                echo "    You may need to install manually: $PIP_CMD install -e api/"
            }
        fi
        
        echo "    Native reranker dependencies installed"
        echo "    Note: Dockerized API has its own copy of dependencies"
    fi
}

# Early check of reranker configuration (before installing dependencies)
CONFIG_FILE="api/run_configs/default.json"
if [ -f "$CONFIG_FILE" ]; then
    RERANKER_SERVICE_EARLY=$(jq -r '.run_config.reranker_service // "remote"' "$CONFIG_FILE")
else
    RERANKER_SERVICE_EARLY="remote"
fi

# Setup Python environment
setup_python_environment
install_dependencies "$RERANKER_SERVICE_EARLY"

# Detect docker compose command
detect_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    elif docker compose version &> /dev/null; then
        echo "docker compose"
    else
        echo "ERROR: Neither 'docker-compose' nor 'docker compose' is available" >&2
        echo "Please install Docker Compose: https://docs.docker.com/compose/install/" >&2
        exit 1
    fi
}

DOCKER_COMPOSE_CMD=$(detect_docker_compose)
echo "Using Docker Compose command: $DOCKER_COMPOSE_CMD"
echo ""

# Configuration
export RERANKER_PORT=$(grep '^RERANKER_PORT=' .env | cut -d '=' -f2- || echo "")
export RERANKER_HOST=$(grep '^RERANKER_HOST=' .env | cut -d '=' -f2- || echo "")
if [ -z "$RERANKER_PORT" ]; then
    RERANKER_PORT=10001
fi
if [ -z "$RERANKER_HOST" ]; then
    RERANKER_HOST="0.0.0.0"
fi
MAIN_API_PORT=8000
CONFIG_FILE="api/run_configs/default.json"

# Check reranker service configuration
if [ -f "$CONFIG_FILE" ]; then
    RERANKER_SERVICE=$(jq -r '.run_config.reranker_service // "remote"' "$CONFIG_FILE")
    echo "Detected reranker service: $RERANKER_SERVICE"
else
    echo "Warning: Config file not found at $CONFIG_FILE, defaulting to 'remote' reranker"
    RERANKER_SERVICE="remote"
fi

# Cleanup function
cleanup_and_exit() {
        echo ""
        echo " Cleaning up..."

        # Gracefully stop reranker
        if [ -n "$RERANKER_PID" ] && ps -p $RERANKER_PID > /dev/null 2>&1; then
            echo "   Stopping reranker (PID=$RERANKER_PID)"
            kill $RERANKER_PID 2>/dev/null || true
            # wait up to 10s
            for i in {1..10}; do
                if ps -p $RERANKER_PID > /dev/null 2>&1; then
                    sleep 1
                else
                    break
                fi
            done
            if ps -p $RERANKER_PID > /dev/null 2>&1; then
                echo "   Reranker didn't exit, force killing"
                kill -9 $RERANKER_PID 2>/dev/null || true
            fi
        fi

        # Stop docker services
        echo "   Stopping Docker services"
        $DOCKER_COMPOSE_CMD down 2>/dev/null || true
        exit $1
}

echo " Configuration:"
echo "   • Python Environment: $(echo $PYTHON_CMD | sed 's/.*conda.*/conda (solaceai)/' | sed 's/.*venv.*/venv/' | sed 's/.*\.venv.*/.venv/')"
echo "   • Web Application: http://localhost:8080 (Nginx Proxy)"
if [ "$RERANKER_SERVICE" = "modal" ]; then
    echo "   • Reranker Service: Modal AI (Cloud GPU)"
else
    echo "   • Reranker Service: http://$RERANKER_HOST:$RERANKER_PORT (Native Reranker Service)"
fi
echo "   • Main API: http://localhost:$MAIN_API_PORT (Dockerized API)"
echo "   • Config: $CONFIG_FILE"
echo ""

# Step 1: Start Reranker (conditionally based on configuration)
if [ "$RERANKER_SERVICE" = "modal" ]; then
    echo "Step 1: Using Modal AI for Reranking..."
    echo "   Reranker configured to use Modal AI cloud service"
    echo "   Skipping local reranker startup"
    echo "   Verifying Modal deployment..."
    
    # Check if Modal CLI is available and app is deployed
    if command -v modal >/dev/null 2>&1 || $PYTHON_CMD -m modal --version >/dev/null 2>&1; then
        # Extract app_name from config
        MODAL_APP_NAME=$(jq -r '.run_config.reranker_args.app_name // "solaceai-reranker"' "$CONFIG_FILE")
        echo "   Checking Modal app: $MODAL_APP_NAME"
        
        # Try to check if app exists (this will work if authenticated)
        if $PYTHON_CMD -m modal app list 2>/dev/null | grep -q "$MODAL_APP_NAME" || true; then
            echo "   ✓ Modal app '$MODAL_APP_NAME' found or Modal is accessible"
        else
            echo "   Note: Could not verify Modal app (this is okay if you're authenticated)"
        fi
    else
        echo "   Warning: Modal CLI not found. Make sure Modal is installed and configured."
        echo "   Install: pip install modal"
        echo "   Authenticate: modal token new"
    fi
    
    RERANKER_PID=""  # No local process
else
    echo "Step 1: Starting Native GPU Reranker Service..."
    if lsof -Pi :$RERANKER_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "   Port $RERANKER_PORT already in use - stopping existing service"
        pkill -f "reranker_service.py" || true
        sleep 2
    fi

    echo "   Launching reranker service ..."
    # Ensure logs directory exists
    mkdir -p api/logs
    nohup env PYTHONPATH=api $PYTHON_CMD reranker_service.py > api/logs/reranker_service.log 2>&1 &
    RERANKER_PID=$!

    # Wait for service to start
    echo "   Waiting for reranker service to initialize..."
    for i in {1..15}; do
        if curl -sf http://$RERANKER_HOST:$RERANKER_PORT/ready > /dev/null 2>&1; then
            echo "   Reranker service ready!"
            break
        fi
        if [ $i -eq 15 ]; then
            echo "   Reranker service failed to start"
            echo "   Last 100 lines of reranker log:"
            tail -n 100 api/logs/reranker_service.log || true
            exit 1
        fi
        sleep 2
    done
fi

# Step 2
echo ""
echo "Step 2: Starting Main API with Docker..."
echo "    Using config: $CONFIG_FILE"

# Make sure we have the config
if [ ! -f "$CONFIG_FILE" ]; then
    echo "   Config file not found: $CONFIG_FILE"
    exit 1
fi

# Start main services with docker-compose
echo "   Starting Docker services..."
$DOCKER_COMPOSE_CMD up -d --build

# Wait for main API
echo "   Waiting for main API..."
for i in {1..20}; do
    if curl -sf http://localhost:$MAIN_API_PORT/health > /dev/null 2>&1; then
        echo "   Main API ready!"
        break
    fi
    if [ $i -eq 20 ]; then
        echo "   Main API failed to start"
        echo "   Docker service logs (last 200 lines):"
        $DOCKER_COMPOSE_CMD logs --no-color --tail=200 || true
        cleanup_and_exit 1
    fi
    sleep 3
done

# Step 3
echo ""
echo " Step 3: Testing Integration..."

# Test reranker service (only if running locally)
if [ "$RERANKER_SERVICE" != "modal" ]; then
    echo "   Testing health of local reranker service..."
    HEALTH_RESPONSE=$(curl -s http://0.0.0.0:$RERANKER_PORT/health || echo "Failed")
    echo "   Response: $HEALTH_RESPONSE"
else
    echo "   Skipping local reranker health check (using Modal AI)"
fi

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
echo "   • Python Environment: $(echo $PYTHON_CMD | sed 's/.*conda.*/conda (solaceai)/' | sed 's/.*venv.*/venv/' | sed 's/.*\.venv.*/.venv/')"
echo "   • Web Application: http://localhost:8080"
if [ "$RERANKER_SERVICE" = "modal" ]; then
    echo "   • Reranker: Modal AI (Cloud GPU)"
    MODAL_APP_NAME=$(jq -r '.run_config.reranker_args.app_name // "solaceai-reranker"' "$CONFIG_FILE")
    echo "     - App Name: $MODAL_APP_NAME"
    echo "     - View logs: python3 -m modal app logs $MODAL_APP_NAME"
else
    echo "   • Native Reranker: http://$RERANKER_HOST:$RERANKER_PORT/health"
    echo "     - Process ID: $RERANKER_PID"
    echo "     - Logs: api/logs/reranker_service.log"
fi
echo ""
echo "   • Main API: http://localhost:$MAIN_API_PORT"
echo ""
echo " Management Commands:"
if [ "$RERANKER_SERVICE" != "modal" ] && [ -n "$RERANKER_PID" ]; then
    echo "   • Stop reranker: kill $RERANKER_PID"
fi
echo "   • Stop all services: press Ctrl+C in this terminal"
echo ""
echo " The architecture is running!"

# Trap signals for cleanup
trap 'cleanup_and_exit 0' SIGINT SIGTERM

# Keep script running or optionally wait for user input
echo ""
echo "Press Ctrl+C to stop all services..."

# Wait appropriately based on reranker type
if [ "$RERANKER_SERVICE" = "modal" ]; then
    # No local reranker process to wait for, just wait indefinitely
    while true; do
        sleep 3600  # Sleep for 1 hour at a time
    done
else
    # Wait for the local reranker process
    wait $RERANKER_PID
fi
