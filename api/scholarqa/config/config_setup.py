import json
import logging
from typing import Callable, Literal, Optional

from pydantic import BaseModel, Field, validator

from scholarqa.state_mgmt.local_state_mgr import AbsStateMgrClient
from scholarqa.utils import TaskIdAwareLogFormatter, init_settings

logger = logging.getLogger(__name__)


class LogsConfig(BaseModel):
    log_dir: str = Field(
        default="logs",
        description="Directory to store logs, event traces and litellm cache",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )
    llm_cache_dir: str = Field(
        default="llm_cache", description="Sub directory to cache llm calls"
    )
    event_trace_loc: str = Field(
        default="scholarqa_traces",
        description="Sub directory to store event traces" "OR the GCS bucket name",
    )
    extras: dict = Field(default=None, description="Extra arguments for the logs")
    tracing_mode: Literal["local", "gcs"] = Field(
        default="local", description="Mode to store event traces (local or gcs)"
    )
    tid_log_formatter: TaskIdAwareLogFormatter = Field(
        default=None,
        description="Task Id aware log formatter which prepends the current task id to every log message",
    )

    @property
    def task_id(self):
        return self.tid_log_formatter.task_id

    @task_id.setter
    def task_id(self, task_id: str):
        self.tid_log_formatter.task_id = task_id

    def init_formatter(self):
        self.tid_log_formatter = init_settings(
            logs_dir=self.log_dir,
            log_level=self.log_level,
            litellm_cache_dir=self.llm_cache_dir,
        )

    class Config:
        arbitrary_types_allowed = True


class RunConfig(BaseModel):
    retrieval_service: str = Field(
        default="public_api", description="Service to use for paper retrieval"
    )
    retriever_args: dict = Field(
        default=None, description="Arguments for the retrieval service"
    )
    reranker_service: str = Field(
        default="remote",
        description="Service to use for paper reranking. Options: 'remote', 'crossencoder', 'biencoder', 'flag_embedding', 'modal'",
    )
    reranker_args: dict = Field(
        default=None, description="Arguments for the reranker service"
    )
    reranker_fallback_configs: Optional[dict] = Field(
        default=None,
        description="Optional fallback configurations for traditional local rerankers with model_name_or_path",
    )
    paper_finder_args: dict = Field(
        default=None, description="Arguments for the paper finder service"
    )
    pipeline_args: dict = Field(
        default=None, description="Arguments for the Scholar QA pipeline service"
    )

    @validator("reranker_service")
    def validate_reranker_service(cls, v):
        valid_services = {
            "remote",
            "crossencoder",
            "biencoder",
            "flag_embedding",
            "modal",
        }
        if v not in valid_services:
            raise ValueError(
                f"reranker_service must be one of {valid_services}, got {v}"
            )
        return v

    @validator("reranker_args")
    def validate_reranker_args(cls, v, values):
        if v is None:
            return v

        reranker_service = values.get("reranker_service", "remote")

        # Validate required fields based on reranker service type
        if reranker_service == "remote":
            # Remote reranker needs service_name and batch_size
            if "service_name" not in v:
                logger.warning(
                    "Remote reranker missing 'service_name', using default 'reranker-service'"
                )
            if "batch_size" not in v:
                logger.warning("Remote reranker missing 'batch_size', using default 32")

        elif reranker_service in ["crossencoder", "biencoder", "flag_embedding"]:
            # Local rerankers need model_name_or_path
            if "model_name_or_path" not in v:
                raise ValueError(
                    f'Local reranker service "{reranker_service}" requires "model_name_or_path" in reranker_args'
                )

        elif reranker_service == "modal":
            # Modal reranker needs app_name and api_name
            required_fields = ["app_name", "api_name"]
            missing_fields = [field for field in required_fields if field not in v]
            if missing_fields:
                raise ValueError(
                    f"Modal reranker service requires {missing_fields} in reranker_args"
                )

        return v

    @classmethod
    def get_reranker_config_examples(cls) -> dict:
        """
        Returns example configurations for different reranker services.
        Useful for documentation and validation.
        """
        return {
            "remote": {
                "reranker_service": "remote",
                "reranker_args": {"service_name": "reranker-service", "batch_size": 32},
            },
            "remote_with_fallback": {
                "reranker_service": "remote",
                "reranker_args": {
                    "service_name": "reranker-service",
                    "batch_size": 32,
                    "fallback_model_path": "mixedbread-ai/mxbai-rerank-large-v1",
                },
            },
            "crossencoder": {
                "reranker_service": "crossencoder",
                "reranker_args": {
                    "model_name_or_path": "mixedbread-ai/mxbai-rerank-large-v1"
                },
            },
            "biencoder": {
                "reranker_service": "biencoder",
                "reranker_args": {
                    "model_name_or_path": "avsolatorio/GIST-large-Embedding-v0"
                },
            },
            "flag_embedding": {
                "reranker_service": "flag_embedding",
                "reranker_args": {"model_name_or_path": "BAAI/bge-reranker-v2-m3"},
            },
            "modal": {
                "reranker_service": "modal",
                "reranker_args": {
                    "app_name": "your-modal-app-name",
                    "api_name": "your-modal-api-name",
                    "batch_size": 256,
                    "gen_options": {},
                },
            },
        }


class AppConfig(BaseModel):
    logs: LogsConfig = Field(
        default=None, description="Configuration for logs and event traces"
    )
    run_config: RunConfig = Field(
        default=None,
        description="Configuration for components of the ScholarQA pipeline",
    )
    state_mgr_client: AbsStateMgrClient = Field(
        default=None,
        description="State manager client for managing async task states and cost reporting of llm calls",
    )
    load_scholarqa: Callable = Field(
        default=None,
        description="Function to lazy load ScholarQA instance, should be overridden by the app using this config class",
    )

    def get_reranker_type(self) -> str:
        """Returns the type of reranker being used"""
        return self.run_config.reranker_service if self.run_config else "unknown"

    def is_remote_reranker(self) -> bool:
        """Returns True if using remote reranker service"""
        return self.get_reranker_type() == "remote"

    def has_fallback_reranker(self) -> bool:
        """Returns True if remote reranker has fallback configuration"""
        if not self.is_remote_reranker():
            return False
        return (
            self.run_config.reranker_args
            and "fallback_model_path" in self.run_config.reranker_args
        )

    def validate_config(self) -> list:
        """
        Validates the configuration and returns list of warnings/errors.
        Returns empty list if configuration is valid.
        """
        issues = []

        if not self.run_config:
            issues.append("ERROR: Missing run_config")
            return issues

        # Check reranker configuration
        reranker_service = self.run_config.reranker_service
        reranker_args = self.run_config.reranker_args or {}

        if reranker_service == "remote":
            if not reranker_args.get("service_name"):
                issues.append(
                    "WARNING: Remote reranker missing service_name, will use default"
                )
            if not reranker_args.get("batch_size"):
                issues.append(
                    "WARNING: Remote reranker missing batch_size, will use default"
                )

        elif reranker_service in ["crossencoder", "biencoder", "flag_embedding"]:
            if not reranker_args.get("model_name_or_path"):
                issues.append(
                    f"ERROR: {reranker_service} reranker requires model_name_or_path"
                )

        elif reranker_service == "modal":
            required = ["app_name", "api_name"]
            missing = [field for field in required if not reranker_args.get(field)]
            if missing:
                issues.append(
                    f"ERROR: Modal reranker missing required fields: {missing}"
                )

        return issues

    class Config:
        arbitrary_types_allowed = True


def read_json_config(config_path: str, model_class: AppConfig = AppConfig) -> AppConfig:
    logger.info(f"Reading app config from {config_path}")
    json_data = json.load(open(config_path, "r"))
    app_config = model_class.model_validate(json_data)
    app_config.logs.tid_log_formatter = init_settings(
        logs_dir=app_config.logs.log_dir,
        log_level=app_config.logs.log_level,
        litellm_cache_dir=app_config.logs.llm_cache_dir,
    )

    # Validate configuration and log any issues
    issues = app_config.validate_config()
    for issue in issues:
        if issue.startswith("ERROR:"):
            logger.error(issue)
        elif issue.startswith("WARNING:"):
            logger.warning(issue)

    # Log configuration details
    reranker_type = app_config.get_reranker_type()
    logger.info(f"Using reranker: {reranker_type}")

    if app_config.is_remote_reranker():
        if app_config.has_fallback_reranker():
            logger.info("Remote reranker configured with local fallback")
        else:
            logger.info("Remote reranker configured without fallback")

    return app_config
