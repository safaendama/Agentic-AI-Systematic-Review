
from rag.document_loader import DocumentLoaderAgent


def main():
    loader = DocumentLoaderAgent()

    documents = loader.load_documents()

    print("\nDOCUMENT LOADER TEST")
    print("-" * 40)

    print(f"Total documents loaded: {len(documents)}")

    if documents:
        first_document = documents[0]

        print("\nFIRST DOCUMENT")
        print(f"Title: {first_document.metadata['title']}")
        print(f"Year: {first_document.metadata['year']}")
        print(f"Source: {first_document.metadata['source']}")
        print(f"Abstract length: {len(first_document.page_content)} characters")
        print(f"Abstract preview: {first_document.page_content[:200]}...")


if __name__ == "__main__":
    main()
