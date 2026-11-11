
from rag.answer_generator import RAGAnswerGenerator


def main():
    print("\nRAG ANSWER GENERATOR TEST")
    print("-" * 50)

    generator = RAGAnswerGenerator()

    question = (
        "What explainable AI methods are used "
        "in credit risk assessment?"
    )

    print(f"\nResearch question: {question}")
    print("\nRetrieving evidence and generating answer...")

    result = generator.generate_answer(
        research_question=question,
        k=3
    )

    print("\nGENERATED ANSWER")
    print("-" * 50)
    print(result["answer"])

    print("\nREFERENCES")
    print("-" * 50)

    for index, paper in enumerate(result["sources"], start=1):
        print(f"\n[{index}] {paper['title']}")
        print(f"Year: {paper['year']}")
        print(f"Source: {paper['source']}")
        print(f"Paper ID: {paper['paper_id']}")

    print(f"\nTotal sources used: {len(result['sources'])}")


if __name__ == "__main__":
    main()
