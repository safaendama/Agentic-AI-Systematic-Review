
from agents.evidence_analysis import EvidenceAnalysisAgent

paper = {
    "title": "Test of explainable credit risk models",
    "abstract": (
        "This study compares Random Forest and Decision Tree "
        "models for credit risk prediction using a dataset of "
        "10000 loan applications. Random Forest achieved "
        "93% accuracy, whereas Decision Tree achieved 89% "
        "accuracy. SHAP was used to explain predictions. "
        "The authors identified limited external validation "
        "as a limitation."
    )
}

agent = EvidenceAnalysisAgent()
result = agent.analyze_paper(
    paper,
    "Explainable AI for Credit Risk Assessment"
)

import json
print(json.dumps(result, indent=2, ensure_ascii=False))
