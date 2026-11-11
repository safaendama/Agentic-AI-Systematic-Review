
import json
from pathlib import Path

from agents.screening import ScreeningAgent


RESEARCH_TOPIC = (
    "Explainable Artificial Intelligence "
    "for Credit Risk Assessment"
)

# Provisional criteria for this validation test.
# They must be approved before final review decisions.
INCLUSION_CRITERIA = [
    "Original empirical studies published from 2019 to 2026",
    "Studies written in English",
    "Studies applying explainable AI methods to credit risk assessment",
    "Studies reporting actual empirical methods and results",
    "Peer-reviewed research publications"
]

EXCLUSION_CRITERIA = [
    "Studies unrelated to credit risk assessment",
    "Studies without explainable AI methods",
    "Systematic reviews, literature reviews, scoping reviews, "
    "and meta-analyses",
    "Theoretical or proposed studies without empirical validation",
    "Non-peer-reviewed publications"
]


def main():
    input_path = Path("data/outputs/retrieved_papers.json")

    if not input_path.exists():
        raise FileNotFoundError(
            f"File not found: {input_path}"
        )

    with open(input_path, "r", encoding="utf-8") as file:
        papers = json.load(file)

    if isinstance(papers, dict):
        papers = papers.get(
            "papers",
            papers.get("retrieved_papers", [])
        )

    if not isinstance(papers, list):
        raise ValueError(
            "Retrieved papers must be stored as a list."
        )

    agent = ScreeningAgent()
    results = []

    print("\nSCREENING VALIDATION TEST")
    print("=" * 55)

    for index, paper in enumerate(papers, start=1):
        print(f"\nScreening paper {index}/{len(papers)}")

        result = agent.screen_paper(
            paper=paper,
            research_topic=RESEARCH_TOPIC,
            inclusion_criteria=INCLUSION_CRITERIA,
            exclusion_criteria=EXCLUSION_CRITERIA
        )

        results.append({
            "paper": paper,
            "decision": result["decision"],
            "reason": result["reason"]
        })

        print("Title:", result["title"])
        print("Decision:", result["decision"])
        print("Reason:", result["reason"])

    summary = {
        "total": len(results),
        "included": sum(
            r["decision"] == "include" for r in results
        ),
        "excluded": sum(
            r["decision"] == "exclude" for r in results
        ),
        "uncertain": sum(
            r["decision"] == "uncertain" for r in results
        )
    }

    output_path = Path(
        "data/outputs/screening_validation_test.json"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(
            {
                "research_topic": RESEARCH_TOPIC,
                "criteria_status": "provisional",
                "summary": summary,
                "results": results
            },
            file,
            indent=4,
            ensure_ascii=False
        )

    print("\nFINAL SCREENING SUMMARY")
    print("=" * 55)
    print(summary)
    print("\nSaved to:", output_path)


if __name__ == "__main__":
    main()
