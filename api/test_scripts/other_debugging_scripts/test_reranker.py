#!/usr/bin/env python3
"""
Simple test script to verify reranker initialization with MPS support
"""
import os
import sys

sys.path.append(os.getcwd())

from solaceai.rag.reranker.reranker_base import CrossEncoderScores


def test_reranker():
    print("Testing CrossEncoder reranker initialization...")

    # Initialize the reranker (this should trigger MPS device detection)
    reranker = CrossEncoderScores("mixedbread-ai/mxbai-rerank-large-v1")

    print("Reranker initialized successfully!")

    # Test a simple scoring operation
    query = "cholera outbreak management"
    passages = [
        "Cholera is a waterborne disease that spreads during floods",
        "Ethiopia has experienced several cholera outbreaks",
        "Machine learning algorithms can predict weather patterns",
    ]

    print(f"\nTesting reranker with query: '{query}'")
    print("Passages to rank:")
    for i, passage in enumerate(passages, 1):
        print(f"  {i}. {passage}")

    # Get scores
    scores = reranker.get_scores(query, passages)

    print(f"\nReranker scores: {scores}")

    # Show ranked results
    ranked_passages = sorted(zip(passages, scores), key=lambda x: x[1], reverse=True)
    print("\nRanked passages (highest score first):")
    for i, (passage, score) in enumerate(ranked_passages, 1):
        print(f"  {i}. Score: {score:.4f} - {passage}")


if __name__ == "__main__":
    test_reranker()
