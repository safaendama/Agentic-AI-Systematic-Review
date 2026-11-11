
import json
from pathlib import Path

from agents.pdf_report import PDFReportAgent


BASE = Path("data/outputs")
REPORTS = BASE / "reporting_test"


def load_json(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def main():
    protocol = load_json(BASE / "review_protocol.json")
    synthesis = load_json(REPORTS / "synthesis_report.json")
    qa = load_json(REPORTS / "quality_assurance.json")
    prisma = load_json(REPORTS / "prisma_preliminary.json")

    prisma_image = REPORTS / "prisma_flow.png"

    agent = PDFReportAgent(output_dir=REPORTS)

    pdf_path = agent.generate(
        protocol=protocol,
        synthesis=synthesis,
        qa=qa,
        prisma=prisma,
        prisma_image=prisma_image
    )

    print("\nPDF REPORT TEST")
    print("=" * 50)
    print("PDF generated successfully!")
    print("Saved to:", pdf_path)


if __name__ == "__main__":
    main()
