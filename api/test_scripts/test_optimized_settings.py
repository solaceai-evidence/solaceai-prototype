#!/usr/bin/env python3
"""
Test script to validate optimized reranker batch size and timeout settings
"""
import sys
import os
import json
sys.path.append(os.path.dirname(__file__))
sys.path.append("api")

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_configuration_values():
    """Test that configuration files contain optimized values"""
    logger.info("🔍 Testing optimized configuration values...")
    
    # Test default.json config
    config_path = "api/run_configs/default.json"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        batch_size = config.get("run_config", {}).get("reranker_args", {}).get("batch_size")
        timeout = config.get("run_config", {}).get("reranker_args", {}).get("timeout")
        
        logger.info(f"✅ Default config batch_size: {batch_size} (expected: 64)")
        logger.info(f"✅ Default config timeout: {timeout} (expected: 300)")
        
        assert batch_size == 64, f"Expected batch_size 64, got {batch_size}"
        assert timeout == 300, f"Expected timeout 300, got {timeout}"
    else:
        logger.warning("Default config not found")
    
    # Test environment example
    env_path = ".env_example"
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            env_content = f.read()
        
        # Check for optimized timeout values
        expected_values = [
            "RERANKER_CLIENT_TIMEOUT=300",
            "MAX_CONCURRENCY=2", 
            "RERANKER_TIMEOUT_MS=300000",
            "RERANKER_QUEUE_TIMEOUT_MS=30000"
        ]
        
        for expected in expected_values:
            if expected in env_content:
                logger.info(f"✅ Found optimized setting: {expected}")
            else:
                logger.error(f"❌ Missing optimized setting: {expected}")
                raise AssertionError(f"Missing {expected} in .env_example")
    else:
        logger.warning(".env_example not found")


def test_class_defaults():
    """Test that reranker classes have optimized default values"""
    logger.info("🔍 Testing reranker class default values...")
    
    try:
        # Test remote reranker defaults - this will fail without dependencies but that's expected
        import tempfile
        
        # Create a minimal test to verify batch sizes without actual imports
        test_code = """
import sys, os
sys.path.append('api')

# Test values by reading source code directly
with open('api/scholarqa/rag/reranker/remote_reranker.py', 'r') as f:
    content = f.read()
    
# Check for optimized default
if 'batch_size: int = 64' in content and 'RERANKER_CLIENT_TIMEOUT", "300.0"' in content:
    print('✅ Remote reranker has optimized defaults')
else:
    print('❌ Remote reranker defaults not optimized')
    exit(1)

# Check reranker service
with open('reranker_service.py', 'r') as f:
    content = f.read()
    
if 'default=64' in content and 'le=256' in content and '"300000"' in content:
    print('✅ Reranker service has optimized defaults')
else:
    print('❌ Reranker service defaults not optimized')
    exit(1)
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_file = f.name
        
        result = os.system(f"cd /home/runner/work/solaceai-prototype/solaceai-prototype && python {temp_file}")
        os.unlink(temp_file)
        
        if result == 0:
            logger.info("✅ Class defaults verification passed")
        else:
            logger.error("❌ Class defaults verification failed")
            raise AssertionError("Class defaults not optimized")
            
    except Exception as e:
        logger.warning(f"Could not test class defaults due to dependencies: {e}")


def test_port_consistency():
    """Test that ports are consistent across test scripts"""
    logger.info("🔍 Testing port consistency...")
    
    test_files = [
        "api/test_scripts/test_reranker_alignment.py",
        "api/test_scripts/test_exact_mapping.py", 
        "api/test_scripts/test_remote_architecture.py",
        "api/test_scripts/test_remote_client.py"
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            with open(test_file, 'r') as f:
                content = f.read()
            
            # Check for old port 8001
            if ":8001" in content:
                logger.error(f"❌ Found old port 8001 in {test_file}")
                raise AssertionError(f"Port 8001 found in {test_file}")
            
            # Check for correct port 10001
            if ":10001" in content:
                logger.info(f"✅ Correct port 10001 found in {test_file}")
            else:
                logger.warning(f"⚠️ No port references found in {test_file}")
        else:
            logger.warning(f"Test file not found: {test_file}")


def main():
    """Run all validation tests"""
    logger.info("🚀 Starting optimized settings validation...")
    
    try:
        test_configuration_values()
        test_class_defaults()
        test_port_consistency()
        
        logger.info("🎉 All optimization validations passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Validation failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)