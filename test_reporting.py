
import json
from pathlib import Path

from agents.review_reporting import ReviewReportingAgent


OUTPUT_DIR = Path("data/outputs")


def load_json(filename, required=True):
    path = OUTPUT_DIR / filename

    if not path.exists():
        if required:
            raise FileNotFoundError(
                f"Missing file: {path}"
            )
        return None

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def main():
    print("\nLOADING PREVIOUS WORKFLOW RESULTS")
    print("=" * 50)

    protocol = load_json("review_protocol.json")
    screening = load_json("screening_results.json")
    evidence = load_json("evidence_results.json")

    retrieved = load_json(
        "retrieved_papers.json",
        required=False
    )

    dedup = load_json(
        "deduplication_result.json",
        required=False
    )

    # Reconstruct unique records from the papers
    # actually passed to screening.
    screened_papers = [
        item["paper"]
        for item in screening
    ]

    if dedup is None:
        print(
            "Deduplication JSON not found. "
            "Using screened records as the "
            "post-deduplication set."
        )

        dedup = {
            "unique_papers": screened_papers,
            "reconstructed_for_test": True
        }

    # We cannot infer how many records were originally
    # identified if the retrieval file is unavailable.
    # Avoid inventing identification counts.
    if retrieved is None:
        print(
            "\nRetrieved papers JSON is missing."
        )
        print(
            "Original identification counts cannot "
            "be verified from saved files."
        )
        print(
            "Reporting test will use screened papers "
            "as temporary input, with identification "
            "counts marked as unavailable."
        )

        retrieved = screened_papers
        identification_counts_unverified = True
    else:
        identification_counts_unverified = False

    state = {
        "research_topic": protocol.get(
            "research_topic",
            "Unknown research topic"
        ),
        "protocol": protocol,
        "retrieved_papers": retrieved,
        "deduplication_result": dedup,
        "screening_results": screening,
        "evidence_results": evidence
    }

    agent = ReviewReportingAgent(
        output_dir="data/outputs/reporting_test"
    )

    result = agent.run(state)

    prisma = result["prisma_report"]

    # When identification records were unavailable,
    # do not present reconstructed counts as actual
    # identification counts.
    if identification_counts_unverified:
        prisma["records_identified"] = None
        prisma["duplicates_removed"] = None

        prisma["note"] += (
            " Original identification and duplicate "
            "counts could not be reconstructed."
        )

        agent.save(
            "prisma_preliminary.json",
            prisma
        )

    print("\nREPORTING TEST RESULTS")
    print("=" * 50)

    print(
        "Identified:",
        prisma["records_identified"]
    )
    print(
        "Duplicates removed:",
        prisma["duplicates_removed"]
    )
    print(
        "Screened:",
        prisma["records_screened_title_abstract"]
    )
    print(
        "Provisionally included:",
        prisma["records_provisionally_included"]
    )
    print(
        "Excluded:",
        prisma["records_excluded_title_abstract"]
    )
    print(
        "Uncertain:",
        prisma["records_uncertain"]
    )
    print(
        "Finally included:",
        prisma["studies_finally_included"]
    )

    print("\nGenerated reports:")

    for name, path in result["report_paths"].items():
        print(f"{name}: {path}")

    print("\nReporting test completed successfully!")


if __name__ == "__main__":
    main()
