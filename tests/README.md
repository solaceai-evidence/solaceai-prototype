# Test Scripts for SolaceAI Prototype

This folder contains various test scripts that were created during development and performance optimization of the reranker system.

## Test Files

### Performance and Integration Tests
- `test_consolidated_reranker.py` - Tests the main reranker service performance (now just `reranker.py`)
- `test_large_batch.py` - Tests reranker performance with large document batches
- `quick_batch_test.py` - Quick performance test for reranker service
- `simple_test.py` - Basic reranker functionality test

### API and System Tests  
- `test_api_key.py` - Verifies API key loading and functionality
- `test_end_to_end.py` - Full system integration test with climate emergency query
- `test_integration.py` - Integration test from the original reranker service

### Compatibility Tests
- `test_tokenizer_compatibility.py` - Tests tokenizer compatibility across implementations

## Usage

Most tests can be run directly:
```bash
python tests/test_api_key.py
python tests/quick_batch_test.py
```

## Performance History

These tests were instrumental in discovering that the ONNX implementation was achieving only 0.1 docs/sec (100x slower than expected), leading to the consolidation into a single CrossEncoder-based reranker achieving 15x+ performance improvement.

## Note

With the reranker consolidation complete, most of these tests serve as reference and backup. The main reranker service is now optimized and working at expected performance levels.
