from langchain_community.document_loaders import PyMuPDFLoader,TextLoader,WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import Literal
class DocsLoader:
    def __init__(self,doctype:Literal["pdf",'url',"txt"],chunk_size:int=600,chunk_overlap:int=80,file_path:str = None,encoding:str =None,password:str=None):
        if not file_path:
            raise ValueError("file_path must be provided")
        self.doctype = doctype
        self.file_path = file_path
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = encoding
        self.__password = password

    def splitter(self):
        return RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=[
                        "\n# ", "\n## ", "\n### ", "\n#### ",   # Markdown headers
                        "\nChapter ", "\nSection ", "\nArticle ",  # Structured docs
                        "\n\n",        # Paragraph
                        "\n",          # Line break
                        ". ", "? ", "! ",  # Sentence endings
                        "; ", ": ",    # Semi-structured splits
                        ", ",          # Clause level
                        " ",           # Word level
                        ""             # Character fallback (always last)
                    ])

    def loader(self):
        splitter = self.splitter()
        if self.doctype =="pdf":
            loader = PyMuPDFLoader(file_path=self.file_path,password=self.__password)
        elif self.doctype =="url":
            loader = WebBaseLoader(self.file_path)
        else:
            loader = TextLoader(file_path=self.file_path,encoding=self.encoding)
        docs = splitter.split_documents(loader.load())
        return docs
