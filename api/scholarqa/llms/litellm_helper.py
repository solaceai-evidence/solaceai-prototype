import logging
from scholarqa.llms.constants import *
from typing import List, Any, Callable, Tuple, Union, Generator, Optional

import litellm
from litellm.caching import Cache
from litellm.utils import trim_messages
from langsmith import traceable

from scholarqa.state_mgmt.local_state_mgr import AbsStateMgrClient
from scholarqa.llms.rate_limiter import RateLimiter
from time import sleep

logger = logging.getLogger(__name__)

######################################################################
# Setup rate limiter from environment variables (via app initialization)
######################################################################

# Global rate limiter instance set during app init
_rate_limiter: Optional[RateLimiter] = None


def set_rate_limiter(rate_limiter: RateLimiter):
    """Set the global rate limiter instance"""
    global _rate_limiter
    _rate_limiter = rate_limiter
    logger.info(f"Global rate limiter configured for LLM calls")


######################################################################
# LLM completion with rate limiting Wrappers
######################################################################


# Wrapper that enforces rate limiting around a single LLM completion (llm_completion).
# It estimates input tokens, acquires a rate-limiter slot, calls the LLM, then records actual token usage.
@traceable(run_type="llm", name="llm completion with rate limiting")
def llm_completion_with_rate_limiting(
    user_prompt: str,
    system_prompt: str = None,
    fallback: Optional[str] = GPT_5_CHAT,
    **llm_lite_params,
) -> CompletionResult:
    """Rate-limited version of llm_completion"""
    # Initialized global rate limiter
    global _rate_limiter

    # Apply rate limiting if enabled
    # (by acquiring permission to make one API request)
    if _rate_limiter:
        # Estimate input tokens (rough heuristic: ~4 chars per token)
        estimated_input = len(user_prompt + (system_prompt or "")) // 4

        with _rate_limiter.request_context(
            estimated_input_tokens=estimated_input
        ) as rate_limiter:
            result = llm_completion(
                user_prompt, system_prompt, fallback, **llm_lite_params
            )

            # Record actual token usage with the existing tracking
            rate_limiter.record_token_usage(result.input_tokens, result.output_tokens)

            # Log token usage for debugging
            logger.info(
                f"LLM call completed - Input: {result.input_tokens}, Output: {result.output_tokens}, Total: {result.total_tokens}, Cost: {result.cost}"
            )
            return result
    else:
        result = llm_completion(user_prompt, system_prompt, fallback, **llm_lite_params)
        logger.info(
            f"LLM call completed (no rate limiting) - Input: {result.input_tokens}, Output: {result.output_tokens}, Total: {result.total_tokens}, Cost: {result.cost}"
        )
        return result


# Wrapper that enforces rate limiting for batch completions by looping one message at a time and calling batch_llm_completion(model, [message], ...).
# Records usage per message.
@traceable(run_type="llm", name="batch llm completion with rate limiting")
def batch_llm_completion_with_rate_limiting(
    model: str,
    messages: List[str],
    system_prompt: str = None,
    fallback: Optional[str] = GPT_5_CHAT,
    **llm_lite_params,
) -> List[CompletionResult]:
    """Rate-limited version of batch_llm_completion"""
    global _rate_limiter

    if _rate_limiter:
        # Acquire permission for each message in the batch
        results = []
        for message in messages:
            # Estimate input tokens for this message
            estimated_input = len(message + (system_prompt or "")) // 4

            with _rate_limiter.request_context(
                estimated_input_tokens=estimated_input
            ) as rate_limiter:
                # Process 1 message at a time w rate limiting
                single_result = batch_llm_completion(
                    model, [message], system_prompt, fallback, **llm_lite_params
                )

                # Record actual token usage for this completion
                if single_result:
                    rate_limiter.record_token_usage(
                        single_result[0].input_tokens, single_result[0].output_tokens
                    )

                results.extend(single_result)
        return results
    else:
        return batch_llm_completion(
            model, messages, system_prompt, fallback, **llm_lite_params
        )


#########################################################################
# LLM completion
###########################################################################


class CostAwareLLMCaller:
    def __init__(self, state_mgr: AbsStateMgrClient):
        self.state_mgr = state_mgr

    # normalizes method results to (result, [CompletionResult], [models]).
    @staticmethod
    def parse_result_args(
        method_result: Union[Tuple[Any, CompletionResult], CompletionResult],
    ) -> Tuple[Any, List[CompletionResult], List[str]]:
        if type(method_result) == tuple:
            result, completion_costs = method_result
        else:
            result, completion_costs = method_result, method_result
        completion_costs = (
            [completion_costs] if type(completion_costs) != list else completion_costs
        )
        completion_models = [cost.model for cost in completion_costs]
        return result, completion_costs, completion_models

    # normalizes state_mgr.report_llm_usage return to (total_cost, tokens), defaulting tokens to zeros if not provided.
    def parse_usage_args(
        self, method_result: Union[Tuple[float, TokenUsage], float]
    ) -> Tuple[float, TokenUsage]:
        if isinstance(method_result, tuple):
            total_cost, tokens = method_result
        else:
            total_cost, tokens = method_result, TokenUsage(
                input=0, output=0, total=0, reasoning=0
            )
        return total_cost, tokens

    # Calls an LLM-using method, reports usage to state_mgr, returns a CostAwareLLMResult with costs/tokens/models.
    def call_method(
        self, cost_args: CostReportingArgs, method: Callable, **kwargs
    ) -> CostAwareLLMResult:
        method_result = method(**kwargs)
        result, completion_costs, completion_models = self.parse_result_args(
            method_result
        )
        llm_usage = self.state_mgr.report_llm_usage(
            completion_costs=completion_costs, cost_args=cost_args
        )
        total_cost, tokens = self.parse_usage_args(llm_usage)
        return CostAwareLLMResult(
            result=result, tot_cost=total_cost, models=completion_models, tokens=tokens
        )

    # Wraps a generator of LLM calls, yields incremental results, aggregates completions, reports usage once at the end, returns CostAwareLLMResult.
    # Includes detailed logging and fail-fast validation.
    def call_iter_method(
        self, cost_args: CostReportingArgs, gen_method: Callable, **kwargs
    ) -> Generator[Any, None, CostAwareLLMResult]:
        all_results, all_completion_costs, all_completion_models = [], [], []
        logger.info(f"Starting def call_iter_method for {cost_args.description}")

        try:
            for i, method_result in enumerate(gen_method(**kwargs)):
                result, completion_costs, completion_models = self.parse_result_args(
                    method_result
                )
                all_completion_costs.extend(completion_costs)
                all_completion_models.extend(completion_models)
                all_results.append(result)

                # Log individual completion details
                total_tokens_this_iter = sum(
                    [cost.total_tokens for cost in completion_costs]
                )
                logger.info(
                    f"Iteration {i+1}: {len(completion_costs)} completions, {total_tokens_this_iter} total tokens"
                )

                yield result
        except Exception as e:
            logger.error(f"Exception in iterative method {cost_args.description}: {e}")
            import traceback

            traceback.print_exc()
            raise  # Re-raise to fail fast and preserve the original error

        # Log aggregation details
        total_completions = len(all_completion_costs)
        if total_completions == 0:
            raise ValueError(
                f"No completions collected for {cost_args.description} - generator failed without producing any results"
            )

        total_input_tokens = sum([cost.input_tokens for cost in all_completion_costs])
        total_output_tokens = sum([cost.output_tokens for cost in all_completion_costs])
        total_all_tokens = sum([cost.total_tokens for cost in all_completion_costs])

        logger.info(
            f"Aggregating {total_completions} completions: Input={total_input_tokens}, Output={total_output_tokens}, Total={total_all_tokens}"
        )

        llm_usage = self.state_mgr.report_llm_usage(
            completion_costs=all_completion_costs, cost_args=cost_args
        )
        total_cost, tokens = self.parse_usage_args(llm_usage)

        if tokens is None:
            raise ValueError(
                f"Token aggregation failed for {cost_args.description} - state_mgr.report_llm_usage returned None tokens"
            )

        logger.info(f"Final aggregated tokens: {tokens}")

        result = CostAwareLLMResult(
            result=all_results,
            tot_cost=total_cost,
            models=all_completion_models,
            tokens=tokens,
        )

        logger.info(f"CostAwareLLMResult created with tokens: {result.tokens}")

        # Strict validation - fail fast if tokens is None
        if result.tokens is None:
            raise ValueError(
                "CostAwareLLMResult created with None tokens! This indicates a critical failure in token aggregation."
            )

        return result


# Attaches cache-hit info from LiteLLM into responses.
def success_callback(kwargs, completion_response, start_time, end_time):
    """required callback method to update the response object with cache hit/miss info"""
    completion_response.cache_hit = (
        kwargs["cache_hit"] if kwargs["cache_hit"] is not None else False
    )


NUM_RETRIES = 3
RETRY_STRATEGY = "exponential_backoff"
litellm.success_callback = [success_callback]


# Configures LiteLLM caching and enables it.
def setup_llm_cache(cache_type: str = "s3", **cache_args):
    logger.info("Setting up LLM cache...")
    litellm.cache = Cache(type=cache_type, **cache_args)
    litellm.enable_cache()


# Builds messages, calls litellm.batch_completion (with retry/fallback), computes cost and token usage, returns a list of CompletionResult.
@traceable(run_type="llm", name="batch completion")
def batch_llm_completion(
    model: str,
    messages: List[str],
    system_prompt: str = None,
    fallback: Optional[str] = GPT_5_CHAT,
    **llm_lite_params,
) -> List[Optional[CompletionResult]]:
    """returns the result from the llm chat completion api with cost and tokens used"""
    fallbacks = [f.strip() for f in fallback.split(",")] if fallback else []
    messages = [
        trim_messages(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": msg},
            ],
            model,
        )
        for msg in messages
    ]

    results, pending = [None] * len(messages), [_ for _ in range(len(messages))]
    curr_retry = 0

    # retries with exponential backoff in addition to fallbacks for pending instances
    while pending and curr_retry <= NUM_RETRIES:
        pending_msges = [messages[idx] for idx in pending]
        responses = litellm.completion_with_retries(
            messages=pending_msges,
            model=model,
            fallbacks=fallbacks,
            retry_strategy=RETRY_STRATEGY,
            num_retries=NUM_RETRIES,
            original_function=litellm.batch_completion,
            **llm_lite_params,
        )

        for i, res in enumerate(responses):
            original_idx = pending[i]  # Map back to original index
            try:
                res_cost = round(litellm.completion_cost(res), 6)
                res_usage = res.usage
                reasoning_tokens = (
                    0
                    if not (
                        res_usage.completion_tokens_details
                        and res_usage.completion_tokens_details.reasoning_tokens
                    )
                    else res_usage.completion_tokens_details.reasoning_tokens
                )
                res_str = res["choices"][0]["message"]["content"].strip()
                cost_tuple = CompletionResult(
                    content=res_str,
                    model=res["model"],
                    cost=res_cost if not res.get("cache_hit") else 0.0,
                    input_tokens=res_usage.prompt_tokens,
                    output_tokens=res_usage.completion_tokens,
                    total_tokens=res_usage.total_tokens,
                    reasoning_tokens=reasoning_tokens,
                )
                results[original_idx] = cost_tuple  # Use original index
            except Exception as e:
                if curr_retry == NUM_RETRIES:
                    logger.error(
                        f"Error received for instance {original_idx} in batch llm job, no more retries left: {e}"
                    )
                    raise e

        pending = [i for i, r in enumerate(results) if not r]
        curr_retry += 1
        if pending:
            logger.info(
                f"Retrying {len(pending)} failed instances in batch llm job, attempt {curr_retry}"
            )
            sleep(2**curr_retry)

    return results


# Core single LLM call.
# Builds messages, calls litellm.completion_with_retries (with retry/fallback), computes cost and token usage, returns a CompletionResult.
# Handles tool call content fallback.
@traceable(run_type="llm", name="completion")
def llm_completion(
    user_prompt: str, system_prompt: str = None, fallback=GPT_5_CHAT, **llm_lite_params
) -> CompletionResult:
    """returns the result from the llm chat completion api with cost and tokens used"""
    messages = []
    fallbacks = [f.strip() for f in fallback.split(",")] if fallback else []

    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    response = litellm.completion_with_retries(
        messages=messages,
        retry_strategy=RETRY_STRATEGY,
        num_retries=NUM_RETRIES,
        fallbacks=fallbacks,
        **llm_lite_params,
    )

    res_cost = round(litellm.completion_cost(response), 6)
    res_usage = response.usage
    reasoning_tokens = (
        0
        if not (
            res_usage.completion_tokens_details
            and res_usage.completion_tokens_details.reasoning_tokens
        )
        else res_usage.completion_tokens_details.reasoning_tokens
    )
    res_str = response["choices"][0]["message"]["content"]
    if res_str is None:
        logger.warning(
            "Content returned as None, checking for response in tool_calls..."
        )
        res_str = response["choices"][0]["message"]["tool_calls"][0].function.arguments
    cost_tuple = CompletionResult(
        content=res_str.strip(),
        model=response.model,
        cost=res_cost if not response.get("cache_hit") else 0.0,
        input_tokens=res_usage.prompt_tokens,
        output_tokens=res_usage.completion_tokens,
        total_tokens=res_usage.total_tokens,
        reasoning_tokens=reasoning_tokens,
    )
    return cost_tuple
