
from rag.vector_store import VectorStoreAgent


class ResearchRetriever:

    def __init__(
        self,
        documents=None,
        collection_name="scientific_papers"
    ):
        self.vector_store = VectorStoreAgent().create_vector_store(
            documents=documents,
            collection_name=collection_name
        )

    def retrieve_evidence(self, research_question, k=3):
        results = self.vector_store.similarity_search_with_score(
            research_question,
            k=k
        )

        evidence = []

        for document, distance in results:
            evidence.append({
                "title": document.metadata.get("title", ""),
                "year": document.metadata.get("year", ""),
                "source": document.metadata.get("source", ""),
                "paper_id": document.metadata.get("paper_id", ""),
                "abstract": document.page_content,
                "distance": float(distance)
            })

        return evidence
