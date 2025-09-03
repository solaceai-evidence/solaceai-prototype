# Makefile for Solace AI System
.PHONY: help setup start stop restart logs clean health test

# Default target
help: ## Show this help message
	@echo "Solace AI - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "URLs:"
	@echo "  Web App: http://localhost:8080"
	@echo "  API:     http://localhost:8000"
	@echo "  UI:      http://localhost:4000"

# Detect docker compose command
DOCKER_COMPOSE := $(shell if command -v docker-compose >/dev/null 2>&1; then echo "docker-compose"; elif docker compose version >/dev/null 2>&1; then echo "docker compose"; else echo ""; fi)

# Python environment detection
PYTHON_ENV_CMD := $(shell \
	if command -v conda >/dev/null 2>&1 && conda info --envs | grep -q solaceai; then \
		echo "conda run -n solaceai"; \
	elif [ -f "venv/bin/activate" ]; then \
		echo "source venv/bin/activate &&"; \
	elif [ -f ".venv/bin/activate" ]; then \
		echo "source .venv/bin/activate &&"; \
	else \
		echo ""; \
	fi \
)

PYTHON_ENV_NAME := $(shell \
	if command -v conda >/dev/null 2>&1 && conda info --envs | grep -q solaceai; then \
		echo "conda (solaceai)"; \
	elif [ -f "venv/bin/activate" ]; then \
		echo "venv"; \
	elif [ -f ".venv/bin/activate" ]; then \
		echo ".venv"; \
	else \
		echo "system"; \
	fi \
)

# Environment setup
setup: ## Initial setup - copy .env.example to .env
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ Created .env file from .env.example"; \
		echo "📝 Please edit .env with your API keys"; \
	else \
		echo "✅ .env file already exists"; \
	fi
	@mkdir -p api/logs
	@echo "✅ Created api/logs directory"
	@echo "🐍 Detected Python environment: $(PYTHON_ENV_NAME)"
	@echo "📦 Installing dependencies..."
	@$(PYTHON_ENV_CMD) pip install -r api/reranker_requirements.txt > /dev/null 2>&1 || \
		echo "⚠️  Failed to install reranker requirements. You may need to set up a Python environment."
	@$(PYTHON_ENV_CMD) pip install -e api/ > /dev/null 2>&1 || \
		echo "⚠️  Failed to install API package. You may need to set up a Python environment."

setup-python: ## Set up Python virtual environment
	@echo "🐍 Setting up Python virtual environment..."
	@if command -v conda >/dev/null 2>&1; then \
		echo "📦 Creating conda environment 'solaceai'..."; \
		conda create -n solaceai python=3.11 -y; \
		conda run -n solaceai pip install torch torchvision torchaudio; \
		echo "✅ Conda environment 'solaceai' created"; \
		echo "💡 To activate: conda activate solaceai"; \
	elif command -v python3 >/dev/null 2>&1; then \
		echo "📦 Creating virtual environment 'venv'..."; \
		python3 -m venv venv; \
		source venv/bin/activate && pip install --upgrade pip; \
		source venv/bin/activate && pip install torch torchvision torchaudio; \
		echo "✅ Virtual environment 'venv' created"; \
		echo "💡 To activate: source venv/bin/activate"; \
	else \
		echo "❌ Neither conda nor python3 found. Please install Python 3.11+"; \
		exit 1; \
	fi
	@echo ""
	@echo "🎯 Next steps:"
	@echo "  1. Edit .env with your API keys"
	@echo "  2. Run: make start"

# Start services
start: setup ## Start all services (hybrid architecture)
	@echo "🚀 Starting Solace AI Hybrid Architecture..."
	@$(MAKE) start-reranker
	@sleep 5
	@$(MAKE) start-docker
	@echo ""
	@echo "✅ All services started!"
	@$(MAKE) status

start-reranker: ## Start native reranker service
	@echo "🔧 Starting native reranker service..."
	@echo "🐍 Using Python environment: $(PYTHON_ENV_NAME)"
	@pkill -f "reranker_service.py" || true
	@sleep 2
	@echo "📦 Installing dependencies..."
	@$(PYTHON_ENV_CMD) pip install -r api/reranker_requirements.txt > /dev/null 2>&1
	@$(PYTHON_ENV_CMD) pip install -e api/ > /dev/null 2>&1
	@nohup $(PYTHON_ENV_CMD) env PYTHONPATH=api python reranker_service.py > api/logs/reranker_service.log 2>&1 &
	@echo "⏳ Waiting for reranker to be ready..."
	@for i in $$(seq 1 15); do \
		if curl -sf http://localhost:10001/ready >/dev/null 2>&1; then \
			echo "✅ Reranker service ready!"; \
			break; \
		fi; \
		if [ $$i -eq 15 ]; then \
			echo "❌ Reranker failed to start"; \
			tail -n 50 api/logs/reranker_service.log; \
			exit 1; \
		fi; \
		sleep 2; \
	done

start-docker: ## Start Docker services
	@echo "🐳 Starting Docker services..."
	@$(DOCKER_COMPOSE) up -d --build
	@echo "⏳ Waiting for API to be ready..."
	@for i in $$(seq 1 20); do \
		if curl -sf http://localhost:8000/health >/dev/null 2>&1; then \
			echo "✅ API service ready!"; \
			break; \
		fi; \
		if [ $$i -eq 20 ]; then \
			echo "❌ API failed to start"; \
			$(DOCKER_COMPOSE) logs --tail=50; \
			exit 1; \
		fi; \
		sleep 3; \
	done

# Stop services  
stop: ## Stop all services
	@echo "🛑 Stopping all services..."
	@pkill -f "reranker_service.py" || true
	@$(DOCKER_COMPOSE) down
	@echo "✅ All services stopped"

# Restart services
restart: stop start ## Restart all services

# View logs
logs: ## View logs from all services
	@echo "📋 Recent reranker logs:"
	@tail -n 20 api/logs/reranker_service.log || echo "No reranker logs found"
	@echo ""
	@echo "📋 Docker service logs:"
	@$(DOCKER_COMPOSE) logs --tail=20

logs-reranker: ## View reranker logs
	@tail -f api/logs/reranker_service.log

logs-docker: ## View Docker service logs
	@$(DOCKER_COMPOSE) logs -f

# Health checks
health: ## Check health of all services
	@echo "🔍 Service Health Check:"
	@echo ""
	@echo "Reranker Service:"
	@curl -s http://localhost:10001/health || echo "❌ Reranker not responding"
	@echo ""
	@echo "API Service:"
	@curl -s http://localhost:8000/health || echo "❌ API not responding"
	@echo ""
	@echo "Web Application:"
	@curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost:8080 || echo "❌ Web app not responding"

status: ## Show service status and URLs
	@echo ""
	@echo "🌐 Service URLs:"
	@echo "  • Web Application: http://localhost:8080 (Main Entry Point)"
	@echo "  • API Documentation: http://localhost:8000/docs"
	@echo "  • Reranker Health: http://localhost:10001/health" 
	@echo "  • UI Direct: http://localhost:4000"
	@echo ""
	@echo "📋 Management:"
	@echo "  • Logs: make logs"
	@echo "  • Health: make health"
	@echo "  • Stop: make stop"

# Development helpers
dev: start ## Start in development mode (alias for start)

test: ## Run basic connectivity tests
	@echo "🧪 Running connectivity tests..."
	@curl -f http://localhost:8080 >/dev/null && echo "✅ Web app accessible"
	@curl -f http://localhost:8000/health >/dev/null && echo "✅ API healthy"
	@curl -f http://localhost:10001/health >/dev/null && echo "✅ Reranker healthy"

# Cleanup
clean: stop ## Stop services and clean up
	@echo "🧹 Cleaning up..."
	@$(DOCKER_COMPOSE) down -v --remove-orphans
	@docker system prune -f
	@echo "✅ Cleanup complete"

# Environment check
check-env: ## Check if required environment variables are set
	@echo "🔍 Checking environment configuration..."
	@if [ ! -f .env ]; then echo "❌ .env file missing"; exit 1; fi
	@if [ -z "$$(grep '^S2_API_KEY=' .env | cut -d'=' -f2)" ]; then echo "⚠️ S2_API_KEY not set"; fi
	@if [ -z "$$(grep '^ANTHROPIC_API_KEY=' .env | cut -d'=' -f2)" ]; then echo "⚠️ ANTHROPIC_API_KEY not set"; fi
	@if [ -z "$$(grep '^OPENAI_API_KEY=' .env | cut -d'=' -f2)" ]; then echo "⚠️ OPENAI_API_KEY not set"; fi
	@echo "✅ Environment check complete"
