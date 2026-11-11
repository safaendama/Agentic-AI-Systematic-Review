
from agents.review_reporting import ReviewReportingAgent

agent = ReviewReportingAgent()

state = {
    "research_topic": "Machine Learning Classification",

    "protocol": {
        "status": "draft",
        "research_questions": [
            "Which classification methods are used?",
            "What evaluation metrics are reported?",
            "What comparative findings are reported?",
        ],
    },

    "screening_results": [
        {"decision": "include"},
        {"decision": "include"},
    ],

    "retrieved_papers": [
        {"title": "Example Study"},
        {"title": "Example Study 2"},
    ],

    "deduplication_result": {
        "unique_papers": [
            {"title": "Example Study"},
            {"title": "Example Study 2"},
        ],
    },

    "evidence_results": [
        {
            "paper": {
                "title": "Example Study",
                "year": 2026,
                "abstract": (
                    "Random Forest achieved 91% "
                    "accuracy compared with 87% "
                    "for Logistic Regression."
                ),
            },
            "analysis": {
                "status": "analyzed",
                "extraction": {
                    "method_names": [
                        "Random Forest",
                        "Logistic Regression",
                    ],
                    "dataset": "500 samples",
                    "evaluation_metrics": "Accuracy",
                    "main_findings": (
                        "Random Forest achieved "
                        "91% accuracy."
                    ),
                    "quantitative_results": [
                        "91% accuracy",
                        "87% accuracy",
                    ],
                    "reported_comparisons": [
                        "Random Forest 91% versus "
                        "Logistic Regression 87%"
                    ],
                },
                "quality_appraisal": {
                    "rating": "preliminary_only",
                    "concerns": [],
                },
                "requires_full_text_review": True,
            },
        },
        {
            "paper": {
                "title": "Example Study 2",
                "year": 2026,
                "abstract": (
                    "This paper investigates "
                    "classification."
                ),
            },
            "analysis": {
                "status": "manual_review_required",
                "extraction": {
                    "evidence_snippets": [
                        "This paper investigates "
                        "classification."
                    ],
                },
                "quality_appraisal": {
                    "rating": "not_assessable",
                    "concerns": [
                        "Structured extraction failed."
                    ],
                },
                "requires_full_text_review": True,
            },
        },
    ],
}

result = agent.run(state)

print("\n===== REPORTING TEST =====")
print(
    "Total records:",
    len(
        result["synthesis_report"][
            "study_summaries"
        ]
    ),
)

print(
    "Structured evidence:",
    result["qa_report"][
        "records_with_structured_evidence"
    ],
)

print(
    "Missing structured evidence:",
    result["qa_report"][
        "records_without_structured_evidence"
    ],
)

for item in result["synthesis_report"][
    "research_question_discussion"
]:
    print("\nRQ:", item["question"])
    print(
        "Supporting studies:",
        len(item["supporting_studies"]),
    )
