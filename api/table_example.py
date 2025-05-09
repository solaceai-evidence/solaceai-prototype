import logging
import uuid

from scholarqa.config.config_setup import LogsConfig
from scholarqa.state_mgmt.local_state_mgr import LocalStateMgrClient
from scholarqa.rag.retriever_base import FullTextRetriever
from scholarqa.rag.retrieval import PaperFinder
from scholarqa.llms.litellm_helper import CostAwareLLMCaller
from scholarqa.table_generation.table_generator import TableGenerator


retriever = FullTextRetriever(n_retrieval=256, n_keyword_srch=20)
logger = logging.getLogger(__name__)
logger.info("initializing the log configs")
logs_config = LogsConfig(llm_cache_dir="lib_llm_cache")
logs_config.init_formatter()
state_mgr = LocalStateMgrClient(logs_config.log_dir)
table_generator = TableGenerator(
    paper_finder=PaperFinder(retriever=retriever),
    llm_caller=CostAwareLLMCaller(state_mgr=state_mgr),
)
table = table_generator.run_table_generation(
    thread_id=uuid.uuid4().hex,
    user_id="test_user",
    original_query="What AI work has been done in answering science questions? Add year and citation columns",
    section_title="Applications and Specialized Systems",
    corpus_ids=[214594294, 204915921, 220250086, 40382019, 206561353, 234119176, 2598611, 20813703, 221800820],
)
print(table)