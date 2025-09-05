"""
Query refinement pipeline step for Solace-AI.
"""

import logging
from time import time
from typing import List, Dict, Any, Tuple, Optional, Callable
from pydantic import BaseModel, Field

from scholarqa.llms.litellm_helper import llm_completion
from scholarqa.llms.constants import CompletionResult
from scholarqa.llms.prompts import (
    SYSTEM_PROMPT_QUERY_REFINEMENT,
    PROMPT_SETTING_CLARITY_CHECK,
    PROMPT_CLIMATE_FACTOR_CHECK,
    PROMPT_HEALTH_OUTCOME_CHECK,
    PROMPT_TEMPORAL_SCOPE_CHECK,
    PROMPT_SETTING_CLARIFICATION,
    PROMPT_SETTING_SUGGESTION,
    PROMPT_CLIMATE_FACTOR_CLARIFICATION,
    PROMPT_CLIMATE_FACTOR_SUGGESTION,
    PROMPT_HEALTH_OUTCOME_CLARIFICATION,
    PROMPT_HEALTH_OUTCOME_SUGGESTION,
    PROMPT_TEMPORAL_SCOPE_CLARIFICATION,
    PROMPT_TEMPORAL_SCOPE_SUGGESTION,
    PROMPT_QUESTION_REFORMULATION,
)

logger = logging.getLogger(__name__)


class RefinedElements(BaseModel):
    """Container for the key elements of a research question."""

    setting: Optional[str] = Field(
        default=None, description="Geographic region or population context"
    )
    climate_factor: Optional[str] = Field(
        default=None, description="Climate-related factor, exposure, or intervention"
    )
    health_outcome: Optional[str] = Field(
        default=None, description="Health outcomes of interest"
    )
    temporal_scope: Optional[str] = Field(
        default=None,
        description="Temporal scope: immediate, short-term, medium-term, or long-term effects or actions",
    )


class QueryRefinementAnalysis(BaseModel):
    """Analysis of query completeness and missing elements"""

    is_setting_clear: bool = Field(
        description="Whether geographic/population context is clear"
    )
    is_climate_factor_clear: bool = Field(description="Whether climate factor is clear")
    is_health_outcome_clear: bool = Field(description="Whether health outcome is clear")
    is_temporal_scope_clear: bool = Field(description="Whether temporal scope is clear")
    needs_clarification: bool = Field(
        description="Whether any element needs clarification"
    )


class InteractiveRefinementStep(BaseModel):
    """Single step in the refinement process"""

    element_type: str = Field(
        description="Type of element being refined: setting, climate_factor, health_outcome, or temporal_scope"
    )
    prompt: str = Field(description="The prompt to show to the user")
    is_suggestion: bool = Field(
        default=False,
        description="Whether this is a suggestion or initial clarification",
    )


class QueryRefinementResult(BaseModel):
    """Result of query refinement analysis and optional reformulation."""

    original_query: str
    refined_query: str
    analysis: QueryRefinementAnalysis
    refined_elements: RefinedElements
    conversation_history: List[Tuple[str, str]] = Field(
        default_factory=list, description="List of (role, message) tuples"
    )
    interactive_steps: List[InteractiveRefinementStep] = Field(
        default_factory=list, description="Steps for interactive refinement"
    )
    needs_interaction: bool = Field(
        description="Whether the query needs interactive refinement"
    )


# ----------------- Core Functions ----------------- #
def check_element_clarity(
    query: str, element_type: str, llm_model: str, **llm_kwargs
) -> Tuple[bool, CompletionResult]:
    """
    Check if a specific element (setting, climate_factor, health_outcome, temporal_scope) is clear in the query.

    Returns (is_clear, completion_result).
    """
    logger.info(f"Checking {element_type} clarity for query: '{query}'")

    prompt_mapping = {
        "setting": PROMPT_SETTING_CLARITY_CHECK,
        "climate_factor": PROMPT_CLIMATE_FACTOR_CHECK,
        "health_outcome": PROMPT_HEALTH_OUTCOME_CHECK,
        "temporal_scope": PROMPT_TEMPORAL_SCOPE_CHECK,
    }

    expected_responses = {
        "setting": "SETTING_CLEAR",
        "climate_factor": "CLIMATE_CLEAR",
        "health_outcome": "HEALTH_OUTCOME_CLEAR",
        "temporal_scope": "TEMPORAL_CLEAR",
    }

    if element_type not in prompt_mapping:
        logger.error(f"Unknown element type: {element_type}")
        raise ValueError(f"Unknown element type: {element_type}")

    try:
        logger.debug(
            f"Using prompt for {element_type}: {prompt_mapping[element_type].format(question=query)}"
        )

        result = llm_completion(
            user_prompt=prompt_mapping[element_type].format(question=query),
            system_prompt=SYSTEM_PROMPT_QUERY_REFINEMENT,
            model=llm_model,
            temperature=0.0,
            **llm_kwargs,
        )

        llm_response = result.content.strip()
        is_clear = llm_response.startswith(expected_responses[element_type])

        logger.info(
            f"{element_type} clarity check result: {llm_response} -> {'CLEAR' if is_clear else 'NEEDS_CLARIFICATION'}"
        )
        logger.debug(
            f"LLM call cost: ${result.cost:.4f}, tokens: {result.total_tokens}"
        )

        return is_clear, result
    except Exception as e:
        logger.warning(f"{element_type} clarity check failed: {e}")
        # Fail-open: assume it's clear if we can't check
        error_completion = CompletionResult(
            content=f"Error checking {element_type}",
            model=f"error-{llm_model}",
            cost=0.0,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            reasoning_tokens=0,
        )
        logger.info(f"Failing open for {element_type} - assuming clear")
        return True, error_completion


def looks_broad(user_answer: str) -> bool:
    """
    Simple heuristic to determine if a user's answer looks broad and could benefit from a suggestion.
    """
    logger.debug(f"Evaluating broadness of answer: '{user_answer}'")

    broad_indicators = [
        "global",
        "worldwide",
        "all countries",
        "all regions",
        "general",
        "overall",
        "broad",
        "climate change",
        "health outcomes",
        "population",
        "people in general",
        "displaced communities",
        "communities",
        "refugees",  # Added common broad population terms
    ]
    answer_lower = user_answer.lower().strip()

    # If the answer is very short (1 word), consider it broad
    words = answer_lower.split()
    if len(words) == 1:
        logger.debug(f"Answer is too short ({len(words)} word) -> BROAD")
        return True

    # Check for exact broad phrases
    for indicator in broad_indicators:
        if indicator in answer_lower:
            logger.debug(f"Found broad indicator '{indicator}' in answer -> BROAD")
            return True

    logger.debug(f"Answer appears specific enough -> NOT BROAD")
    return False


def extract_element_from_query(query: str, element_type: str) -> Optional[str]:
    """
    Simple extraction of elements from the original query.
    This is a placeholder - in practice you might want more sophisticated extraction.
    """
    # For now, return None since the query wasn't clear enough to begin with
    # In a more sophisticated implementation, you could try to extract partial information
    return None


def assess_response_specificity(
    element_type: str, user_answer: str, llm_model: str, **llm_kwargs
) -> bool:
    """
    Use LLM to assess if a user response is broad/general and needs further clarification.
    Returns True if the response is broad and needs clarification.
    """
    logger.info(f"Assessing specificity of {element_type} response: '{user_answer}'")

    element_guidance = {
        "setting": (
            "population/setting specificity (geographic location, specific population groups)"
        ),
        "climate_factor": (
            "climate factor specificity (specific climate exposures vs. general climate change)"
        ),
        "health_outcome": (
            "health outcome specificity (specific diseases/conditions vs. general health)"
        ),
        "temporal_scope": (
            "temporal scope specificity (defined timeframes vs. vague time references)"
        ),
    }

    assessment_prompt = f"""
Based on the detailed system guidance for research question refinement, assess this user response:

Element type: {element_type} ({element_guidance.get(element_type, element_type)})
User answer: "{user_answer}"

According to the system guidance, is this answer BROAD/GENERAL (needs clarification) or SPECIFIC (acceptable)?

Consider the examples provided in the system prompt for {element_type}.

Respond with only "BROAD" or "SPECIFIC".
"""

    try:
        logger.debug(f"LLM assessment prompt: {assessment_prompt}")

        from scholarqa.llms.prompts import SYSTEM_PROMPT_QUERY_REFINEMENT
        from scholarqa.llms.litellm_helper import chat_completion_with_cache

        response = chat_completion_with_cache(
            model=llm_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_QUERY_REFINEMENT},
                {"role": "user", "content": assessment_prompt},
            ],
            **llm_kwargs,
        )

        result = response.choices[0].message.content.strip().upper()
        is_broad = result == "BROAD"

        logger.info(
            f"LLM assessment result: {result} -> {'NEEDS_CLARIFICATION' if is_broad else 'ACCEPTABLE'}"
        )

        return is_broad

    except Exception as e:
        logger.warning(f"LLM assessment failed: {e}, falling back to heuristic")
        # Fallback to the simple heuristic if LLM call fails
        fallback_result = looks_broad(user_answer)
        logger.info(
            f"Heuristic fallback result: {'BROAD' if fallback_result else 'SPECIFIC'}"
        )
        return fallback_result


def create_clarification_prompt(
    element_type: str, user_answer: Optional[str] = None
) -> str:
    """
    Create the appropriate clarification prompt for an element type.
    """
    if user_answer is None:
        # Initial clarification
        clarification_mapping = {
            "setting": PROMPT_SETTING_CLARIFICATION,
            "climate_factor": PROMPT_CLIMATE_FACTOR_CLARIFICATION,
            "health_outcome": PROMPT_HEALTH_OUTCOME_CLARIFICATION,
            "temporal_scope": PROMPT_TEMPORAL_SCOPE_CLARIFICATION,
        }
        return clarification_mapping[element_type]
    else:
        # Suggestion after user provided an answer
        suggestion_mapping = {
            "setting": PROMPT_SETTING_SUGGESTION,
            "climate_factor": PROMPT_CLIMATE_FACTOR_SUGGESTION,
            "health_outcome": PROMPT_HEALTH_OUTCOME_SUGGESTION,
            "temporal_scope": PROMPT_TEMPORAL_SCOPE_SUGGESTION,
        }
        return suggestion_mapping[element_type].format(user_answer=user_answer)


def analyze_query_completeness(
    query: str, llm_model: str, **llm_kwargs
) -> Tuple[QueryRefinementAnalysis, List[CompletionResult]]:
    """
    Analyze a query for completeness of all four elements.

    Returns analysis result and list of completion results for cost tracking.
    """
    logger.info(f"Starting comprehensive query analysis for: '{query}'")
    completions: List[CompletionResult] = []

    # Check all four elements
    logger.info("Checking all four elements sequentially...")

    setting_clear, setting_completion = check_element_clarity(
        query, "setting", llm_model, **llm_kwargs
    )
    completions.append(setting_completion)

    climate_clear, climate_completion = check_element_clarity(
        query, "climate_factor", llm_model, **llm_kwargs
    )
    completions.append(climate_completion)

    health_outcome_clear, health_completion = check_element_clarity(
        query, "health_outcome", llm_model, **llm_kwargs
    )
    completions.append(health_completion)

    temporal_clear, temporal_completion = check_element_clarity(
        query, "temporal_scope", llm_model, **llm_kwargs
    )
    completions.append(temporal_completion)

    needs_clarification = not (
        setting_clear and climate_clear and health_outcome_clear and temporal_clear
    )

    analysis = QueryRefinementAnalysis(
        is_setting_clear=setting_clear,
        is_climate_factor_clear=climate_clear,
        is_health_outcome_clear=health_outcome_clear,
        is_temporal_scope_clear=temporal_clear,
        needs_clarification=needs_clarification,
    )

    total_cost = sum(c.cost for c in completions)
    total_tokens = sum(c.total_tokens for c in completions)
    logger.info(
        f"Analysis complete - Clear: setting={setting_clear}, climate={climate_clear}, "
        f"health={health_outcome_clear}, temporal={temporal_clear}, needs_clarification={needs_clarification}, "
        f"cost: ${total_cost:.4f}"
    )

    return analysis, completions


def create_interactive_refinement_steps(
    query: str, analysis: QueryRefinementAnalysis
) -> List[InteractiveRefinementStep]:
    """
    Create the sequence of interactive steps needed to refine the query.
    """
    steps = []

    # Check each element in order and create steps as needed
    if not analysis.is_setting_clear:
        steps.append(
            InteractiveRefinementStep(
                element_type="setting",
                prompt=create_clarification_prompt("setting"),
                is_suggestion=False,
            )
        )

    if not analysis.is_climate_factor_clear:
        steps.append(
            InteractiveRefinementStep(
                element_type="climate_factor",
                prompt=create_clarification_prompt("climate_factor"),
                is_suggestion=False,
            )
        )

    if not analysis.is_health_outcome_clear:
        steps.append(
            InteractiveRefinementStep(
                element_type="health_outcome",
                prompt=create_clarification_prompt("health_outcome"),
                is_suggestion=False,
            )
        )

    return steps


def refine_query_with_conversation(
    original_query: str,
    conversation_history: List[Tuple[str, str]],
    llm_model: str,
    **llm_kwargs,
) -> Tuple[str, CompletionResult]:
    """
    Refine a query based on conversation history using question reformulation prompt.

    Returns refined query and completion result for cost tracking.
    """
    # Format conversation history for the prompt
    formatted_history = "\n".join(
        [f"{role}: {message}" for role, message in conversation_history]
    )

    try:
        result = llm_completion(
            user_prompt=PROMPT_QUESTION_REFORMULATION.format(
                conversation_history=formatted_history
            ),
            system_prompt=SYSTEM_PROMPT_QUERY_REFINEMENT,
            model=llm_model,
            temperature=0.1,
            **llm_kwargs,
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


def refine_research_question_interactive(
    user_question: str,
    user_responses: Dict[str, List[str]],
    llm_model: str,
    **llm_kwargs,
) -> Tuple[str, RefinedElements, List[Tuple[str, str]], List[CompletionResult]]:
    """
    Interactive refinement following the pseudocode logic.

    Args:
        user_question: Original user question
        user_responses: Dict mapping element types to list of user responses
                       e.g., {"setting": ["urban populations"], "climate_factor": ["extreme heat", "heatwaves"]}
        llm_model: LLM model to use
        **llm_kwargs: Additional LLM parameters

    Returns:
        Tuple of (final_question, refined_elements, conversation_history, completions)
    """
    conversation_history: List[Tuple[str, str]] = []
    completions: List[CompletionResult] = []
    refined_elements = RefinedElements()

    # STEP 1: setting check
    setting_clear, setting_completion = check_element_clarity(
        user_question, "setting", llm_model, **llm_kwargs
    )
    completions.append(setting_completion)

    if not setting_clear:
        # Get user response for setting
        setting_responses = user_responses.get("setting", [])
        if setting_responses:
            user_answer = setting_responses[0]
            conversation_history.append(("assistant", PROMPT_SETTING_CLARIFICATION))
            conversation_history.append(("user", user_answer))

            # Check if we need a suggestion
            if len(setting_responses) > 1 and looks_broad(user_answer):
                followup = setting_responses[1] if len(setting_responses) > 1 else ""
                suggestion = create_clarification_prompt("setting", user_answer)
                conversation_history.append(("assistant", suggestion))
                conversation_history.append(("user", followup))
                refined_elements.setting = followup if followup else user_answer
            else:
                refined_elements.setting = user_answer
    else:
        refined_elements.setting = extract_element_from_query(user_question, "setting")

    # STEP 2: climate factor check
    climate_clear, climate_completion = check_element_clarity(
        user_question, "climate_factor", llm_model, **llm_kwargs
    )
    completions.append(climate_completion)

    if not climate_clear:
        # Get user response for climate factor
        climate_responses = user_responses.get("climate_factor", [])
        if climate_responses:
            user_answer = climate_responses[0]
            conversation_history.append(
                ("assistant", PROMPT_CLIMATE_FACTOR_CLARIFICATION)
            )
            conversation_history.append(("user", user_answer))

            # Check if we need a suggestion
            if len(climate_responses) > 1 and looks_broad(user_answer):
                followup = climate_responses[1] if len(climate_responses) > 1 else ""
                suggestion = create_clarification_prompt("climate_factor", user_answer)
                conversation_history.append(("assistant", suggestion))
                conversation_history.append(("user", followup))
                refined_elements.climate_factor = followup if followup else user_answer
            else:
                refined_elements.climate_factor = user_answer
    else:
        refined_elements.climate_factor = extract_element_from_query(
            user_question, "climate_factor"
        )

    # STEP 3: health outcome factor check
    health_outcome_clear, health_completion = check_element_clarity(
        user_question, "health_outcome", llm_model, **llm_kwargs
    )
    completions.append(health_completion)

    if not health_outcome_clear:
        # Get user response for health outcome
        health_responses = user_responses.get("health_outcome", [])
        if health_responses:
            user_answer = health_responses[0]
            conversation_history.append(
                ("assistant", PROMPT_HEALTH_OUTCOME_CLARIFICATION)
            )
            conversation_history.append(("user", user_answer))

            # Check if we need a suggestion
            if len(health_responses) > 1 and looks_broad(user_answer):
                followup = health_responses[1] if len(health_responses) > 1 else ""
                suggestion = create_clarification_prompt("health_outcome", user_answer)
                conversation_history.append(("assistant", suggestion))
                conversation_history.append(("user", followup))
                refined_elements.health_outcome = followup if followup else user_answer
            else:
                refined_elements.health_outcome = user_answer
    else:
        refined_elements.health_outcome = extract_element_from_query(
            user_question, "health_outcome"
        )

    # STEP 4: final reformulation
    final_question, reformulation_completion = refine_query_with_conversation(
        user_question, conversation_history, llm_model, **llm_kwargs
    )
    completions.append(reformulation_completion)

    return final_question, refined_elements, conversation_history, completions


def run_query_refinement_step(
    query: str,
    llm_model: str,
    user_responses: Optional[Dict[str, List[str]]] = None,
    **llm_kwargs,
) -> Tuple[QueryRefinementResult, List[CompletionResult]]:
    """
    Main pipeline step for query refinement.

    Analyzes query completeness and optionally runs interactive refinement if user_responses provided.
    Returns result compatible with pipeline patterns and completion results for cost tracking.

    Args:
        query: The original user query
        llm_model: LLM model to use for analysis
        user_responses: Optional dict of user responses for interactive refinement
                       Format: {"setting": ["response1", "response2"], "climate_factor": [...], "health_outcome": [...]}
        **llm_kwargs: Additional LLM parameters
    """
    pipeline_start = time()
    logger.info(f"Starting query refinement pipeline - Query: '{query}', Model: {llm_model}")
    if user_responses:
        logger.info(f"User responses provided: {user_responses}")

    all_completions: List[CompletionResult] = []

    # Step 1: Analyze query completeness
    logger.info("STEP 1: Analyzing query completeness...")
    analysis, analysis_completions = analyze_query_completeness(
        query, llm_model, **llm_kwargs
    )
    all_completions.extend(analysis_completions)

    # Initialize default values
    refined_query = query
    refined_elements = RefinedElements()
    conversation_history: List[Tuple[str, str]] = []

    # Step 2: Determine what clarification is needed based on analysis and current user responses
    logger.info("STEP 2: Determining next clarification step...")
    next_step = determine_next_clarification_step(analysis, user_responses)

    if next_step:
        logger.info(
            f"Next step needed: {next_step['element_type']} ({'suggestion' if next_step.get('is_suggestion') else 'initial clarification'})"
        )
    else:
        logger.info("No further clarification needed")

    # Step 3: If user responses are provided, process the current step
    if user_responses and next_step:
        logger.info("STEP 3: Processing user responses...")
        # Process the current user response and determine if we need a follow-up
        processed_step = process_user_response_for_step(
            next_step, user_responses, llm_model, **llm_kwargs
        )
        if processed_step:
            logger.info(
                f"Added conversation entries: {len(processed_step['conversation'])}"
            )
            conversation_history.extend(processed_step["conversation"])
            if processed_step["element_value"]:
                setattr(
                    refined_elements,
                    next_step["element_type"],
                    processed_step["element_value"],
                )
                logger.info(
                    f"Set {next_step['element_type']} = '{processed_step['element_value']}'"
                )

            # Check if we need a follow-up suggestion
            if processed_step.get("needs_followup"):
                next_step = processed_step["followup_step"]
                logger.info(f"Follow-up needed for {next_step['element_type']}")
            else:
                # Move to the next element that needs clarification
                logger.info(
                    f"{next_step['element_type']} complete, checking for next element..."
                )
                next_step = determine_next_clarification_step(
                    analysis, user_responses, skip_element=next_step["element_type"]
                )
                if next_step:
                    logger.info(f"Moving to next element: {next_step['element_type']}")
                else:
                    logger.info("All elements processed")

    # Step 4: If we have completed the interactive refinement, generate the final query
    if user_responses and not next_step:
        logger.info("STEP 4: Generating final refined query...")
        refined_query, refinement_completion = refine_query_with_conversation(
            query, conversation_history, llm_model, **llm_kwargs
        )
        all_completions.append(refinement_completion)
        needs_interaction = False
        logger.info(f"Final refined query: '{refined_query}'")
    elif next_step:
        needs_interaction = True
        logger.info(
            f"⏸Interaction needed: waiting for {next_step['element_type']} response"
        )
    else:
        # No interaction needed - query is already complete or no responses provided
        needs_interaction = (
            len(create_interactive_refinement_steps(query, analysis)) > 0
        )
        if (
            analysis.is_setting_clear
            and analysis.is_climate_factor_clear
            and analysis.is_health_outcome_clear
            and analysis.is_temporal_scope_clear
        ):
            # Extract elements from the original query
            refined_elements.setting = (
                extract_element_from_query(query, "setting") or "global population"
            )
            refined_elements.climate_factor = (
                extract_element_from_query(query, "climate_factor")
                or "climate change in general"
            )
            refined_elements.health_outcome = (
                extract_element_from_query(query, "health_outcome")
                or "all health outcomes"
            )
            refined_elements.temporal_scope = (
                extract_element_from_query(query, "temporal_scope") or "all timeframes"
            )
            logger.info("Applied default fallback values for complete query")
        logger.info(f"Query complete, needs interaction: {needs_interaction}")

    # Step 5: Create interactive steps for the frontend
    if needs_interaction and next_step:
        interactive_steps = [
            InteractiveRefinementStep(
                element_type=next_step["element_type"],
                prompt=next_step["prompt"],
                is_suggestion=next_step.get("is_suggestion", False),
            )
        ]
        logger.info(f"Created interactive step for UI: {next_step['element_type']}")
    else:
        interactive_steps = []
        logger.info("No interactive steps needed")

    result = QueryRefinementResult(
        original_query=query,
        refined_query=refined_query,
        analysis=analysis,
        refined_elements=refined_elements,
        conversation_history=conversation_history,
        interactive_steps=interactive_steps,
        needs_interaction=needs_interaction,
    )

    # Final summary logging
    total_cost = sum(c.cost for c in all_completions)
    total_tokens = sum(c.total_tokens for c in all_completions)
    
    logger.info(
        f"Query refinement complete - Status: {'NEEDS_INTERACTION' if needs_interaction else 'COMPLETE'}, "
        f"cost: ${total_cost:.4f}, time: {time() - pipeline_start:.2f}"
    )
    logger.info(f"Refined query: '{refined_query}'" if refined_query != query else "Query unchanged")

    return result, all_completions


def determine_next_clarification_step(
    analysis: QueryRefinementAnalysis,
    user_responses: Optional[Dict[str, List[str]]] = None,
    skip_element: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Determine what the next clarification step should be based on analysis and current responses.

    Returns a dict with element_type, prompt, and is_suggestion fields, or None if no clarification needed.
    """
    if user_responses is None:
        user_responses = {}

    # Define the order of elements to check
    elements_to_check = [
        ("setting", analysis.is_setting_clear),
        ("climate_factor", analysis.is_climate_factor_clear),
        ("health_outcome", analysis.is_health_outcome_clear),
        ("temporal_scope", analysis.is_temporal_scope_clear),
    ]

    for element_type, is_clear in elements_to_check:
        if skip_element and element_type == skip_element:
            continue

        if not is_clear:
            responses = user_responses.get(element_type, [])

            if len(responses) == 0:
                # Need initial clarification
                return {
                    "element_type": element_type,
                    "prompt": create_clarification_prompt(element_type),
                    "is_suggestion": False,
                }
            elif len(responses) == 1:
                # Check if the first response looks broad and needs a suggestion
                user_answer = responses[0]
                if user_answer != "[SKIP]" and looks_broad(user_answer):
                    return {
                        "element_type": element_type,
                        "prompt": create_clarification_prompt(
                            element_type, user_answer
                        ),
                        "is_suggestion": True,
                    }
                # Otherwise, this element is complete, continue to next
            # If len(responses) >= 2, this element is complete

    return None


def process_user_response_for_step(
    step: Dict[str, Any],
    user_responses: Dict[str, List[str]],
    llm_model: str,
    **llm_kwargs,
) -> Optional[Dict[str, Any]]:
    """
    Process a user response for a specific clarification step.

    Returns a dict with conversation history, element value, and whether a followup is needed.
    """
    element_type = step["element_type"]
    responses = user_responses.get(element_type, [])

    if not responses:
        return None

    conversation = []
    element_value = None
    needs_followup = False
    followup_step = None

    if step.get("is_suggestion", False):
        # This is a suggestion step (follow-up)
        if len(responses) >= 2:
            initial_answer = responses[0]
            followup_answer = responses[1]

            # Add the original clarification and response
            conversation.append(
                ("assistant", create_clarification_prompt(element_type))
            )
            conversation.append(("user", initial_answer))

            # Add the suggestion and follow-up response
            conversation.append(("assistant", step["prompt"]))
            conversation.append(("user", followup_answer))

            # Use the follow-up answer if provided, otherwise use the initial answer
            element_value = (
                followup_answer
                if followup_answer.strip() and followup_answer != "[SKIP]"
                else initial_answer
            )
        else:
            # We have the suggestion step but no follow-up response yet
            initial_answer = responses[0]
            conversation.append(
                ("assistant", create_clarification_prompt(element_type))
            )
            conversation.append(("user", initial_answer))

            # We need to wait for the follow-up response
            needs_followup = True
            followup_step = step
    else:
        # This is an initial clarification step
        user_answer = responses[0]
        conversation.append(("assistant", step["prompt"]))
        conversation.append(("user", user_answer))

        # Check if we need a follow-up suggestion
        if user_answer != "[SKIP]" and looks_broad(user_answer):
            needs_followup = True
            followup_step = {
                "element_type": element_type,
                "prompt": create_clarification_prompt(element_type, user_answer),
                "is_suggestion": True,
            }
        else:
            element_value = user_answer

    return {
        "conversation": conversation,
        "element_value": element_value,
        "needs_followup": needs_followup,
        "followup_step": followup_step,
    }


def get_next_refinement_step(
    refinement_result: QueryRefinementResult, step_index: int = 0
) -> Optional[InteractiveRefinementStep]:
    """
    Get the next step in the interactive refinement process.

    Args:
        refinement_result: Result from run_query_refinement_step
        step_index: Index of the step to retrieve (0-based)

    Returns:
        The next step or None if no more steps
    """
    if step_index < len(refinement_result.interactive_steps):
        return refinement_result.interactive_steps[step_index]
    return None


def create_suggestion_step(
    element_type: str, user_answer: str
) -> InteractiveRefinementStep:
    """
    Create a suggestion step for a given broad answer by the user.

    Args:
        element_type: either setting, climate_factor or health_outcome
        user_answer: The user's initial answer

    Returns:
        InteractiveRefinementStep for the suggestion
    """
    return InteractiveRefinementStep(
        element_type=element_type,
        prompt=create_clarification_prompt(element_type, user_answer),
        is_suggestion=True,
    )
