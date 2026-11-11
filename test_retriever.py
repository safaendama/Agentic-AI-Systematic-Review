
from rag.retriever import ResearchRetriever


def main():
    print("\nRESEARCH RETRIEVER TEST")
    print("-" * 50)

    retriever = ResearchRetriever()

    question = (
        "What explainable AI methods are used "
        "in credit risk assessment?"
    )

    print(f"\nResearch question: {question}")

    evidence = retriever.retrieve_evidence(
        research_question=question,
        k=3
    )

    print(f"\nTotal evidence retrieved: {len(evidence)}")

    for index, paper in enumerate(evidence, start=1):
        print(f"\n{'-' * 50}")
        print(f"PAPER {index}")
        print(f"Title: {paper['title']}")
        print(f"Year: {paper['year']}")
        print(f"Source: {paper['source']}")
        print(f"Paper ID: {paper['paper_id']}")
        print(f"Distance: {paper['distance']:.4f}")
        print(f"Abstract preview: {paper['abstract'][:200]}...")


if __name__ == "__main__":
    main()
