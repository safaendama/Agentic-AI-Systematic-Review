
import csv
import json
from pathlib import Path

OUTPUT_DIR = Path("data/outputs")
INPUT_FILE = OUTPUT_DIR / "screening_results.json"
OUTPUT_FILE = OUTPUT_DIR / "human_review.csv"


def main():
    with INPUT_FILE.open("r", encoding="utf-8") as file:
        screening_results = json.load(file)

    fieldnames = [
        "paper_id",
        "title",
        "year",
        "source",
        "doi",
        "venue",
        "publisher",
        "publication_type",
        "publication_url",
        "automated_decision",
        "automated_reason",
        "peer_review_verified",
        "language_verified",
        "evidence_url",
        "evidence_notes",
        "human_decision",
        "reviewer",
        "review_notes"
    ]

    rows = []

    for index, item in enumerate(screening_results, 1):
        if item.get("decision") != "uncertain":
            continue

        paper = item.get("paper", {})
        crossref = paper.get("crossref_metadata") or {}

        rows.append({
            "paper_id": index,
            "title": paper.get("title", ""),
            "year": paper.get("year", ""),
            "source": paper.get("source", ""),
            "doi": paper.get("doi", ""),
            "venue": paper.get("venue_name", ""),
            "publisher": paper.get("publisher", ""),
            "publication_type": paper.get(
                "crossref_type", ""
            ),
            "publication_url": crossref.get(
                "source_url", ""
            ),
            "automated_decision": item.get(
                "decision", ""
            ),
            "automated_reason": item.get(
                "reason", ""
            ),
            "peer_review_verified": "",
            "language_verified": "",
            "evidence_url": "",
            "evidence_notes": "",
            "human_decision": "",
            "reviewer": "",
            "review_notes": ""
        })

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )
        writer.writeheader()
        writer.writerows(rows)

    print("\nHUMAN REVIEW WORKSHEET CREATED")
    print("Papers requiring review:", len(rows))
    print("File:", OUTPUT_FILE)

    print("\nReview instructions:")
    print("1. Open the CSV in Excel.")
    print("2. Investigate each publication.")
    print("3. Record evidence URLs and notes.")
    print("4. Enter include, exclude, or uncertain.")
    print("5. Add the reviewer name.")
    print("6. Save the CSV without changing columns.")


if __name__ == "__main__":
    main()
