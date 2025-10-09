from solaceai import SolaceAI
from solaceai.rag.reranker.modal_engine import ModalReranker
from solaceai.rag.retrieval import PaperFinderWithReranker
from solaceai.rag.retriever_base import FullTextRetriever

retriever = FullTextRetriever(n_retrieval=256, n_keyword_srch=20)
reranker = ModalReranker(
    app_name="modal_app_name",
    api_name="modal_api_name",
    batch_size=256,
    gen_options=dict(),
)
paper_finder = PaperFinderWithReranker(
    retriever, reranker, n_rerank=50, context_threshold=0.5
)
solace_ai = SolaceAI(paper_finder=paper_finder)

print(solace_ai.answer_query("Which is the 9th planet in our solar system?"))
