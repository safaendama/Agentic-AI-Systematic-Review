
from agents.evidence_analysis import EvidenceAnalysisAgent

agent = EvidenceAnalysisAgent(
    debug=True,
    max_attempts=3
)

paper = {
    "title": "Example Study",
    "abstract": (
        "This study evaluates a classification approach "
        "using a dataset of 500 samples. "
        "Random Forest and Logistic Regression were compared. "
        "Random Forest achieved 91% accuracy, while "
        "Logistic Regression achieved 87% accuracy. "
        "The authors identified the small sample size "
        "as a limitation."
    )
}

result = agent.analyze_paper(
    paper,
    "Machine Learning Classification"
)

print("\n========== FINAL RESULT ==========")
print("STATUS:", result["status"])

print("\nEXTRACTION:")
for key, value in result["extraction"].items():
    print(f"{key}: {value}")

print("\nQUALITY APPRAISAL:")
print(result["quality_appraisal"])
