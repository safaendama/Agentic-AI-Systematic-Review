
from workflow import review_workflow


def main():
    topic = (
        "Explainable Artificial Intelligence "
        "for Credit Risk Assessment"
    )

    print("\nSTARTING COMPLETE SYSTEMATIC REVIEW")
    print("Research topic:", topic)

    result = review_workflow.invoke(
        {"research_topic": topic},
        config={"recursion_limit": 25}
    )

    print("\nWORKFLOW EXECUTION COMPLETED")

    print(
        "Publication range:",
        result["protocol"]["publication_start_year"],
        "-",
        result["protocol"]["publication_end_year"]
    )

    print(
        "Retrieved papers:",
        len(result["retrieved_papers"])
    )

    print(
        "Unique papers:",
        len(
            result["deduplication_result"][
                "unique_papers"
            ]
        )
    )

    print(
        "Screening summary:",
        result["screening_summary"]
    )

    print(
        "PRISMA diagram:",
        result["prisma_image_path"]
    )

    print(
        "PDF report:",
        result["pdf_report_path"]
    )


if __name__ == "__main__":
    main()
