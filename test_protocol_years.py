
from agents.protocol import ProtocolAgent


def main():

    topic = (
        "Explainable Artificial Intelligence "
        "for Credit Risk Assessment"
    )

    agent = ProtocolAgent(
        start_year=2022,
        end_year=2026,
        language="English"
    )

    protocol = agent.generate_protocol(
        topic
    )

    print("\n" + "=" * 60)
    print("PROTOCOL YEAR VALIDATION")
    print("=" * 60)

    print(
        "Publication range:",
        protocol["publication_start_year"],
        "to",
        protocol["publication_end_year"]
    )

    print(
        "\nINCLUSION CRITERIA:"
    )

    for item in protocol["inclusion_criteria"]:
        print("-", item)

    print(
        "\nEXCLUSION CRITERIA:"
    )

    for item in protocol["exclusion_criteria"]:
        print("-", item)

    assert (
        protocol["publication_start_year"]
        == 2022
    )

    assert (
        protocol["publication_end_year"]
        == 2026
    )

    print(
        "\nTEST PASSED: Publication range "
        "is 2022–2026."
    )


if __name__ == "__main__":
    main()
