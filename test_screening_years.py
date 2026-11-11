
from agents.screening import ScreeningAgent


agent = ScreeningAgent()

inclusion = [
    "Peer-reviewed empirical studies published "
    "in English from 2022 to 2026",
    "Studies applying XAI to credit risk assessment"
]

exclusion = [
    "Studies published outside 2022 to 2026",
    "Secondary reviews and meta-analyses",
    "Preprints without verified peer-reviewed publication"
]


def test_paper(year, expected):

    paper = {
        "title": "Explainable AI for Credit Risk",
        "year": year,
        "abstract": (
            "An empirical study applying SHAP "
            "to credit default prediction."
        )
    }

    result = agent.screen_paper(
        paper=paper,
        research_topic=(
            "Explainable Artificial Intelligence "
            "for Credit Risk Assessment"
        ),
        inclusion_criteria=inclusion,
        exclusion_criteria=exclusion
    )

    assert result["decision"] == expected, (
        f"Year {year}: expected {expected}, "
        f"got {result['decision']}"
    )

    print(
        f"Year {year}: "
        f"{result['decision'].upper()} — PASS"
    )


def main():

    # These are outside the allowed range.
    # The agent should reject them before
    # invoking the language model.

    test_paper(2019, "exclude")
    test_paper(2020, "exclude")
    test_paper(2021, "exclude")

    print("\nYear limits:", agent._year_limits(inclusion))

    assert agent._year_limits(inclusion) == (
        2022,
        2026
    )

    print("\nSCREENING YEAR TESTS PASSED!")


if __name__ == "__main__":
    main()
