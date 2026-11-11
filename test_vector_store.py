
from rag.vector_store import VectorStoreAgent


def main():
    print("\nVECTOR STORE TEST")
    print("-" * 40)

    agent = VectorStoreAgent()

    print("Loading documents and generating embeddings...")

    vector_store = agent.create_vector_store()

    print("Vector database created successfully!")

    # Check how many documents are stored
    total_documents = vector_store._collection.count()

    print(f"Total indexed documents: {total_documents}")

    # Test semantic search
    query = "Which explainable AI methods are used in credit risk assessment?"

    print(f"\nSearch question: {query}")

    results = vector_store.similarity_search(
        query,
        k=3
    )

    print("\nTOP 3 RELEVANT PAPERS")
    print("-" * 40)

    for index, document in enumerate(results, start=1):
        print(f"\nPaper {index}")
        print(f"Title: {document.metadata['title']}")
        print(f"Source: {document.metadata['source']}")
        print(f"Abstract preview: {document.page_content[:200]}...")


if __name__ == "__main__":
    main()
