
import json

from rag.document_loader import DocumentLoaderAgent


def main():
    print("\nDOCUMENT CONVERSION TEST")
    print("-" * 50)

    with open(
        "data/outputs/retrieved_papers.json",
        "r",
        encoding="utf-8"
    ) as file:
        papers = json.load(file)

    loader = DocumentLoaderAgent()

    documents = loader.convert_papers_to_documents(papers)

    print(f"Input papers: {len(papers)}")
    print(f"Converted documents: {len(documents)}")

    if documents:
        first_document = documents[0]

        print("\nFIRST DOCUMENT")
        print(f"Title: {first_document.metadata['title']}")
        print(f"Year: {first_document.metadata['year']}")
        print(f"Source: {first_document.metadata['source']}")
        print(f"Paper ID: {first_document.metadata['paper_id']}")
        print(
            f"Abstract length: "
            f"{len(first_document.page_content)} characters"
        )

    assert len(documents) == sum(
        bool(paper.get("abstract"))
        for paper in papers
    ), "Document count does not match papers with abstracts."

    print("\nDocument conversion test PASSED!")


if __name__ == "__main__":
    main()
