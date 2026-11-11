
import hashlib

from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

from rag.document_loader import DocumentLoaderAgent


class VectorStoreAgent:

    def __init__(self):
        self.embeddings = OllamaEmbeddings(
            model="nomic-embed-text"
        )

        self.persist_directory = "data/chroma_db"

    def create_vector_store(
        self,
        documents=None,
        collection_name="scientific_papers"
    ):

        if documents is None:
            loader = DocumentLoaderAgent()
            documents = loader.load_documents()

        if not documents:
            raise ValueError("No documents available for indexing.")

        vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )

        document_ids = []

        for document in documents:
            paper_id = document.metadata.get("paper_id", "")

            if not paper_id:
                paper_id = (
                    document.metadata.get("title", "")
                    + str(document.metadata.get("year", ""))
                )

            stable_id = hashlib.sha256(
                paper_id.encode("utf-8")
            ).hexdigest()

            document_ids.append(stable_id)

        vector_store.add_documents(
            documents=documents,
            ids=document_ids
        )

        return vector_store
