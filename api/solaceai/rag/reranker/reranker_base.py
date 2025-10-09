import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

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

        if torch.cuda.is_available():
            device = "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"
        logger.info(
            f"Initializing SentenceTransformerEncoder model: {model_name_or_path} on device: {device}"
        )
        self.model = SentenceTransformer(
            model_name_or_path, revision=None, device=device
        )
        self.device = device

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
        logger.info(f"Initializing BiEncoder model: {model_name_or_path}")
        self.model = SentenceTransformerEncoder(model_name_or_path)
        self.device = self.model.device

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
    def __init__(self, model_name_or_path: str, batch_size: int = 128):
        from sentence_transformers import CrossEncoder

        if torch.cuda.is_available():
            device = "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"
        logger.info(
            f"Initializing CrossEncoder model: {model_name_or_path} on device: {device}"
        )
        self.model = CrossEncoder(
            model_name_or_path,
            automodel_args={"torch_dtype": "float16"} if device != "mps" else {},
            trust_remote_code=True,
            device=device,
        )
        self.device = device
        self.batch_size = batch_size
        logger.info(f"CrossEncoder batch_size set to: {batch_size}")

    def get_tokenizer(self):
        return self.model.tokenizer

    def get_scores(self, query: str, passages: List[str]) -> List[float]:
        sentence_pairs = [[query, passage] for passage in passages]
        scores = self.model.predict(
            sentence_pairs,
            convert_to_tensor=True,
            show_progress_bar=True,
            batch_size=self.batch_size,
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


RERANKER_MAPPING = {
    "crossencoder": CrossEncoderScores,
    "biencoder": BiEncoderScores,
    "flag_embedding": FlagEmbeddingScores,
}

# Import and add remote reranker - conditional import to avoid dependency issues in Docker
try:
    from .remote_reranker import RemoteRerankerClient

    RERANKER_MAPPING["remote"] = RemoteRerankerClient
except ImportError as e:
    logger.warning(f"Remote reranker client not available: {e}")
    # Remote reranker requires httpx which might not be in minimal Docker images
