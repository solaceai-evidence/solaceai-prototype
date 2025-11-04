import logging
from typing import Any, Dict, List, Tuple, Union

import modal

from solaceai.rag.reranker.reranker_base import RERANKER_MAPPING, AbstractReranker

logger = logging.getLogger(__name__)


class ModalReranker(AbstractReranker):
    def __init__(
        self,
        app_name: str,
        api_name: str,
        batch_size=32,
        gen_options: Dict[str, Any] = None,
    ):
        logger.info(f"using model {app_name} on Modal for reranking")
        self.modal_engine = ModalEngine(app_name, api_name, gen_options)
        self.batch_size = batch_size

    def get_scores(self, query: str, documents: List[str]):
        logger.info("Invoking the reranker deployed on Modal")
        return self.modal_engine.generate(
            (query, documents, self.batch_size), streaming=False
        )


RERANKER_MAPPING["modal"] = ModalReranker


class ModalEngine:
    def __init__(
        self, model_id: str, api_name: str, gen_options: Dict[str, Any] = None
    ) -> None:
        # Modal 1.2.1+ uses MODAL_TOKEN_ID and MODAL_TOKEN_SECRET from environment
        # These are automatically picked up by Modal's config system
        # No need to explicitly create a client - Modal handles it internally

        self.model_id = model_id
        self.api_name = api_name
        # Note: gen_options parameter is ignored for rerankers
        # Rerankers don't use LLM parameters like temperature, max_tokens, etc.

    def fn_lookup(self) -> modal.Function:
        # In Modal 1.2.1+, Function.from_name handles authentication internally
        fn = modal.Function.from_name(self.model_id, self.api_name)
        return fn

    def generate(
        self, input_args: Tuple, streaming=False, **opt_kwargs
    ) -> Union[str, List[Dict]]:
        gen_fn = self.fn_lookup()

        # For reranker: only pass positional args (query, passages, batch_size)
        # The Modal reranker uses default values for its optional parameters
        if streaming:
            outputs = []
            for chunk in gen_fn.remote_gen(*input_args):
                outputs.append(chunk)
            return (
                "".join(outputs) if outputs and isinstance(outputs[0], str) else outputs
            )
        else:
            # Just pass the three required positional arguments
            return gen_fn.remote(*input_args)
