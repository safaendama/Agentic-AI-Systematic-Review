
import json

from agents.publication_verification import (
    PublicationVerificationAgent
)


def main():
    with open(
        "data/outputs/enriched_papers.json",
        "r",
        encoding="utf-8"
    ) as file:
        papers = json.load(file)

    agent = PublicationVerificationAgent()

    verified_papers = agent.verify_papers(papers)

    print("\nPUBLICATION VERIFICATION SUMMARY")
    print("--------------------------------")

    print("Total papers:", len(verified_papers))

    pending = 0

    for index, paper in enumerate(verified_papers, 1):
        print(f"\nPAPER {index}")
        print("Title:", paper.get("title"))
        print(
            "Status:",
            paper.get("verification_status")
        )
        print(
            "Missing:",
            paper.get("verification_missing")
        )

        if paper["verification_status"] == "pending":
            pending += 1

    with open(
        "data/outputs/publication_verification.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            verified_papers,
            file,
            indent=2,
            ensure_ascii=False
        )

    print("\nTotal pending:", pending)
    print("Verification report saved successfully!")


if __name__ == "__main__":
    main()
