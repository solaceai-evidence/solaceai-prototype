# Overview
The [ai2-scholar-qa-reranker.py](https://github.com/allenai/ai2-scholarqa-lib/blob/main/api/scholarqa/rag/reranker/ai2-scholar-qa-reranker.py)
script provides sample code for creating a modal image to deploy a reranker model.
The scripts include code for downloading the model from HuggingFace, and creating
a basic image. They then define up to three containers:
1. The Model class. This is the one that runs on GPUs and does the actual inference,
and will always be present.
2. A deployed function endpoint. This can be called directly from client code using the
modal python package.

# Working with Modal

## Getting set up

See https://modal.com/docs/guide for instructions on setting up an account at modal.com
and installing the modal Python package. This will create a .modal.toml file in your
home directory with your auth token_id and token_secret from your account setup.

The resulting .toml file should look something like the following,
substitutuing actual token and secret values:
```
[user]
token_id = "ak-*[...]*"
token_secret = "as-*[...]*"

active = true
```

## Launching an app

You can test your code with
`modal run <script>.py`, it runs on modal as an ephermal app and is not deployed.

To deploy your api, use `modal deploy <script>.py`, e.g.

## Calling the app:

Once deployed, you can use the `app_name` and `api_name` and create an instance of [ModalEngine](https://github.com/allenai/ai2-scholarqa-lib/blob/21336d381f73f46d5896f6fcc78d678eb21034a3/api/scholarqa/rag/reranker/modal_engine.py#L25),
and call the api with `generate()`.


