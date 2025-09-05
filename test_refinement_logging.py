#!/usr/bin/env python3
"""
Test script for query refinement with verbose logging.
This script demonstrates the complete refinement flow with detailed logging.
"""

import sys
import os
import logging

# Add the API directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

from scholarqa.preprocess.query_refiner import run_query_refinement_step
from scholarqa.config.config_setup import read_json_config

def test_refinement_with_logging():
    """Test the refinement process with various queries to demonstrate logging."""

    # Set up configuration (this will set up logging)
    config_path = "api/run_configs/default.json"
    app_config = read_json_config(config_path)

    # Test cases with different levels of completeness
    test_cases = [
        {
            "name": "Complete Query",
            "query": "What are the effects of extreme heat on cardiovascular mortality in elderly populations in Mediterranean countries over the next decade?",
            "user_responses": None,
        },
        {
            "name": "Vague Query - Initial Analysis",
            "query": "Addressing substance misuse",
            "user_responses": None,
        },
        {
            "name": "Vague Query - Initial Analysis",
            "query": "Addressing substance misuse",
            "user_responses": {"setting": ["displaced communities"]},
        },
        {
            "name": "Vague Query - With Broad Response",
            "query": "How does climate change affect health?",
            "user_responses": {"setting": ["displaced communities"]},
        },
        {
            "name": "Vague Query - With Specific Response",
            "query": "How does climate change affect health?",
            "user_responses": {
                "setting": ["displaced communities", "Syrian refugees in Jordan"],
                "climate_factor": ["extreme heat"],
                "health_outcome": ["cardiovascular disease"],
            },
        },
    ]

    print("Starting Query Refinement Testing with Verbose Logging")
    print("=" * 80)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n\nTEST CASE {i}: {test_case['name']}")
        print("=" * 60)

        try:
            result, completions = run_query_refinement_step(
                query=test_case["query"],
                llm_model="anthropic/claude-3-5-sonnet-20241022",
                user_responses=test_case["user_responses"],
                max_tokens=512
            )

            print(f"\nRESULTS SUMMARY:")
            print(f"   Original: {result.original_query}")
            print(f"   Refined:  {result.refined_query}")
            print(f"   Needs Interaction: {result.needs_interaction}")
            print(f"   Status: {'COMPLETE' if not result.needs_interaction else 'NEEDS_CLARIFICATION'}")

            if result.interactive_steps:
                print(f"   Next Step: {result.interactive_steps[0].element_type}")

            total_cost = sum(c.cost for c in completions)
            print(f"   Cost: ${total_cost:.4f}")

        except Exception as e:
            print(f"Test case failed: {e}")
            logging.exception("Test case exception:")

        print("\n" + "=" * 60)
        input("Press Enter to continue to next test case...")

if __name__ == "__main__":
    test_refinement_with_logging()
