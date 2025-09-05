#!/usr/bin/env python3
"""
Test script for the query refinement API endpoint with verbose logging.
This script tests the API endpoint to ensure proper logging integration.
"""

import requests
import json
import time


def test_api_endpoint():
    """Test the query refinement API endpoint."""

    base_url = "http://localhost:8000"
    endpoint = f"{base_url}/api/query_refinement"

    # Test cases
    test_cases = [
        {
            "name": "Initial Analysis - Vague Query",
            "payload": {
                "query": "How does climate change affect displaced communities?",
                "opt_in": True,
                "user_id": "test_user_123",
            },
        },
        {
            "name": "With Broad User Response",
            "payload": {
                "query": "How does climate change affect displaced communities?",
                "opt_in": True,
                "user_id": "test_user_123",
                "user_responses": {"setting": ["displaced communities"]},
            },
        },
        {
            "name": "With Specific User Response",
            "payload": {
                "query": "How does climate change affect displaced communities?",
                "opt_in": True,
                "user_id": "test_user_123",
                "user_responses": {
                    "setting": ["displaced communities", "Syrian refugees in Jordan"],
                    "climate_factor": ["extreme heat"],
                    "health_outcome": ["cardiovascular disease"],
                    "temporal_scope": ["immediate effects"],
                },
            },
        },
    ]

    print("🌐 Testing Query Refinement API Endpoint")
    print("=" * 60)
    print(f"Base URL: {base_url}")
    print(f"Endpoint: {endpoint}")
    print("=" * 60)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\nAPI TEST {i}: {test_case['name']}")
        print("-" * 40)

        try:
            print(f"📤 Sending request...")
            print(f"   Payload: {json.dumps(test_case['payload'], indent=2)}")

            response = requests.post(
                endpoint,
                json=test_case["payload"],
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            print(f"Response Status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"Success!")
                print(f"   Status: {result.get('status', 'unknown')}")
                print(
                    f"   Needs Interaction: {result.get('needs_interaction', 'unknown')}"
                )

                if result.get("element_type"):
                    print(f"   Next Element: {result['element_type']}")
                    print(f"   Is Suggestion: {result.get('is_suggestion', False)}")

                if result.get("clarification_question"):
                    print(f"   Question: {result['clarification_question'][:100]}...")

                if result.get("refined_query") != result.get("original_query"):
                    print(f"   Refined Query: {result['refined_query']}")

            else:
                print(f"Error: {response.status_code}")
                print(f"   Response: {response.text}")

        except requests.exceptions.ConnectionError:
            print(f"Connection Error: Could not connect to {base_url}")
            print("   Make sure the API server is running with:")
            print("   cd /Users/w1214757/Dev/solaceai-prototype && ./start_hybrid.sh")
            break
        except Exception as e:
            print(f"Request failed: {e}")

        print("-" * 40)
        if i < len(test_cases):
            time.sleep(1)  # Brief pause between requests

    print("\nAPI testing complete")


if __name__ == "__main__":
    test_api_endpoint()
