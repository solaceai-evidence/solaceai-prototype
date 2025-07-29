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

    def get_scores(
        self, query: str, passages: List[str], separator: str
    ) -> List[float]:
        sentence_pairs = [
            (query, passage.replace(separator, self.get_tokenizer().eos_token))
            for passage in passages
        ]
        scores = self.model.compute_score(sentence_pairs, normalize=True, batch_size=32)
        return [float(s) for s in scores]


class RemoteReranker(AbstractReranker):
    """
    Reranker that delegates scoring to a remote HTTP service.
    """

    def __init__(self, reranker_args: dict, **kwargs):
        self.url = reranker_args.get("url", "http://reranker-service:8001/rerank")
        self.kwargs = kwargs

    def get_scores(self, query: str, passages: List[str]) -> List[float]:
        logger.info(f"RemoteReranker: Sending {len(passages)} passages to {self.url}")
        resp = requests.post(self.url, json={"query": query, "passages": passages})
        resp.raise_for_status()
        scores = resp.json()["scores"]
        logger.info(
            f"RemoteReranker: Received {len(scores)} scores from remote service"
        )
        return scores

    def get_tokenizer(self):
        # Remote reranker does not expose a tokenizer
        return None


RERANKER_MAPPING = {
    "crossencoder": CrossEncoderScores,
    "biencoder": BiEncoderScores,
    "flag_embedding": FlagEmbeddingScores,
    "remote": RemoteReranker,
}
