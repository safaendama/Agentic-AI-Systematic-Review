
from agents.screening import ScreeningAgent


# Example scientific paper for testing
test_paper = {
    "title": "Explainable AI for Credit Risk Assessment",
    "year": 2025,
    "abstract": (
        "This study investigates explainable artificial "
        "intelligence techniques for credit risk assessment. "
        "Machine learning models are evaluated using "
        "SHAP and LIME to explain loan default predictions. "
        "The study examines predictive performance and "
        "model interpretability."
    )
}

# Example eligibility criteria
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

# Initialize the Screening Agent
agent = ScreeningAgent()

# Screen the paper
result = agent.screen_paper(
    paper=test_paper,
    research_topic="Explainable Artificial Intelligence for Credit Risk Assessment",
    inclusion_criteria=inclusion_criteria,
    exclusion_criteria=exclusion_criteria
)

# Display the result
print("\nSCREENING AGENT TEST")
print("=" * 45)
print(f"Title: {result['title']}")
print(f"Decision: {result['decision']}")
print(f"Reason: {result['reason']}")
