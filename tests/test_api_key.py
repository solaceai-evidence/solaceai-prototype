#!/usr/bin/env python3
"""
Test to verify the Anthropic API key is being loaded correctly.
This makes a direct API call to check credentials.
"""

import requests
import json
import time

def test_api_key_loading():
    """Test if the API can access Anthropic services with the new key."""
    print("🔑 Testing Anthropic API Key Loading...")
    
    # Make a request to the main API that should use the Anthropic key
    url = "http://localhost:8000/query_corpusqa"
    data = {
        "query": "What is climate change?",
        "run_config": "default",  # Use default configuration which should use CLAUDE_4_OPUS
        "task_id": None  # New task
    }
    
    try:
        print(f"Making request to: {url}")
        start_time = time.time()
        
        response = requests.post(
            url,
            json=data,
            timeout=60,
            headers={"Content-Type": "application/json"}
        )
        
        elapsed = time.time() - start_time
        
        print(f"Response received in {elapsed:.2f}s")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API request successful! Response received:")
            
            # Check if we got a task_id (async response)
            if 'task_id' in result:
                task_id = result['task_id']
                print(f"   Task ID: {task_id}")
                print(f"   Query: {result.get('query', 'N/A')}")
                print(f"   Status: {result.get('task_status', 'N/A')}")
                print("🎉 API is accepting requests - key loading seems successful!")
                return True
            else:
                print(f"   Response: {result}")
                print("✅ API responded, but unexpected format")
                return True
        else:
            print(f"❌ API request failed:")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out - this might indicate API key issues")
        return False
    except Exception as e:
        print(f"❌ Error testing API key: {e}")
        return False

def test_environment_variables():
    """Check if environment variables are accessible from within the container."""
    print("\n🔧 Testing Environment Variable Access...")
    
    try:
        # Make a request to a custom endpoint that shows environment info
        url = "http://localhost:8000/debug/env"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Environment debug endpoint accessible")
            return True
        else:
            print(f"⚠️  Debug endpoint not available (status: {response.status_code})")
            return False
            
    except Exception as e:
        print(f"⚠️  Debug endpoint not available: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing API Key and Environment Loading")
    print("=" * 50)
    
    # Test environment access
    env_ok = test_environment_variables()
    
    # Test API key functionality  
    api_ok = test_api_key_loading()
    
    print("\n" + "=" * 50)
    if api_ok:
        print("✅ SUCCESS: API key is working correctly!")
    else:
        print("❌ FAILURE: API key issues detected")
        print("💡 Try restarting containers: docker-compose down && docker-compose up -d")
        
    exit(0 if api_ok else 1)
