
import json

from agents.retrieval import RetrievalAgent


def main():
    agent = RetrievalAgent()

    with open(
        "data/outputs/enriched_papers.json",
        "r",
        encoding="utf-8"
    ) as file:
        papers = json.load(file)

    openalex_papers = [
        paper
        for paper in papers
        if paper.get("openalex_id")
    ]

    if not openalex_papers:
        print("No OpenAlex papers found.")
        return

    paper = openalex_papers[0]

    print("Testing retrieval for:")
    print(paper.get("title"))

    result = agent.retrieve_paper(
        paper["openalex_id"]
    )

    print("\nPUBLICATION METADATA")
    print("---------------------")

    fields = [
        "title",
        "year",
        "doi",
        "venue_name",
        "venue_type",
        "venue_issn",
        "publication_version",
        "language",
        "language_verified",
        "peer_reviewed",
        "peer_review_verified",
        "verification_status",
    ]

    for field in fields:
        print(f"{field}: {result.get(field)}")

    print("\nRetrieval verification test completed!")


if __name__ == "__main__":
    main()
