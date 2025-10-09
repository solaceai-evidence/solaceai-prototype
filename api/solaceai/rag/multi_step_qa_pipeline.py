import json
import logging
import os
import re
from enum import Enum
from typing import Any, Dict, Generator, List, Tuple

import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from solaceai.llms.constants import CompletionResult, GPT_4o
from solaceai.llms.litellm_helper import (
    batch_llm_completion_with_rate_limiting,
    llm_completion_with_rate_limiting,
)
from solaceai.llms.prompts import (
    PROMPT_ASSEMBLE_NO_QUOTES_SUMMARY,
    USER_PROMPT_PAPER_LIST_FORMAT,
    USER_PROMPT_QUOTE_LIST_FORMAT,
)

# Load environment variables at the top of the file
load_dotenv()


logger = logging.getLogger(__name__)


class DimFormat(str, Enum):
    """Output format for organizing extracted evidence: synthesis (narrative) or list (bullet points)."""
    SYNTHESIS = "synthesis"
    LIST = "list"


class Dimension(BaseModel):
    """Represents a thematic section in the final answer with associated evidence quotes."""
    name: str = Field(default=None, description=("The name of the dimension"))
    format: DimFormat = Field(
        default=None,
        description=(
            "The generation format of the dimension - can be either list of synthesis"
        ),
    )
    quotes: List[int] = Field(
        default=None,
        description=(
            "A list of indices of paper quotes in the dimension, can be empty if no relevant quotes are found"
        ),
    )


class ClusterPlan(BaseModel):
    """LLM-generated plan for organizing evidence into thematic sections with reasoning."""
    cot: str = Field(
        default=None,
        description=("The justification for every dimension name and its format"),
    )
    dimensions: List[Dimension] = Field(
        default=None,
        description=(
            "The list of dimensions along with the associated quote indices as per the cot plan"
        ),
    )


class MultiStepQAPipeline:
    """Orchestrates the evidence extraction, clustering, and section generation pipeline stages."""
    def __init__(
        self,
        llm_model: str,
        fallback_llm: str = GPT_4o,
        batch_workers: int = int(os.getenv("MAX_LLM_WORKERS", "20")),
        **llm_kwargs,
    ):
        """Initialize pipeline with LLM configuration and parallelization settings."""
        self.llm_model = llm_model
        self.fallback_llm = fallback_llm
        self.batch_workers = batch_workers
        max_output_tokens = int(os.getenv("RATE_LIMIT_OTPM", (4096 * 4)))
        self.llm_kwargs = {"max_tokens": max_output_tokens}
        if llm_kwargs:
            self.llm_kwargs.update(llm_kwargs)
        logger.info(
            f"Pipeline initialized: {self.batch_workers} workers, "
            f"max_tokens_per_request={max_output_tokens}"
        )

    def step_select_quotes(
        self, query: str, scored_df: pd.DataFrame, sys_prompt: str
    ) -> Tuple[Dict[str, str], List[CompletionResult]]:
        """Stage 3: Extract relevant evidence quotes from each paper using LLM in parallel."""

        logger.info(
            f"Querying {self.llm_model} to extract quotes from these papers with {self.batch_workers} parallel workers"
        )
        tup_items = {
            k: v
            for k, v in zip(
                scored_df["reference_string"],
                scored_df["relevance_judgment_input_expanded"],
            )
        }
        messages = [
            USER_PROMPT_PAPER_LIST_FORMAT.format(query, v) for k, v in tup_items.items()
        ]
        completion_results = batch_llm_completion_with_rate_limiting(
            self.llm_model,
            messages=messages,
            system_prompt=sys_prompt,
            max_workers=self.batch_workers,
            fallback=self.fallback_llm,
            **self.llm_kwargs,
        )
        quotes = [
            (
                cr.content
                if cr.content != "None"
                and not cr.content.startswith("None\n")
                and not cr.content.startswith("None ")
                else ""
            )
            for cr in completion_results
        ]
        per_paper_summaries = {
            t[0]: quote
            for t, quote in zip(tup_items.items(), quotes)
            if len(quote) > 10
        }
        per_paper_summaries = dict(
            sorted(per_paper_summaries.items(), key=lambda x: x[0])
        )
        return per_paper_summaries, completion_results

    def step_clustering(
        self, query: str, per_paper_summaries: Dict[str, str], sys_prompt: str
    ) -> Tuple[Dict[str, Any], CompletionResult]:
        """Stage 4: Organize extracted quotes into thematic dimensions using LLM reasoning."""
        def make_prompt(query: str, paper_paper_quotes_dict: Dict[str, str]) -> str:
            """Format quotes with indices for LLM clustering input."""
            # paper_paper_quotes_dict is a dictionary with keys being the paper titles and values being the quotes
            # need to make a single string with all of the quotes
            quotes = ""
            for idx, (paper, quotes_str) in enumerate(paper_paper_quotes_dict.items()):
                # there are multiple quotes per paper
                quotes_str = quotes_str.replace("\n", "")
                quotes += f"[{idx}]\t{quotes_str}" + "\n"
            prompt = USER_PROMPT_QUOTE_LIST_FORMAT.format(query, quotes)
            return prompt

        user_prompt = make_prompt(query, per_paper_summaries)
        try:
            # params for reasoning mode: max_completion_tokens=4096, max_tokens=4096+1024, reasoning_effort="low"
            response = llm_completion_with_rate_limiting(
                user_prompt=user_prompt,
                system_prompt=sys_prompt,
                fallback=self.fallback_llm,
                model=self.llm_model,
                response_format=ClusterPlan,
                **self.llm_kwargs,
            )
            return json.loads(response.content), response
        except Exception as e:
            logger.warning(f"Error while clustering with {self.llm_model}: {e}")
            raise e

    def generate_iterative_summary(
        self,
        query: str,
        per_paper_summaries_extd: Dict[str, Dict[str, Any]],
        plan: Dict[str, Any],
        sys_prompt: str,
    ) -> Generator[CompletionResult, None, None]:
        """Stage 5: Generate narrative sections iteratively, building on previous sections with streaming output."""
        # first, we need to make a map from the index to the quotes because the llm is using index only

        # now fill in the prompt
        per_paper_summaries_tuples = [
            (ref_string, response)
            for ref_string, response in per_paper_summaries_extd.items()
        ]
        # only use the section headings from the plan, discard the quote indices
        plan_str = "\n".join([k for k in plan])
        existing_sections = []
        i = 0
        for section_name, inds in plan.items():
            # inds are a string like this: "[1, 2, 3]"
            # get the quotes for each index
            quotes = ""
            for ind in inds:
                if ind < len(per_paper_summaries_tuples):
                    quotes += (
                        per_paper_summaries_tuples[ind][0]
                        + ": "
                        + str(per_paper_summaries_tuples[ind][1])
                        + "\n"
                    )
                else:
                    logger.warning(f"index {ind} out of bounds")
            # existing sections should have their summaries removed because they are confusing.
            # remove anything in []
            already_written = "\n\n".join(existing_sections)
            already_written = re.sub(r"\[.*?\]", "", already_written)
            fill_in_prompt_args = {
                "query": query,
                "plan": plan_str,
                "already_written": already_written,
                "section_name": section_name,
            }
            if quotes:
                fill_in_prompt_args["section_references"] = quotes
                filled_in_prompt = sys_prompt.format(**fill_in_prompt_args)
            else:
                logger.warning(f"No quotes for section {section_name}")
                filled_in_prompt = PROMPT_ASSEMBLE_NO_QUOTES_SUMMARY.format(
                    **fill_in_prompt_args
                )

            try:
                logger.info(
                    f"About to call llm_completion_with_rate_limiting for section '{section_name}'"
                )
                response = llm_completion_with_rate_limiting(
                    user_prompt=filled_in_prompt,
                    fallback=self.fallback_llm,
                    model=self.llm_model,
                    **self.llm_kwargs,
                )
                logger.info(
                    f"LLM call successful for section '{section_name}', response type: {type(response)}"
                )
                existing_sections.append(response.content)
                logger.info(
                    f"Successfully generated section '{section_name}' with {response.total_tokens} tokens"
                )
                yield response
            except Exception as e:
                logger.error(f"Error generating section '{section_name}': {e}")
                logger.error(f"Exception type: {type(e)}")
                import traceback

                traceback.print_exc()
                raise  # Re-raise to maintain error flow
