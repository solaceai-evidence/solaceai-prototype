from scholarqa.rag.reranker.modal_engine import ModalReranker
from scholarqa.rag.retrieval import PaperFinderWithReranker
from scholarqa.rag.retriever_base import FullTextRetriever
from scholarqa import ScholarQA

retriever = FullTextRetriever(n_retrieval=256, n_keyword_srch=20)
reranker = ModalReranker(app_name="ai2-scholar-qa", api_name="inference_api", batch_size=256, gen_options=dict())
paper_finder = PaperFinderWithReranker(retriever, reranker, n_rerank=50, context_threshold=0.5)
scholar_qa = ScholarQA(paper_finder=paper_finder)

print(scholar_qa.answer_query("Which is the 9th planet in our solar system?"))