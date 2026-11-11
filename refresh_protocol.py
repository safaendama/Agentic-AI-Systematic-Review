
import json
from pathlib import Path

from agents.protocol import ProtocolAgent


OUTPUT_PATH = Path("data/outputs/review_protocol.json")

REQUIRED_FIELDS = [
    "research_objective",
    "research_questions",
    "inclusion_criteria",
    "exclusion_criteria",
    "recommended_databases",
    "search_keywords"
]


def main():
    topic = (
        "Explainable Artificial Intelligence "
        "for Credit Risk Assessment"
    )

    print("\nRegenerating structured review protocol...")

    agent = ProtocolAgent()
    protocol = agent.generate_protocol(topic)

    missing = [
        field
        for field in REQUIRED_FIELDS
        if not protocol.get(field)
    ]

    if missing:
        raise ValueError(
            f"Protocol is incomplete. Missing: {missing}"
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Preserve the previous protocol for comparison.
    if OUTPUT_PATH.exists():
        backup = OUTPUT_PATH.with_name(
            "review_protocol_backup.json"
        )

        backup.write_bytes(OUTPUT_PATH.read_bytes())
        print("Previous protocol backed up:", backup)

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            protocol,
            file,
            indent=2,
            ensure_ascii=False
        )

    print("\nStructured protocol saved successfully!")
    print("Path:", OUTPUT_PATH)

    print("\nResearch objective:")
    print(protocol["research_objective"])

    print("\nResearch questions:")
    for index, question in enumerate(
        protocol["research_questions"],
        start=1
    ):
        print(f"{index}. {question}")

    print("\nAll required protocol fields are present.")


if __name__ == "__main__":
    main()
