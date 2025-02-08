

# Ai2 Scholar QA

<img width="1050" alt="image" src="https://github.com/user-attachments/assets/2d7ccc15-2cd8-4316-bec6-ed2a1509f27b" />

This repo houses the code for the [live demo](https://scholarqa.allen.ai/) and can be run as local docker containers or embedded into another application as a [python package](https://pypi.org/project/ai2-scholar-qa).

- [Overview](#overview)
- [Setup](#setup)
  * [Environment Variables](#environment-variables)
  * [Runtime Config](#runtime-config)

- ### Overview

- ### Setup

* #### Environment Variables

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

* #### Application Configuration
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
      "decomposer_llm": "anthropic/claude-3-5-sonnet-20241022"
    }
  }
}
```

The config is used to populate the [AppConfig](https://github.com/allenai/ai2-scholarqa-lib/blob/c65c0917b64c501db397e01f34420c7167927da8/api/scholarqa/config/config_setup.py#L47) instance: 

**Logging**
```python
class LogsConfig(BaseModel):
    log_dir: str = Field(default="logs", description="Directory to store logs, event traces and litellm cache")
    llm_cache_dir: str = Field(default="llm_cache", description="Sub directory to cache llm calls")
    event_trace_loc: str = Field(default="scholarqa_traces", description="Sub directory to store event traces"
                                                                         "OR the GCS bucket name")
    tracing_mode: Literal["local", "gcs"] = Field(default="local",
                                                  description="Mode to store event traces (local or gcs)")
```
**Note:**

> i. Event Traces are json documents containing the entire trace of the
> pipeline i.e. the results of retrieval, reranking, each step of the qa
> pipeline and associated costs, if any. Please refer to the examples in
> Logging.MD
> 
> ii. llm_cache_dir is used to initialize the local disk cache for caching llm calls via [litellm](https://docs.litellm.ai/docs/caching/all_caches).
> 
> ii. The traces are stored locally in `{log_dir}/{event_trace_loc}` by
> default. They can also be persisted in a Google Cloud Storage (GCS)
> bucket. Please set the `tracing_mode="gcs"` and `event_trace_loc=<GCS
> bucket name>`  here and the `export
> GOOGLE_APPLICATION_CREDENTIALS=<Service Account Key json file path>`
> in .`env`.
> 
> iii. By default, the working directory is `./api` , so the `log_dir` will be created inside it as a sub-directory unless the config is modified.

**Pipeline**
```python
class RunConfig(BaseModel):  
retrieval_service: str = Field(default="public_api", description="Service to use for paper retrieval")  
retriever_args: dict = Field(default=None, description="Arguments for the retrieval service")  
reranker_service: str = Field(default="modal", description="Service to use for paper reranking")  
reranker_args: dict = Field(default=None, description="Arguments for the reranker service")  
paper_finder_args: dict = Field(default=None, description="Arguments for the paper finder service")  
pipeline_args: dict = Field(default=None, description="Arguments for the Scholar QA pipeline service")
```

**Note:**

> i. `*(retrieval, reranker)_service` can be used to indicate the type
> of retrieval/reranker you want to instantiate. Ai2 Scholar QA uses the
> `FullTextRetriever` and `ModalReranker`  which are chosen based on the
> default  `public_api` and `modal` keywords. To choose a #
> SentenceTransformers reranker, replace `modal` with `cross_encoder` or
> `biencoder` or define your own types.
> 
> ii. `*(retriever, reranker, paper_finder, pipeline)_args` are used to
> initialize the corresponding instances of the pipeline components. eg.
> ``retriever = FullTextRetriever(**run_config.retriever_args)``. You
> can initialize multiple runs and customize your pipeline.
>
>iii.  If the `reranker_args` are not defined, the app resorts to using only the retrieval service.

* #### docker-compose.yaml
The web app initializes 4 docker containers - one each for the API, GUI, nginx proxy and sonar with their own Dockerfile.
The api container config can also be used to declare environment variables - 
```yaml
api:  
build: ./api  
volumes:  
- ./api:/api  
- ./secret:/secret  
environment:  
# This ensures that errors are printed as they occur, which  
# makes debugging easier.  
- PYTHONUNBUFFERED=1  
- LOG_LEVEL=INFO
- CONFIG_PATH=run_configs/default.json  
ports:  
- 8000:8000  
env_file:  
- .env
```
`environment.CONFIG_PATH` indicates the path of the application configuration json file.
`env_file` indicates the path of the file with environment variables.

### Run Webapp

Please refer to [DOCKER.md](https://github.com/allenai/ai2-scholarqa-lib/blob/main/docs/DOCKER.md)
for more info on setting up the docker app.

i. Clone the repo
```bash
git clone git@github.com:allenai/ai2-scholarqa-lib.git
cd ai2-scholarqa-lib
```
ii. Run docker-compose
```bash
docker compose up --build
```

#### Startup

https://github.com/user-attachments/assets/7d6761d6-1e95-4dac-9aeb-a5a898a89fbe

### UI

https://github.com/user-attachments/assets/baed8710-2161-4fbf-b713-3a2dcf46ac61

### Backend

https://github.com/user-attachments/assets/f9a1b39f-36c8-41c4-a0ac-10046ded0593








