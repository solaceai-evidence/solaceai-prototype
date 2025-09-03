# Tiltfile for Solace AI Hybrid Architecture
# Run: tilt up

# Load environment variables
load('ext://dotenv', 'dotenv')
dotenv()

# Configuration
reranker_port = os.getenv('RERANKER_PORT', '10001')
reranker_host = os.getenv('RERANKER_HOST', '0.0.0.0')

# Native Reranker Service
local_resource(
    'reranker-setup',
    '''
    mkdir -p api/logs
    # Try different Python environment setups
    if command -v conda >/dev/null 2>&1 && conda info --envs | grep -q solaceai; then
        echo "Using conda environment: solaceai"
        conda run -n solaceai pip install -r api/reranker_requirements.txt
        conda run -n solaceai pip install -e api/
    elif [ -f "venv/bin/activate" ]; then
        echo "Using virtual environment: venv"
        source venv/bin/activate && pip install -r api/reranker_requirements.txt && pip install -e api/
    elif [ -f ".venv/bin/activate" ]; then
        echo "Using virtual environment: .venv"
        source .venv/bin/activate && pip install -r api/reranker_requirements.txt && pip install -e api/
    else
        echo "Using system Python"
        pip install -r api/reranker_requirements.txt
        pip install -e api/
    fi
    ''',
    labels=['setup']
)

local_resource(
    'reranker-service',
    '''
    if command -v conda >/dev/null 2>&1 && conda info --envs | grep -q solaceai; then
        conda run -n solaceai env PYTHONPATH=api python reranker_service.py
    elif [ -f "venv/bin/activate" ]; then
        source venv/bin/activate && env PYTHONPATH=api python reranker_service.py
    elif [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate && env PYTHONPATH=api python reranker_service.py
    else
        env PYTHONPATH=api python reranker_service.py
    fi
    ''',
    serve_cmd='''
    if command -v conda >/dev/null 2>&1 && conda info --envs | grep -q solaceai; then
        conda run -n solaceai env PYTHONPATH=api python reranker_service.py
    elif [ -f "venv/bin/activate" ]; then
        source venv/bin/activate && env PYTHONPATH=api python reranker_service.py
    elif [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate && env PYTHONPATH=api python reranker_service.py
    else
        env PYTHONPATH=api python reranker_service.py
    fi
    ''',
    deps=['reranker_service.py', 'api/'],
    readiness_probe=probe(
        http_get=http_get_action(port=int(reranker_port), path='/ready')
    ),
    links=[
        link('http://{}:{}/health'.format(reranker_host, reranker_port), 'Reranker Health'),
        link('http://{}:{}/docs'.format(reranker_host, reranker_port), 'Reranker API Docs'),
    ],
    labels=['native'],
    resource_deps=['reranker-setup']
)

# Docker services
docker_compose('./docker-compose.yaml')

# Configure Docker Compose services with port forwards and links
dc_resource('proxy', 
    links=[
        link('http://localhost:8080', 'Web Application'),
    ],
    labels=['web']
)

# API Service  
dc_resource('api',
    links=[
        link('http://localhost:8000/docs', 'API Documentation'),
        link('http://localhost:8000/health', 'API Health'),
    ],
    labels=['api'],
    resource_deps=['reranker-service']
)

# UI Service (direct access)
dc_resource('ui',
    links=[
        link('http://localhost:4000', 'UI Direct Access'),
    ],
    labels=['ui']
)

print("""
🚀 Solace AI - Hybrid Architecture

Services:
• Web Application: http://localhost:8080 (Nginx Proxy - Main Entry Point)
• API: http://localhost:8000 (Dockerized API)
• UI Direct: http://localhost:4000 (Direct UI access)
• Reranker: http://{}:{} (Native GPU service)

Commands:
• tilt up    - Start all services
• tilt down  - Stop all services
• tilt logs  - View logs
""".format(reranker_host, reranker_port))
