from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from sentence_transformers import CrossEncoder

app = FastAPI()
model = CrossEncoder("mixedbread-ai/mxbai-rerank-large-v1", trust_remote_code=True)


class RerankRequest(BaseModel):
    query: str
    passages: List[str]


class RerankResponse(BaseModel):
    scores: List[float]


@app.post("/rerank", response_model=RerankResponse)
def rerank(req: RerankRequest):
    pairs = [[req.query, passage] for passage in req.passages]
    scores = model.predict(pairs).tolist()
    return RerankResponse(scores=scores)
