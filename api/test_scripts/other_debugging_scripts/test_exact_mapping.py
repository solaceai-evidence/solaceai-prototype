#!/usr/bin/env python3
"""
Simple test to demonstrate 1-1 mapping between input passages and scores
"""
import os
import sys

sys.path.append(os.path.dirname(__file__))

import logging

from scholarqa.rag.reranker.reranker_base import RERANKER_MAPPING

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_exact_mapping():
    """Test exact index-to-score mapping with demonstration"""

    # Create test data with clear expected ordering
    query = "machine learning algorithms"
    passages = [
        "Neural networks are machine learning models",
        "Today is a beautiful sunny day",
        "Deep learning uses neural networks",
        "Cats are popular household pets",
        "Supervised learning trains on labeled data",
    ]

    logger.info("Testing Exact Index-to-Score Mapping")
    logger.info("=" * 50)
    logger.info(f"Query: '{query}'")
    logger.info(f"Number of passages: {len(passages)}")
    logger.info("")

    # Show input with indices
    logger.info("INPUT PASSAGES:")
    for i, passage in enumerate(passages):
        logger.info(f"   Index {i}: '{passage}'")
    logger.info("")

    # Test with crossencoder
    logger.info("Testing with CrossEncoder...")
    reranker = RERANKER_MAPPING["crossencoder"](
        model_name_or_path="mixedbread-ai/mxbai-rerank-large-v1"
    )

    scores = reranker.get_scores(query, passages)

    logger.info("OUTPUT SCORES (maintaining input order):")
    for i, (passage, score) in enumerate(zip(passages, scores)):
        relevance = "HIGH" if score > 0.5 else "LOW"
        logger.info(f"   Index {i}: {score:.4f} ({relevance}) - '{passage}'")
    logger.info("")

    # Verify exact mapping
    logger.info("VERIFICATION:")
    logger.info(f"   • Input length: {len(passages)}")
    logger.info(f"   • Output length: {len(scores)}")
    logger.info(f"   • Mapping preserved: {len(passages) == len(scores)}")
    logger.info("")

    # Show sorted by relevance for comparison
    logger.info("SORTED BY RELEVANCE (for reference):")
    sorted_pairs = sorted(
        enumerate(zip(passages, scores)), key=lambda x: x[1][1], reverse=True
    )
    for rank, (original_idx, (passage, score)) in enumerate(sorted_pairs, 1):
        logger.info(
            f"   Rank {rank}: Index {original_idx} - {score:.4f} - '{passage[:50]}...'"
        )
    logger.info("")

    # Test with remote reranker for consistency
    try:
        logger.info("Testing with Remote Reranker...")
        remote_reranker = RERANKER_MAPPING["remote"](
            service_url="http://localhost:8001",
            model_name_or_path="mixedbread-ai/mxbai-rerank-large-v1",
            reranker_type="crossencoder",
        )

        remote_scores = remote_reranker.get_scores(query, passages)

        logger.info("REMOTE vs LOCAL CONSISTENCY:")
        for i, (local_score, remote_score) in enumerate(zip(scores, remote_scores)):
            diff = abs(local_score - remote_score)
            status = "MATCH" if diff < 0.0001 else f" DIFF: {diff:.6f}"
            logger.info(
                f"   Index {i}: Local={local_score:.4f}, Remote={remote_score:.4f} - {status}"
            )

        # Check if scores are identical
        scores_identical = all(
            abs(a - b) < 0.0001 for a, b in zip(scores, remote_scores)
        )
        logger.info(
            f"   Overall consistency: {' IDENTICAL' if scores_identical else ' DIFFERENT'}"
        )

    except Exception as e:
        logger.warning(f" Remote reranker test failed: {e}")


if __name__ == "__main__":
    test_exact_mapping()
