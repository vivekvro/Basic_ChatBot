from langchain_huggingface import HuggingFaceEmbeddings

def EmbeddingSentenceTransformermpnet():
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
