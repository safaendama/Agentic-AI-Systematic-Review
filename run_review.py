
"""
Run the complete 10-agent systematic review workflow
for a research topic entered by the user.

Run:
    python run_review.py
"""

import json
import re
from datetime import datetime
from pathlib import Path

from workflow import review_workflow


def create_slug(topic):
    slug = re.sub(
        r"[^a-z0-9]+",
        "_",
        topic.lower()
    ).strip("_")

    return slug[:60] or "research_review"


def main():
    print("\n" + "=" * 65)
    print("AGENTIC AI SYSTEMATIC LITERATURE REVIEW")
    print("=" * 65)

    topic = input(
        "\nEnter your research topic: "
    ).strip()

    if not topic:
        print("ERROR: Research topic cannot be empty.")
        return

    print(f"\nResearch topic: {topic}")
    print("\nStarting the complete 10-agent workflow...\n")

    # Fresh state: do not load previous XAI reports.
    initial_state = {
        "research_topic": topic,
        "review_plan": {},
        "protocol": {},
        "retrieved_papers": [],
        "deduplication_result": {},
        "enriched_papers": [],
        "rag_result": {},
        "screening_results": [],
        "screening_summary": {},
        "evidence_results": [],
        "synthesis_report": {},
        "qa_report": {},
        "prisma_report": {},
        "report_paths": {},
        "prisma_image_path": "",
        "pdf_report_path": "",
    }

    try:
        result = review_workflow.invoke(
            initial_state,
            config={
                "recursion_limit": 30
            }
        )

    except Exception as error:
        print("\nWORKFLOW FAILED")
        print(f"Error: {error}")
        raise

    print("\n" + "=" * 65)
    print("WORKFLOW EXECUTION COMPLETED")
    print("=" * 65)

    print("\nTopic:", topic)

    papers = result.get(
        "retrieved_papers"
    ) or []

    screening = result.get(
        "screening_results"
    ) or []

    evidence = result.get(
        "evidence_results"
    ) or []

    print("Retrieved records:", len(papers))
    print("Screened records:", len(screening))
    print("Evidence analyses:", len(evidence))

    pdf_path = result.get(
        "pdf_report_path"
    )

    if pdf_path and Path(pdf_path).exists():
        print("\nPDF generated:", pdf_path)
    else:
        print("\nWARNING: PDF not found.")

    # Save the final workflow state for debugging.
    output_dir = Path("data/outputs")
    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    state_file = output_dir / (
        f"workflow_state_{create_slug(topic)}_{timestamp}.json"
    )

    with open(
        state_file,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            result,
            file,
            ensure_ascii=False,
            indent=2,
            default=str
        )

    print("Workflow state:", state_file)

    print(
        "\nIMPORTANT: This is an automated preliminary "
        "review. Full-text and human validation "
        "are still required."
    )


if __name__ == "__main__":
    main()
