
from workflow import review_workflow
import json
from pathlib import Path
from datetime import datetime, timezone


def main():
    print("AGENTIC AI SYSTEMATIC REVIEW SYSTEM")
    print("=" * 45)

    topic = input("Enter your research topic: ").strip()

    if not topic:
        print("Please enter a valid research topic.")
        return

    # Initialize LangGraph state
    initial_state = {
        "research_topic": topic,
        "review_plan": {},
        "protocol": {},
        "retrieved_papers": [],
        "deduplication_result": {},
        "enriched_papers": [],
        "rag_result": {}
    }

    # Execute the complete LangGraph workflow
    result = review_workflow.invoke(initial_state)

    # Display systematic review plan
    print("\nSYSTEMATIC REVIEW PLAN")
    print("-" * 45)

    for index, stage in enumerate(
        result["review_plan"]["review_stages"], start=1
    ):
        print(f"{index}. {stage}")

    # Display research protocol
    print("\nREVIEW PROTOCOL")
    print("-" * 45)
    print(result["protocol"]["protocol_content"])

    # Display search and deduplication results
    dedup = result["deduplication_result"]

    print("\nSEARCH & DEDUPLICATION RESULTS")
    print("-" * 45)
    print(f"Total records: {dedup['total_records']}")
    print(f"Unique records: {dedup['unique_count']}")
    print(f"Duplicates removed: {dedup['duplicate_count']}")

    # Display unique papers
    print("\nUNIQUE PAPERS")
    print("-" * 45)

    for index, paper in enumerate(
        dedup["unique_papers"], start=1
    ):
        print(
            f"{index}. {paper['title']} "
            f"({paper['year']}) - {paper['source']}"
        )

    # Display enriched paper records
    print("\nENRICHED PAPER RECORDS")
    print("-" * 45)

    for index, paper in enumerate(
        result["enriched_papers"], start=1
    ):
        abstract = paper.get("abstract")

        print(f"\nPAPER {index}")
        print(f"Title: {paper['title']}")
        print(f"Source: {paper['source']}")
        print(f"Abstract available: {bool(abstract)}")

    # Create output directory
    output_dir = Path("data/outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save retrieved papers to JSON
    output_file = output_dir / "retrieved_papers.json"

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(
            result["enriched_papers"],
            file,
            indent=4,
            ensure_ascii=False
        )

    print(f"\nPapers saved to: {output_file}")

    # Create search audit record
    audit_record = {
        "research_topic": topic,
        "search_completed_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "databases_searched": [
            "OpenAlex",
            "arXiv"
        ],
        "search_input": topic,
        "max_results_per_source": 70,
        "total_records": dedup["total_records"],
        "unique_records": dedup["unique_count"],
        "duplicates_removed": dedup["duplicate_count"],
        "records_by_source": {
            "OpenAlex": sum(
                paper["source"] == "OpenAlex"
                for paper in result["retrieved_papers"]
            ),
            "arXiv": sum(
                paper["source"] == "arXiv"
                for paper in result["retrieved_papers"]
            )
        }
    }

    # Save search audit
    audit_file = output_dir / "search_audit.json"

    with open(audit_file, "w", encoding="utf-8") as file:
        json.dump(
            audit_record,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(f"Search audit saved to: {audit_file}")

    # Display RAG analysis results
    print("\n" + "=" * 60)
    print("RAG ANALYSIS RESULTS")
    print("=" * 60)

    rag_result = result.get("rag_result")

    if rag_result:
        print("\nResearch question:")
        print(rag_result["question"])

        print("\nGenerated answer:")
        print(rag_result["answer"])

        print("\nScientific references:")

        for index, paper in enumerate(
            rag_result["sources"], start=1
        ):
            print(f"\n[{index}] {paper['title']}")
            print(f"Year: {paper['year']}")
            print(f"Source: {paper['source']}")
            print(f"Paper ID: {paper['paper_id']}")
    else:
        print("No RAG result available.")

    print("\nWorkflow executed successfully!")


if __name__ == "__main__":
    main()
