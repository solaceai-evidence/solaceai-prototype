import logging
import os
from abc import ABC, abstractmethod
from time import time
from typing import List, Any

from nora_lib.tasks.state import IStateManager, StateManager

from scholarqa.llms.constants import CompletionResult
from scholarqa.models import TaskResult, TaskStep, AsyncTaskState


class AbsStateMgrClient(ABC):
    @abstractmethod
    def get_state_mgr(self, msg_id: str) -> IStateManager:
        pass

    def init_task(self, task_id: str, tool_request: Any):
        pass

    def update_task_state(
            self,
            task_id: str,
            status: str,
            step_estimated_time: int = 0,
            curr_response: Any = None,
            task_estimated_time: str = None,
    ):
        state_mgr = self.get_state_mgr(task_id)
        curr_step = TaskStep(description=status, start_timestamp=time())
        task_state = state_mgr.read_state(task_id)
        task_state.task_status = status
        if step_estimated_time:
            curr_step.estimated_timestamp = curr_step.start_timestamp + step_estimated_time
        if task_estimated_time:
            task_state.estimated_time = task_estimated_time
        if curr_response:
            task_state.task_result = TaskResult(sections=curr_response)
        task_state.extra_state["steps"].append(curr_step)
        state_mgr.write_state(task_state)

    def report_llm_usage(self, completion_costs: List[CompletionResult], task_id: str, user_id: str, description: str,
                         model: str) -> float:
        pass


class LocalStateMgrClient(AbsStateMgrClient):
    def __init__(self, logs_dir: str, async_state_dir: str = "async_state"):
        self._async_state_dir = f"{logs_dir}/{async_state_dir}"
        os.makedirs(self._async_state_dir, exist_ok=True)
        self.state_mgr = StateManager(AsyncTaskState, self._async_state_dir)

    def get_state_mgr(self, msg_id: str) -> IStateManager:
        return self.state_mgr

    def report_llm_usage(self, completion_costs: List[CompletionResult], task_id: str, user_id: str, description: str,
                         model: str) -> float:
        return sum([cost.cost for cost in completion_costs])
