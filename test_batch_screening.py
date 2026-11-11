
from agents.screening import ScreeningAgent

papers = [
    {
        "title": "Explainable AI for Credit Risk Assessment",
        "year": 2025,
        "abstract": (
            "This study evaluates credit risk prediction "
            "models using SHAP and LIME to explain "
            "loan default predictions."
        )
    },
    {
        "title": "Deep Learning for Medical Image Classification",
        "year": 2024,
        "abstract": (
            "This study evaluates convolutional neural "
            "networks for medical image classification "
            "and disease detection."
        )
    },
    {
        "title": "Machine Learning in Financial Risk",
        "year": 2023,
        "abstract": ""
    }
]

inclusion_criteria = [
    "Studies published from 2015 onwards",
    "Studies focused on credit risk assessment",
    "Studies applying explainable AI techniques",
    "Empirical studies evaluating XAI methods"
]

exclusion_criteria = [
    "Studies unrelated to credit risk",
    "Studies without explainable AI techniques",
    "Purely theoretical studies without empirical evaluation"
]

agent = ScreeningAgent()

print("\nBATCH SCREENING RESULTS")
print("=" * 50)

for paper in papers:
    result = agent.screen_paper(
        paper=paper,
        research_topic=(
            "Explainable Artificial Intelligence "
            "for Credit Risk Assessment"
        ),
        inclusion_criteria=inclusion_criteria,
        exclusion_criteria=exclusion_criteria
    )

    print(f"\nTitle: {result['title']}")
    print(f"Decision: {result['decision']}")
    print(f"Reason: {result['reason']}")
    print("-" * 50)
