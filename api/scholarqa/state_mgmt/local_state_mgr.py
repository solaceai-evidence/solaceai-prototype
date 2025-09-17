import logging
import os
from abc import ABC, abstractmethod
from time import time
from typing import Any, List, Optional, Tuple, Union
from uuid import UUID, uuid5

from nora_lib.tasks.state import IStateManager, StateManager

from scholarqa.llms.constants import CompletionResult, CostReportingArgs, TokenUsage
from scholarqa.models import AsyncTaskState, TaskResult, TaskStep, ToolRequest

logger = logging.getLogger(__name__)

UUID_NAMESPACE = os.getenv("UUID_ENCODER_KEY", "ai2-scholar-qa")


class AbsStateMgrClient(ABC):
    @abstractmethod
    def get_state_mgr(self, tool_req: ToolRequest) -> IStateManager:
        pass

    def init_task(self, task_id: str, tool_request: ToolRequest):
        pass

    def update_task_state(
        self,
        task_id: str,
        tool_req: ToolRequest,
        status: str,
        step_estimated_time: int = 0,
        curr_response: Any = None,
        task_estimated_time: str = None,
    ):
        state_mgr = self.get_state_mgr(tool_req)
        curr_step = TaskStep(description=status, start_timestamp=time())
        task_state = state_mgr.read_state(task_id)
        task_state.task_status = status
        if step_estimated_time:
            curr_step.estimated_timestamp = (
                curr_step.start_timestamp + step_estimated_time
            )
        if task_estimated_time:
            task_state.estimated_time = task_estimated_time
        if curr_response:
            # Create TaskResult with required fields - using defaults for intermediate state
            task_state.task_result = TaskResult(
                sections=curr_response,
                tokens={
                    "input": 0,
                    "output": 0,
                    "total": 0,
                    "reasoning": 0,
                },  # Placeholder for intermediate results
                cost=0.0,  # Placeholder for intermediate results
            )
        task_state.extra_state["steps"].append(curr_step)
        state_mgr.write_state(task_state)

    def report_llm_usage(
        self, completion_costs: List[CompletionResult], cost_args: CostReportingArgs
    ) -> float:
        pass


class LocalStateMgrClient(AbsStateMgrClient):
    def __init__(self, logs_dir: str, async_state_dir: str = "async_state"):
        self._async_state_dir = f"{logs_dir}/{async_state_dir}"
        os.makedirs(self._async_state_dir, exist_ok=True)
        self.state_mgr = StateManager(AsyncTaskState, self._async_state_dir)

    def get_state_mgr(self, tool_req: Optional[ToolRequest] = None) -> IStateManager:
        return self.state_mgr

    def report_llm_usage(
        self, completion_costs: List[CompletionResult], cost_args: CostReportingArgs
    ) -> Union[float, Tuple[float, TokenUsage]]:
        if not completion_costs:
            raise ValueError(
                f"report_llm_usage called with empty completion_costs list for {cost_args.description} - this indicates a critical failure in LLM completion"
            )

        tot_cost = sum([cost.cost for cost in completion_costs])
        token_usage = TokenUsage(
            input=sum([cost.input_tokens for cost in completion_costs]),
            output=sum([cost.output_tokens for cost in completion_costs]),
            total=sum([cost.total_tokens for cost in completion_costs]),
            reasoning=sum([cost.reasoning_tokens for cost in completion_costs]),
        )

        logger.info(
            f"report_llm_usage for {cost_args.description}: {len(completion_costs)} completions, tokens={token_usage}"
        )

        return tot_cost, token_usage

    def init_task(self, task_id: str, tool_request: ToolRequest):
        try:
            tool_request.user_id = str(
                uuid5(
                    namespace=UUID(tool_request.user_id), name=f"nora-{UUID_NAMESPACE}"
                )
            )
        except Exception as e:
            pass
