
import json
from pathlib import Path

from agents.retrieval import RetrievalAgent
from agents.publication_verification import (
    PublicationVerificationAgent
)


def main():
    output_dir = Path("data/outputs")
    input_path = output_dir / "enriched_papers.json"

    with input_path.open("r", encoding="utf-8") as file:
        papers = json.load(file)

    retrieval_agent = RetrievalAgent()
    verification_agent = PublicationVerificationAgent()

    updated_papers = []

    for index, paper in enumerate(papers, 1):
        print(
            f"\nProcessing paper {index}/{len(papers)}"
        )
        print("Title:", paper.get("title"))

        updated = paper.copy()

        openalex_id = paper.get("openalex_id")

        if openalex_id:
            try:
                metadata = retrieval_agent.retrieve_paper(
                    openalex_id
                )

                # Preserve existing fields when OpenAlex
                # does not return a value.
                for key, value in metadata.items():
                    if value is not None:
                        updated[key] = value

                print(
                    "Venue:",
                    updated.get("venue_name")
                )

            except Exception as error:
                print(
                    "Metadata retrieval failed:",
                    error
                )

        updated = verification_agent.verify_paper(
            updated
        )

        updated_papers.append(updated)

    output_path = (
        output_dir / "enriched_papers_verified.json"
    )

    with output_path.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            updated_papers,
            file,
            indent=2,
            ensure_ascii=False
        )

    print("\nMETADATA REFRESH COMPLETED")
    print("Papers processed:", len(updated_papers))
    print("Saved to:", output_path)


if __name__ == "__main__":
    main()
