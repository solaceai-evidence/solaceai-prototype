
# Ai2 Scholar QA

<img width="1050" alt="image" src="https://github.com/user-attachments/assets/2d7ccc15-2cd8-4316-bec6-ed2a1509f27b" />

This repo houses the code for the [live demo](https://scholarqa.allen.ai/) and can be run as local docker containers or embedded into another application as a [python package](https://pypi.org/project/ai2-scholar-qa).

- [Overview](#overview)
- [Setup](#setup)
  * [Environment Variables](#environment-variables)
  * [Runtime Config](#runtime-config)

### Overview

### Setup

 - #### Environment Variables

Environment Variables
Ai2 Scholar QA requires Semantic Scholar api and LLMs for its core functionality of retrieval and generation. So please ensure to create a ``.env``  file in the root directory with the following environment variables:

```
export S2_API_KEY=  
export ANTHROPIC_API_KEY=
export OPENAI_API_KEY=
```

``S2_API_KEY`` : Used to retrieve the relevant [paper passages](https://api.semanticscholar.org/api-docs/#tag/Snippet-Text/operation/get_snippet_search) , [keyword search results](https://api.semanticscholar.org/api-docs/#tag/Paper-Data/operation/get_graph_paper_relevance_search) and [associated metadata](https://api.semanticscholar.org/api-docs/#tag/Paper-Data/operation/post_graph_get_papers) via the Semantic Scholar public api.

``ANTHROPIC_API_KEY`` : Ai2 Scholar QA uses Anthropic's [Claude 3.5 Sonnet](https://www.anthropic.com/news/claude-3-5-sonnet) as the primary LLM for generation, but any model served by [litellm](https://docs.litellm.ai/docs/providers) should work. Please configure the corresponding api key here.

`OPENAI_API_KEY`: OpenAI's [GPT 4o](https://openai.com/index/gpt-4o-and-more-tools-to-chatgpt-free/) is configured as the fallback llm. **Note:** We also use OpenAI's [text moderation api](https://platform.openai.com/docs/guides/moderation/overview#:~:text=The%20moderation%20endpoint%20is%20free%20to%20use%20when%20monitoring%20the%20inputs%20and%20outputs%20of%20OpenAI%20APIs.%20We%20currently%20disallow%20other%20use%20cases.)  to validate and filter harmful queries. If you don't have access to an OpenAI api key, this feature will be disabled.

If you use [Modal](https://modal.com/) to serve your models, please configure `MODAL_TOKEN` and `MODAL_TOKEN_SECRET` here as well.

#### Runtime Config
Please refer to [default.json](https://github.com/allenai/ai2-scholarqa-lib/blob/main/api/run_configs/default.json) for the default runtime config.
```json
{
  "logs": {
    "log_dir": "logs",
    "llm_cache_dir": "llm_cache",
    "event_trace_loc": "scholarqa_traces",
    "tracing_mode": "local"
  },
  "run_config": {
    "retrieval_service": "public_api",
    "retriever_args": {
      "n_retrieval": 256,
      "n_keyword_srch": 20
    },
    "reranker_service": "modal",
    "reranker_args": {
      "app_name": "ai2-scholar-qa",
      "api_name": "inference_api",
      "batch_size": 256,
      "gen_options": {}
    },
    "paper_finder_args": {
      "n_rerank": 50,
      "context_threshold": 0.5
    },
    "pipeline_args": {
      "validate": true,
      "llm": "anthropic/claude-3-5-sonnet-20241022",
      "decomposer_llm": "anthropic/claude-3-5-sonnet-20241022",
      "tables_llm": "openai/gpt-4o"
    }
  }
}
```

