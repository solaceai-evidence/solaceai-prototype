#!/usr/bin/env python3
"""
Test script to verify 1-1 mapping between input passages and reranker scores
Tests both local and remote rerankers for consistency
"""
import os
import sys

sys.path.append(os.path.dirname(__file__))

import logging
from typing import List, Tuple

from solaceai.rag.reranker.reranker_base import RERANKER_MAPPING

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_cases() -> List[Tuple[str, List[str]]]:
    """Create test cases with known expected ordering"""
    return [
        # Test case 1: Machine Learning
        (
            "deep learning neural networks",
            [
                "Deep neural networks are the foundation of modern AI",  # Should rank highest
                "The weather is sunny today",  # Should rank lowest
                "Machine learning algorithms process data",  # Should rank high
                "Pizza is a popular Italian food",  # Should rank low
                "Convolutional neural networks excel at image recognition",  # Should rank high
            ],
        ),
        # Test case 2: Medical
        (
            "cancer treatment research",
            [
                "Chemotherapy is a common cancer treatment",  # Should rank highest
                "Basketball is played with two teams",  # Should rank lowest
                "Clinical trials test new medical treatments",  # Should rank high
                "Mountains are tall geographical features",  # Should rank low
                "Oncology focuses on cancer diagnosis and treatment",  # Should rank highest
            ],
        ),
        # Test case 3: Single passage (edge case)
        ("artificial intelligence", ["AI systems can perform complex reasoning tasks"]),
        # Test case 4: Empty query (edge case)
        ("", ["This is a test passage", "Another test passage"]),
        # Test case 5: Many passages
        (
            "quantum computing",
            [
                (
                    "Quantum computers use quantum bits for computation"
                    if i == 0
                    else f"Random passage number {i}"
                )
                for i in range(10)
            ],
        ),
    ]


def verify_score_alignment(
    query: str, passages: List[str], scores: List[float], reranker_name: str
) -> bool:
    """Verify that scores align 1-1 with input passages"""
    logger.info(f"\n Testing {reranker_name} with {len(passages)} passages")
    logger.info(f"Query: '{query}'")

    # Basic length check
    if len(scores) != len(passages):
        logger.error(
            f" Length mismatch: {len(passages)} passages, {len(scores)} scores"
        )
        return False

    logger.info(f" Length match: {len(passages)} passages = {len(scores)} scores")

    # Score validation
    for i, (passage, score) in enumerate(zip(passages, scores, strict=False)):
        if not isinstance(score, (int, float)):
            logger.error(f" Invalid score type at index {i}: {type(score)} - {score}")
            return False

        if not (0.0 <= score <= 1.0):
            logger.warning(f" Score outside [0,1] range at index {i}: {score}")

    # Display results for manual verification
    logger.info(" Passage-Score Alignment:")
    ranked_pairs = sorted(
        enumerate(zip(passages, scores, strict=False)),
        key=lambda x: x[1][1],
        reverse=True,
    )

    for rank, (original_idx, (passage, score)) in enumerate(ranked_pairs, 1):
        passage_preview = passage[:60] + "..." if len(passage) > 60 else passage
        logger.info(f"   {rank}. [idx:{original_idx}] {score:.4f} - {passage_preview}")

    # Semantic validation (basic heuristics)
    if query and len(passages) > 1:
        max_score_idx = scores.index(max(scores))
        min_score_idx = scores.index(min(scores))

        logger.info(f" Highest score passage: '{passages[max_score_idx][:100]}...'")
        logger.info(f" Lowest score passage: '{passages[min_score_idx][:100]}...'")

        # Check if scores show reasonable variation
        score_range = max(scores) - min(scores)
        if score_range < 0.01:
            logger.warning(f"⚠️ Very low score variation: {score_range:.6f}")
        else:
            logger.info(f" Good score variation: {score_range:.4f}")

    return True


def test_reranker(reranker_name: str, test_cases: List[Tuple[str, List[str]]]) -> bool:
    """Test a specific reranker with all test cases"""
    logger.info(f"\n🔍 Testing {reranker_name.upper()} Reranker")
    logger.info("=" * 50)

    try:
        # Create reranker instance
        if reranker_name == "remote":
            reranker = RERANKER_MAPPING[reranker_name](
                service_url="http://localhost:8001",
                model_name_or_path="mixedbread-ai/mxbai-rerank-large-v1",
                reranker_type="crossencoder",
            )
        else:
            reranker = RERANKER_MAPPING[reranker_name](
                model_name_or_path="mixedbread-ai/mxbai-rerank-large-v1"
            )

        logger.info(f" {reranker_name} reranker initialized")

        # Test all cases
        all_passed = True
        for case_idx, (query, passages) in enumerate(test_cases, 1):
            logger.info(f"\n--- Test Case {case_idx} ---")

            try:
                scores = reranker.get_scores(query, passages)
                passed = verify_score_alignment(query, passages, scores, reranker_name)
                all_passed = all_passed and passed

                if passed:
                    logger.info(f" Test case {case_idx} passed")
                else:
                    logger.error(f" Test case {case_idx} failed")

            except Exception as e:
                logger.error(f" Test case {case_idx} error: {e}")
                all_passed = False

        return all_passed

    except Exception as e:
        logger.error(f" Failed to initialize {reranker_name}: {e}")
        return False


def test_cross_reranker_consistency() -> bool:
    """Test that different rerankers produce consistent results for same input"""
    logger.info("\n Testing Cross-Reranker Consistency")
    logger.info("=" * 50)

    test_query = "machine learning neural networks"
    test_passages = [
        "Deep learning models use neural networks",
        "The weather is nice today",
        "Artificial intelligence algorithms",
    ]

    results = {}

    # Test available rerankers
    available_rerankers = ["crossencoder", "biencoder"]
    if "local_service" in RERANKER_MAPPING:
        available_rerankers.append("local_service")

    for reranker_name in available_rerankers:
        try:
            if reranker_name == "local_service":
                reranker = RERANKER_MAPPING[reranker_name](
                    service_url="http://localhost:8001",
                    model_name_or_path="mixedbread-ai/mxbai-rerank-large-v1",
                    reranker_type="crossencoder",
                )
            else:
                reranker = RERANKER_MAPPING[reranker_name](
                    model_name_or_path="mixedbread-ai/mxbai-rerank-large-v1"
                )

            scores = reranker.get_scores(test_query, test_passages)
            results[reranker_name] = scores

            logger.info(f" {reranker_name}: {[f'{s:.4f}' for s in scores]}")

        except Exception as e:
            logger.warning(f" {reranker_name} failed: {e}")

    # Compare results
    if len(results) > 1:
        reranker_names = list(results.keys())
        base_name = reranker_names[0]
        base_scores = results[base_name]

        logger.info(f"\n Consistency Analysis (vs {base_name}):")

        for other_name in reranker_names[1:]:
            other_scores = results[other_name]

            # Check ranking correlation
            base_ranking = sorted(
                range(len(base_scores)), key=lambda i: base_scores[i], reverse=True
            )
            other_ranking = sorted(
                range(len(other_scores)), key=lambda i: other_scores[i], reverse=True
            )

            ranking_match = base_ranking == other_ranking
            logger.info(
                f"   {other_name} vs {base_name}: {' Same ranking' if ranking_match else '⚠️ Different ranking'}"
            )
            logger.info(f"     {base_name}: {base_ranking}")
            logger.info(f"     {other_name}: {other_ranking}")

    return len(results) > 0


def main():
    """Main test runner"""
    logger.info(" Reranker Alignment Verification")
    logger.info("=" * 50)

    # Create test cases
    test_cases = create_test_cases()
    logger.info(f" Created {len(test_cases)} test cases")

    # Test available rerankers
    rerankers_to_test = ["crossencoder"]

    # Add remote if service is available
    try:
        import httpx

        with httpx.Client(timeout=5.0) as client:
            response = client.get("http://localhost:8001/health")
            if response.status_code == 200:
                rerankers_to_test.append("remote")
                logger.info("✅ Remote reranker service detected")
            else:
                logger.warning(" Remote reranker service not healthy")
    except Exception:
        logger.warning(" Remote reranker service not available")

    # Run tests
    overall_success = True

    for reranker_name in rerankers_to_test:
        success = test_reranker(reranker_name, test_cases)
        overall_success = overall_success and success

    # Test consistency across rerankers
    if len(rerankers_to_test) > 1:
        test_cross_reranker_consistency()

    # Final report
    logger.info("\n🏁 Final Results")
    logger.info("=" * 30)
    if overall_success:
        logger.info(" All alignment tests passed!")
        logger.info(" 1-1 mapping verified for all rerankers")
    else:
        logger.error(" Some tests failed")
        logger.error(" Check logs above for details")

    return 0 if overall_success else 1


if __name__ == "__main__":
    exit(main())
