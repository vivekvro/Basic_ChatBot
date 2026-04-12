from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from typing import List,Literal,Any

from RAG.loadforDoc import DocsLoader
from RAG.embeddings import EmbeddingSentenceTransformermpnet



def FaissRetriever(doctype: Literal['pdf','url', 'txt'],
    chunk_size: int = 600,
    chunk_overlap: int = 80,
    file_path: str = None,
    encoding: str = None,
    password: str=None,
    topk=14):

    docload = DocsLoader(
        doctype=doctype,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        file_path=file_path,
        encoding=encoding,
        password=password)
    vecStore = FAISS.from_documents(
        documents=docload.loader(),
        embedding = EmbeddingSentenceTransformermpnet()
    )
    return vecStore.as_retriever(search_kwargs={'k':topk})


def get_retrieverContent(docs):
    return "\n\n".join([doc.page_content for doc in docs])






