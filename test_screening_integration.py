
import json

from workflow import screening_node


def load_json(filename):
    with open(
        f"data/outputs/{filename}",
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def main():
    protocol = load_json("review_protocol.json")
    papers = load_json("enriched_papers.json")

    state = {
        "research_topic": (
            "Explainable Artificial Intelligence "
            "for Credit Risk Assessment"
        ),
        "protocol": protocol,
        "enriched_papers": papers
    }

    result = screening_node(state)

    summary = result["screening_summary"]

    print("\nSCREENING INTEGRATION TEST")
    print("Total:", summary["total"])
    print("Included:", summary["included"])
    print("Excluded:", summary["excluded"])
    print("Uncertain:", summary["uncertain"])
    print("Status:", summary["status"])

    assert (
        summary["total"]
        == summary["included"]
        + summary["excluded"]
        + summary["uncertain"]
    )

    print("\nScreening integration test passed!")


if __name__ == "__main__":
    main()
