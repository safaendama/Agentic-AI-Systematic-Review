
import json

from agents.publication_verification import (
    PublicationVerificationAgent
)


def main():
    with open(
        "data/outputs/enriched_papers_verified.json",
        "r",
        encoding="utf-8"
    ) as file:
        papers = json.load(file)

    agent = PublicationVerificationAgent()

    results = agent.verify_papers(papers)

    with open(
        "data/outputs/publication_verification_crossref.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            results,
            file,
            indent=2,
            ensure_ascii=False
        )

    print("\nCROSSREF INTEGRATION SUMMARY")

    for index, paper in enumerate(results, 1):
        print(f"\nPAPER {index}")
        print("Title:", paper.get("title"))
        print("Venue:", paper.get("venue_name"))
        print("Publisher:", paper.get("publisher"))
        print(
            "Crossref type:",
            paper.get("crossref_type")
        )
        print(
            "Verification status:",
            paper.get("verification_status")
        )

    print("\nIntegration test completed!")


if __name__ == "__main__":
    main()
