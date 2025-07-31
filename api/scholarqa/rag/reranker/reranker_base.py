from abc import ABC, abstractmethod
from typing import List, Dict, Any
import requests

import logging

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn.functional as F
except ImportError:
    logger.warning("torch not found, custom baseline rerankers will not work.")


class AbstractReranker(ABC):
    @abstractmethod
    def get_scores(self, query: str, documents: List[str]) -> List[float]:
        pass


class SentenceTransformerEncoder:
    def __init__(self, model_name_or_path: str):
        from sentence_transformers import SentenceTransformer

        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(
            model_name_or_path, revision=None, device=device
        )

    def encode(self, sentences: List[str]):
        return self.model.encode(
            sentences, show_progress_bar=True, convert_to_tensor=True
        )

    def get_tokenizer(self):
        return self.model.tokenizer


# GIST embeddings model supported by Sentence transformer
# https://huggingface.co/avsolatorio/GIST-large-Embedding-v0
class BiEncoderScores(AbstractReranker):
    def __init__(self, model_name_or_path: str):
        self.model = SentenceTransformerEncoder(model_name_or_path)

    def get_scores(self, query: str, passages: List[str]) -> List[float]:
        query_embedding = self.model.encode([query])[0]
        passage_embeddings = self.model.encode(passages)
        scores = (
            F.cosine_similarity(query_embedding.unsqueeze(0), passage_embeddings)
            .cpu()
            .numpy()
        )
        return [float(s) for s in scores]


# Sentence Transformer supports Jina AI (https://huggingface.co/jinaai/jina-reranker-v2-base-multilingual)
# and Mix Bread re-rankers (https://huggingface.co/mixedbread-ai/mxbai-rerank-large-v1)
class CrossEncoderScores(AbstractReranker):
    def __init__(self, model_name_or_path: str):
        from sentence_transformers import CrossEncoder

        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(device)
        self.model = CrossEncoder(
            model_name_or_path,
            automodel_args={"torch_dtype": "float16"},
            trust_remote_code=True,
            device=device,
        )

    def get_tokenizer(self):
        return self.model.tokenizer

    def get_scores(self, query: str, passages: List[str]) -> List[float]:
        sentence_pairs = [[query, passage] for passage in passages]
        scores = self.model.predict(
            sentence_pairs,
            convert_to_tensor=True,
            show_progress_bar=True,
            batch_size=128,
        ).tolist()
        return [float(s) for s in scores]


# Supports the BAAI/bge... models https://huggingface.co/BAAI/bge-reranker-v2-m3
class FlagEmbeddingScores:
    def __init__(self, model_name_or_path: str):
        from FlagEmbedding import FlagReranker

        self.model = FlagReranker(model_name_or_path, use_fp16=True)

    def get_tokenizer(self):
        return self.model.tokenizer

    def get_scores(self, query: str, passages: List[str]) -> List[float]:
        # No separator handling needed - FlagReranker handles raw text properly
        sentence_pairs = [(query, passage) for passage in passages]
        scores = self.model.compute_score(sentence_pairs, normalize=True, batch_size=32)
        return [float(s) for s in scores]


class RemoteReranker(AbstractReranker):
    """
    Reranker that delegates scoring to a remote HTTP service.
    Uses environment variables for service discovery.
    Supports fallback to local model if specified.
    """

    def __init__(self, **reranker_args):
        import os

        # Extract parameters from reranker_args (matches other rerankers in this file)
        service_name = reranker_args.get("service_name", "reranker-service")
        self.batch_size = reranker_args.get("batch_size", 32)

        # Optional fallback to local model
        self.fallback_model_path = reranker_args.get("fallback_model_path", None)
        self.fallback_reranker = None

        # Build URL from environment variables and service name
        port = os.getenv("RERANKER_SERVICE_PORT", "8001")
        endpoint = "/rerank"  # Fixed endpoint

        # Map service names to container names
        service_mapping = {
            "reranker-service": "reranker_service",
            # Future: "modal": "modal_service"
        }

        container_name = service_mapping.get(service_name, service_name)
        self.url = f"http://{container_name}:{port}{endpoint}"

        logger.info(
            f"RemoteReranker initialized: {self.url} (batch_size: {self.batch_size})"
        )

        if self.fallback_model_path:
            logger.info(f"Fallback model configured: {self.fallback_model_path}")

    def _get_fallback_reranker(self):
        """Lazy load fallback reranker only when needed"""
        if self.fallback_reranker is None and self.fallback_model_path:
            logger.warning("Loading fallback CrossEncoder model...")
            self.fallback_reranker = CrossEncoderScores(self.fallback_model_path)
        return self.fallback_reranker

    def get_scores(self, query: str, passages: List[str]) -> List[float]:
        logger.info(f"RemoteReranker: Sending {len(passages)} passages to {self.url}")

        try:
            resp = requests.post(
                self.url,
                json={
                    "query": query,
                    "passages": passages,
                    "batch_size": self.batch_size,
                },
                timeout=30,  # Add timeout for robustness
            )
            resp.raise_for_status()
            scores = resp.json()["scores"]
            logger.info(
                f"RemoteReranker: Received {len(scores)} scores from remote service"
            )
            return scores

        except (requests.RequestException, requests.HTTPError) as e:
            logger.warning(f"Remote reranker failed: {e}")

            # Try fallback if configured
            fallback = self._get_fallback_reranker()
            if fallback:
                logger.info("Using fallback local reranker")
                return fallback.get_scores(query, passages)
            else:
                logger.error("No fallback configured, re-raising exception")
                raise

    def get_tokenizer(self):
        # Remote reranker does not expose a tokenizer
        return None


RERANKER_MAPPING = {
    "crossencoder": CrossEncoderScores,
    "biencoder": BiEncoderScores,
    "flag_embedding": FlagEmbeddingScores,
    "remote": RemoteReranker,
}
