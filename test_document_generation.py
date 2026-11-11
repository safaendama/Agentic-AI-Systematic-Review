
import json
from pathlib import Path

from workflow import document_generation_node


BASE = Path("data/outputs")
REPORTS = BASE / "reporting_test"


def load_json(path):
    if not path.exists():
        raise FileNotFoundError(
            f"Missing file: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def main():
    state = {
        "protocol": load_json(
            BASE / "review_protocol.json"
        ),
        "synthesis_report": load_json(
            REPORTS / "synthesis_report.json"
        ),
        "qa_report": load_json(
            REPORTS / "quality_assurance.json"
        ),
        "prisma_report": load_json(
            REPORTS / "prisma_preliminary.json"
        ),
        "report_paths": {}
    }

    result = document_generation_node(state)

    assert Path(
        result["prisma_image_path"]
    ).exists()

    assert Path(
        result["pdf_report_path"]
    ).exists()

    print("\nDOCUMENT GENERATION TEST")
    print("=" * 50)

    print("PRISMA diagram: PASS")
    print("PDF report: PASS")

    print("\nGenerated files:")

    for name, path in result["report_paths"].items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
