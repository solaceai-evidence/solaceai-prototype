#!/usr/bin/env python3
"""
Test script for the new query refinement pipeline step.
Verifies that the step works correctly and produces compatible output.
"""
import os
import sys
import json
from pathlib import Path

# Add the API directory to the path
api_dir = Path(__file__).parent.parent
sys.path.insert(0, str(api_dir))

from scholarqa.preprocess.query_refiner import run_query_refinement_step


def test_query_refinement_basic():
    """Test basic query refinement functionality."""
    print("Testing basic query refinement...")
    
    # Test with a vague query
    vague_query = "Does X help with health outcomes?"
    
    # Use a model (this would need to be configured in your environment)
    model = "gpt-3.5-turbo"
    
    try:
        result, completions = run_query_refinement_step(
            query=vague_query,
            llm_model=model,
            max_tokens=512
        )
        
        print(f"Original query: {result.original_query}")
        print(f"Refined query: {result.refined_query}")
        print(f"Needs clarification: {result.needs_clarification}")
        print(f"Setting clear: {result.analysis.setting_clear}")
        print(f"Question complete: {result.analysis.question_complete}")
        print(f"Missing element: {result.analysis.missing_element}")
        print(f"Clarification suggestion: {result.analysis.clarification_suggestion}")
        print(f"Number of LLM calls: {len(completions)}")
        
        # Verify output structure
        assert hasattr(result, 'original_query')
        assert hasattr(result, 'refined_query')
        assert hasattr(result, 'analysis')
        assert hasattr(result, 'needs_clarification')
        assert isinstance(completions, list)
        
        print("✓ Basic test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Basic test failed: {e}")
        return False


def test_query_refinement_with_context():
    """Test query refinement with conversation context."""
    print("\nTesting query refinement with context...")
    
    query = "What's the effect of meditation?"
    context = "The user mentioned they're interested in cardiovascular health outcomes in elderly populations."
    
    model = "gpt-3.5-turbo"
    
    try:
        result, completions = run_query_refinement_step(
            query=query,
            llm_model=model,
            conversation_context=context,
            max_tokens=512
        )
        
        print(f"Original query: {result.original_query}")
        print(f"Refined query: {result.refined_query}")
        print(f"Context was provided: {context is not None}")
        print(f"Query was modified: {result.original_query != result.refined_query}")
        
        # When context is provided, the query should potentially be refined
        assert result.original_query == query
        print("✓ Context test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Context test failed: {e}")
        return False


def test_pipeline_compatibility():
    """Test that the output is compatible with pipeline expectations."""
    print("\nTesting pipeline compatibility...")
    
    query = "Does exercise help?"
    model = "gpt-3.5-turbo"
    
    try:
        result, completions = run_query_refinement_step(
            query=query,
            llm_model=model,
            max_tokens=256
        )
        
        # Test JSON serialization (important for pipeline state management)
        result_dict = result.model_dump()
        json_str = json.dumps(result_dict)
        reconstructed = json.loads(json_str)
        
        print(f"Result serializes to JSON: {len(json_str)} chars")
        print(f"Completions returned: {len(completions)} items")
        
        # Verify cost tracking compatibility
        for completion in completions:
            assert hasattr(completion, 'input_tokens')
            assert hasattr(completion, 'output_tokens')
            assert hasattr(completion, 'cost')
        
        print("✓ Pipeline compatibility test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Pipeline compatibility test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Query Refinement Pipeline Step Tests")
    print("=" * 60)
    
    # Check if we have the necessary environment
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  Warning: No API keys found in environment.")
        print("   Set OPENAI_API_KEY or ANTHROPIC_API_KEY to run live tests.")
        print("   Running structure tests only...")
        
        # Just test the imports and structure
        try:
            from scholarqa.preprocess.query_refiner import (
                QueryRefinementAnalysis,
                QueryRefinementResult,
                run_query_refinement_step
            )
            print("✓ All imports successful")
            print("✓ Structure test passed!")
            return
        except Exception as e:
            print(f"✗ Structure test failed: {e}")
            return
    
    tests = [
        test_query_refinement_basic,
        test_query_refinement_with_context,
        test_pipeline_compatibility
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n{passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Query refinement step is ready for pipeline integration.")
    else:
        print("⚠️  Some tests failed. Please check the output above.")


if __name__ == "__main__":
    main()
