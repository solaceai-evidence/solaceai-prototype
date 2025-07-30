# ScholarQA Configuration Files

This directory contains various configuration files for different reranker setups.

## Configuration Files

### `default.json` (Recommended)

- **Reranker**: Remote HTTP microservice
- **Benefits**: Scalable, production-ready, Docker/K8s compatible
- **Model**: `mixedbread-ai/mxbai-rerank-large-v1` (loaded in remote service)
- **Use Case**: Production deployments, high performance requirements

### `remote_with_fallback.json` (High Availability)

- **Reranker**: Remote HTTP microservice with local fallback
- **Benefits**: Service resilience, automatic failover
- **Model**: Remote service + local `mixedbread-ai/mxbai-rerank-large-v1` fallback
- **Use Case**: Mission-critical deployments, high availability requirements

### `crossencoder.json`

- **Reranker**: Local CrossEncoder (SentenceTransformers)
- **Model**: `mixedbread-ai/mxbai-rerank-large-v1` (loaded locally)
- **Use Case**: Development, single-machine deployments, GPU-enabled environments

### `biencoder.json`

- **Reranker**: Local BiEncoder (SentenceTransformers)
- **Model**: `avsolatorio/GIST-large-Embedding-v0` (loaded locally)
- **Use Case**: Faster inference, lower memory usage, CPU-friendly

### `flag_embedding.json`

- **Reranker**: Local FlagEmbedding reranker
- **Model**: `BAAI/bge-reranker-v2-m3` (loaded locally)
- **Use Case**: Multilingual reranking, BAAI model ecosystem

## Usage

### Switch Configuration

```bash
# Use remote reranker (default)
export CONFIG_PATH="run_configs/default.json"

# Use local crossencoder
export CONFIG_PATH="run_configs/crossencoder.json"

# Use local biencoder
export CONFIG_PATH="run_configs/biencoder.json"

# Use flag embedding
export CONFIG_PATH="run_configs/flag_embedding.json"
```

### Docker Compose

For remote reranker only (default configuration):

```bash
docker-compose up
```

For local rerankers, you don't need the separate reranker service:

```bash
docker-compose up api ui proxy
```

## Architecture Comparison

### Remote Reranker (default.json)

```
[API Service] --HTTP--> [Reranker Service]
- Scalable microservices
- GPU isolation
- Service discovery
- Load balancing ready
```

### Local Rerankers (crossencoder.json, biencoder.json, flag_embedding.json)

```
[API Service with embedded reranker]
- Single process
- Direct model access
- Lower latency
- Simpler deployment
```

## Model Information

| Reranker        | Model                                 | Size  | Performance | Use Case          |
| --------------- | ------------------------------------- | ----- | ----------- | ----------------- |
| Remote          | `mixedbread-ai/mxbai-rerank-large-v1` | ~7B   | Highest     | Production        |
| Remote+Fallback | Remote + Local fallback               | ~7B   | Highest     | High Availability |
| CrossEncoder    | `mixedbread-ai/mxbai-rerank-large-v1` | ~7B   | Highest     | Development       |
| BiEncoder       | `avsolatorio/GIST-large-Embedding-v0` | ~335M | Fast        | CPU inference     |
| FlagEmbedding   | `BAAI/bge-reranker-v2-m3`             | ~2.3B | High        | Multilingual      |

## Configuration Validation

The enhanced `config_setup.py` now includes:

- **Validation**: Automatic validation of reranker configurations
- **Helpful Warnings**: Missing optional parameters are logged as warnings
- **Error Detection**: Required parameters are validated at startup
- **Configuration Examples**: Built-in examples for all reranker types

### Test Your Configuration

```bash
cd api
python test_config.py
```

This will validate all configuration files and show usage examples.

### Programmatic Access

```python
from scholarqa.config.config_setup import read_json_config, RunConfig

# Load and validate config
config = read_json_config('run_configs/default.json')

# Check configuration type
print(f"Using {config.get_reranker_type()} reranker")
print(f"Is remote: {config.is_remote_reranker()}")
print(f"Has fallback: {config.has_fallback_reranker()}")

# Get example configurations
examples = RunConfig.get_reranker_config_examples()
print(examples['crossencoder'])
```

## Migration Path

1. **Development**: Start with `crossencoder.json` for simplicity
2. **Testing**: Use `default.json` to test microservice architecture
3. **Production**: Deploy with `default.json` + Docker Compose
4. **High Availability**: Use `remote_with_fallback.json` for mission-critical deployments
5. **Optimization**: Switch between models based on performance needs
