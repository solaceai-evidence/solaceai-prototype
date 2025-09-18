import json
import logging
import re
from collections import namedtuple
from multiprocessing import Queue
from typing import List, Optional, Tuple, Union

from litellm import moderation
from pydantic import BaseModel, Field

from scholarqa.llms.constants import CompletionResult
from scholarqa.llms.litellm_helper import llm_completion_with_rate_limiting
from scholarqa.llms.prompts import QUERY_DECOMPOSER_PROMPT

logger = logging.getLogger(__name__)

LLMProcessedQuery = namedtuple(
    "LLMProcessedQuery", ["rewritten_query", "keyword_query", "search_filters"]
)


class DecomposedQuery(BaseModel):
    earliest_search_year: str = Field(
        description="The earliest year to search for papers"
    )
    latest_search_year: str = Field(description="The latest year to search for papers")
    venues: str = Field(
        description="Comma separated list of venues to search for papers"
    )
    authors: Union[List[str] | str] = Field(
        description="List of authors to search for papers", default=[]
    )
    field_of_study: str = Field(
        description="Comma separated list of field of study to search for papers"
    )
    rewritten_query: str = Field(description="The rewritten simplified query")
    rewritten_query_for_keyword_search: str = Field(
        description="The rewritten query for keyword search"
    )


def moderation_api(text: str) -> bool:
    response = moderation(text, model="omni-moderation-latest")
    return response.results[0].flagged


def validate(query: str) -> None:
    # self.update_task_state(task_id, "Validating the query")
    logger.info("Checking query for malicious content with moderation api...")
    try:
        if moderation_api(query):
            raise Exception("The input query contains harmful content.")
    except Exception as e:
        logger.error(f"Query validation failed, {e}")
        raise e
    logger.info(f"{query} is valid")


def decompose_query(
    query: str, decomposer_llm_model: str, **llm_kwargs
) -> Tuple[LLMProcessedQuery, CompletionResult]:
    search_filters = dict()
    decomp_query_res = None
    try:
        # decompose query to get llm re-written and keyword query with filters
        decomp_query_res = llm_completion_with_rate_limiting(
            user_prompt=query,
            system_prompt=QUERY_DECOMPOSER_PROMPT,
            model=decomposer_llm_model,
            response_format=DecomposedQuery,
            **llm_kwargs,
        )
        decomposed_query = json.loads(decomp_query_res.content)
        decomposed_query = {
            k: str(v) if type(v) == int else v for k, v in decomposed_query.items()
        }
        decomposed_query = DecomposedQuery(**decomposed_query)
        logger.info(f"Decomposed query: {decomposed_query}")
        rewritten_query, keyword_query = (
            decomposed_query.rewritten_query,
            decomposed_query.rewritten_query_for_keyword_search,
        )
        if decomposed_query.earliest_search_year or decomposed_query.latest_search_year:
            search_filters["year"] = (
                f"{decomposed_query.earliest_search_year}-{decomposed_query.latest_search_year}"
            )
        if decomposed_query.venues:
            search_filters["venue"] = decomposed_query.venues
        if decomposed_query.field_of_study:
            search_filters["fieldsOfStudy"] = decomposed_query.field_of_study
        if decomposed_query.authors:
            # Handle both list and string formats for authors
            if isinstance(decomposed_query.authors, list):
                search_filters["authors"] = ",".join(decomposed_query.authors)
            else:
                search_filters["authors"] = decomposed_query.authors
    except Exception as e:
        logger.error(f"Error while decomposing query: {e}")
        rewritten_query = query
        keyword_query = ""
        decomp_query_res = CompletionResult(
            content="",
            model=f"error-{decomposer_llm_model}",
            cost=0.0,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            reasoning_tokens=0,
        )

    return (
        LLMProcessedQuery(
            rewritten_query=rewritten_query,
            keyword_query=keyword_query,
            search_filters=search_filters,
        ),
        decomp_query_res,
    )
