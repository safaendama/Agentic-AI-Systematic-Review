
import json

from agents.screening import ScreeningAgent


class FakeResponse:
    def __init__(self, decision, reason):
        self.content = json.dumps({
            "decision": decision,
            "reason": reason
        })


class FakeLLM:
    def invoke(self, prompt):
        return FakeResponse(
            "include",
            "The abstract describes empirical XAI "
            "experiments for credit risk assessment."
        )


agent = ScreeningAgent()
agent.llm = FakeLLM()

inclusion = [
    "Empirical studies published from 2019 to 2026",
    "Studies applying XAI to credit risk assessment",
    "Peer-reviewed empirical publications"
]

exclusion = [
    "Studies unrelated to credit risk",
    "Systematic reviews and literature reviews",
    "Non-peer-reviewed publications"
]

base_paper = {
    "title": "Explainable AI for Credit Risk Assessment",
    "year": 2025,
    "abstract": (
        "This empirical study evaluates SHAP and LIME "
        "for credit default prediction."
    )
}


def check(name, changes, expected):
    paper = {**base_paper, **changes}

    result = agent.screen_paper(
        paper,
        "Explainable AI for Credit Risk Assessment",
        inclusion,
        exclusion
    )

    passed = result["decision"] == expected

    print(
        f"{'PASS' if passed else 'FAIL'} | "
        f"{name}: {result['decision']}"
    )

    if not passed:
        raise AssertionError(
            f"{name}: expected {expected}, "
            f"got {result['decision']}"
        )


check(
    "OpenAlex without verified peer review",
    {"source": "OpenAlex"},
    "uncertain"
)

check(
    "arXiv without verified peer review",
    {"source": "arXiv"},
    "uncertain"
)

check(
    "Verified peer-reviewed publication",
    {
        "source": "OpenAlex",
        "peer_reviewed": True,
        "peer_review_verified": True
    },
    "include"
)

check(
    "Verified non-peer-reviewed publication",
    {
        "peer_reviewed": False,
        "peer_review_verified": True
    },
    "exclude"
)

check(
    "Secondary systematic review",
    {
        "title": "XAI for Credit Risk: A Systematic Review"
    },
    "exclude"
)

check(
    "Outside publication period",
    {"year": 2017},
    "exclude"
)

check(
    "Missing abstract",
    {"abstract": ""},
    "uncertain"
)

print("\nAll screening safeguard tests passed!")
