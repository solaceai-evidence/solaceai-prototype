"""
Query refinement pipeline step for ScholarQA.
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field

from scholarqa.llms.litellm_helper import llm_completion
from scholarqa.llms.constants import CompletionResult
from scholarqa.llms.prompts import (
    SYSTEM_PROMPT_QUERY_REFINEMENT,
    PROMPT_SETTING_CLARITY_CHECK,
    PROMPT_QUESTION_COMPLETENESS_CHECK,
    PROMPT_QUESTION_REFORMULATION,
    PROMPT_GENERAL_CLARIFICATION,
    PROMPT_SETTING_CLARIFICATION,
)

logger = logging.getLogger(__name__)


class QueryRefinementAnalysis(BaseModel):
    """Analysis of query completeness and missing elements."""
    setting_clear: bool = Field(description="Whether geographic/population context is clear")
    question_complete: bool = Field(description="Whether question has sufficient detail")
    missing_element: Optional[str] = Field(default=None, description="Single most critical missing element")
    clarification_suggestion: Optional[str] = Field(default=None, description="Suggested clarification question")


class QueryRefinementResult(BaseModel):
    """Result of query refinement analysis and optional reformulation."""
    original_query: str
    refined_query: str
    analysis: QueryRefinementAnalysis
    needs_clarification: bool = Field(description="Whether the query would benefit from clarification")
    conversation_ready: bool = Field(default=False, description="Whether this result can start an interactive session")


def analyze_query_completeness(
    query: str,
    llm_model: str,
    **llm_kwargs
) -> Tuple[QueryRefinementAnalysis, List[CompletionResult]]:
    """
    Analyze a query for completeness using the Solace-AI prompts.
    
    Returns analysis result and list of completion results for cost tracking.
    """
    completions: List[CompletionResult] = []
    
    # Check setting clarity
    try:
        setting_result = llm_completion(
            user_prompt=PROMPT_SETTING_CLARITY_CHECK.format(question=query),
            system_prompt=SYSTEM_PROMPT_QUERY_REFINEMENT,
            model=llm_model,
            temperature=0.0,
            **llm_kwargs
        )
        completions.append(setting_result)
        setting_clear = setting_result.content.strip().startswith("SETTING_CLEAR")
    except Exception as e:
        logger.warning(f"Setting clarity check failed: {e}")
        setting_clear = True  # Fail-open
        
    # Check question completeness
    try:
        completeness_result = llm_completion(
            user_prompt=PROMPT_QUESTION_COMPLETENESS_CHECK.format(question=query),
            system_prompt=SYSTEM_PROMPT_QUERY_REFINEMENT,
            model=llm_model,
            temperature=0.0,
            **llm_kwargs
        )
        completions.append(completeness_result)
        comp_response = completeness_result.content.strip()
        question_complete = comp_response.startswith("COMPLETE")
        
        # Extract missing element if present
        if not question_complete and "NEEDS_CLARIFICATION:" in comp_response:
            missing_element = comp_response.split("NEEDS_CLARIFICATION:", 1)[1].strip()
        else:
            missing_element = None
            
    except Exception as e:
        logger.warning(f"Question completeness check failed: {e}")
        question_complete = True  # Fail-open
        missing_element = None
    
    # Generate clarification suggestion
    clarification_suggestion = None
    if not setting_clear:
        clarification_suggestion = PROMPT_SETTING_CLARIFICATION
    elif missing_element:
        clarification_suggestion = PROMPT_GENERAL_CLARIFICATION.format(missing_aspect=missing_element)
    
    analysis = QueryRefinementAnalysis(
        setting_clear=setting_clear,
        question_complete=question_complete,
        missing_element=missing_element,
        clarification_suggestion=clarification_suggestion
    )
    
    return analysis, completions


def refine_query_with_context(
    original_query: str,
    conversation_history: str,
    llm_model: str,
    **llm_kwargs
) -> Tuple[str, CompletionResult]:
    """
    Refine a query based on conversation context using question reformulation prompt.
    
    Returns refined query and completion result for cost tracking.
    """
    try:
        result = llm_completion(
            user_prompt=PROMPT_QUESTION_REFORMULATION.format(conversation_history=conversation_history),
            system_prompt=SYSTEM_PROMPT_QUERY_REFINEMENT,
            model=llm_model,
            temperature=0.1,
            **llm_kwargs
        )
        refined_query = result.content.strip()
        return refined_query, result
    except Exception as e:
        logger.warning(f"Query reformulation failed: {e}")
        # Return original query with error completion for cost tracking
        error_completion = CompletionResult(
            content=original_query,
            model=f"error-{llm_model}",
            cost=0.0,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            reasoning_tokens=0,
        )
        return original_query, error_completion


def run_query_refinement_step(
    query: str,
    llm_model: str,
    conversation_context: Optional[str] = None,
    **llm_kwargs
) -> Tuple[QueryRefinementResult, List[CompletionResult]]:
    """
    Main pipeline step for query refinement.
    
    Analyzes query completeness and optionally refines it if conversation context is provided.
    Returns result compatible with pipeline patterns and completion results for cost tracking.
    """
    all_completions: List[CompletionResult] = []
    
    # Always analyze the query first
    analysis, analysis_completions = analyze_query_completeness(query, llm_model, **llm_kwargs)
    all_completions.extend(analysis_completions)
    
    # If conversation context is provided, refine the query
    refined_query = query
    if conversation_context:
        refined_query, refinement_completion = refine_query_with_context(
            query, conversation_context, llm_model, **llm_kwargs
        )
        all_completions.append(refinement_completion)
    
    # Determine if query needs clarification
    needs_clarification = not analysis.setting_clear or not analysis.question_complete
    
    result = QueryRefinementResult(
        original_query=query,
        refined_query=refined_query,
        analysis=analysis,
        needs_clarification=needs_clarification,
        conversation_ready=bool(analysis.clarification_suggestion)
    )
    
    return result, all_completions