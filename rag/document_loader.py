
import json
from pathlib import Path
from langchain_core.documents import Document


class DocumentLoaderAgent:

    def load_documents(self, file_path="data/outputs/retrieved_papers.json"):

        path = Path(file_path)

        with open(path, "r", encoding="utf-8") as file:
            papers = json.load(file)

        documents = []

        for paper in papers:
            abstract = paper.get("abstract", "")

            if not abstract:
                continue

            document = Document(
                page_content=abstract,
                metadata={
                    "title": paper.get("title", ""),
                    "year": paper.get("year", ""),
                    "source": paper.get("source", ""),
                    "doi": paper.get("doi") or "",
                    "paper_id": (
                        paper.get("openalex_id")
                        or paper.get("arxiv_id")
                        or ""
                    )
                }
            )

            documents.append(document)

        return documents

    
    def convert_papers_to_documents(self, papers):
        documents = []

        for paper in papers:
            abstract = paper.get("abstract", "")

            if not abstract:
                continue

            document = Document(
                page_content=abstract,
                metadata={
                    "title": paper.get("title", ""),
                    "year": paper.get("year") or 0,
                    "source": paper.get("source", ""),
                    "doi": paper.get("doi") or "",
                    "paper_id": (
                        paper.get("openalex_id")
                        or paper.get("arxiv_id")
                        or ""
                    )
                }
            )

            documents.append(document)

        return documents
