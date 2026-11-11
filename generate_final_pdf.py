"""Generate a preliminary PDF from saved synthesis; no agents or API calls."""
import json
from pathlib import Path
from agents.pdf_report import PDFReportAgent

BASE = Path(__file__).resolve().parent
OUTPUTS = BASE / "data" / "outputs"
SYNTHESIS_FILE = OUTPUTS / "synthesis_report_revised.json"


def main():
    if not SYNTHESIS_FILE.is_file():
        raise FileNotFoundError(f"Missing saved synthesis: {SYNTHESIS_FILE}")

    with SYNTHESIS_FILE.open("r", encoding="utf-8") as f:
        synthesis = json.load(f)

    studies = synthesis.get("study_summaries", [])
    summary = synthesis.get("screening_summary", {})
    questions = [
        entry.get("question", "")
        for entry in synthesis.get("research_question_discussion", [])
        if isinstance(entry, dict) and entry.get("question")
    ]
    protocol = {
        "research_topic": synthesis.get("research_topic", "Systematic Literature Review"),
        "research_objective": (
            "To identify and summarize the available research evidence for the specified "
            "topic. This report is a preliminary, abstract-based synthesis."
        ),
        "research_questions": questions,
        "searched_databases": synthesis.get("searched_databases", []),
    }

    screened = summary.get("total")
    included = summary.get("provisionally_included")
    excluded = summary.get("excluded")
    uncertain = summary.get("uncertain")

    # Only use counts that can be established from saved records.
    # Search audit provides initial and duplicate counts, when available.
    audit_path = OUTPUTS / "search_audit.json"
    audit = {}
    if audit_path.is_file():
        try:
            with audit_path.open("r", encoding="utf-8") as f:
                audit = json.load(f)
            if audit.get("research_topic") != synthesis.get("research_topic"):
                print("[INFO] Search audit topic differs; identification counts omitted.")
                audit = {}
        except (ValueError, OSError) as exc:
            print(f"[INFO] Search audit unavailable: {exc}")

    prisma = {
        "records_identified": audit.get("total_records", "Not available"),
        "duplicates_removed": audit.get("duplicates_removed", "Not available"),
        "records_after_deduplication": screened if screened is not None else "Not available",
        "records_screened_title_abstract": screened if screened is not None else "Not available",
        "records_provisionally_included": included if included is not None else "Not available",
        "records_excluded_title_abstract": excluded if excluded is not None else "Not available",
        "records_uncertain": uncertain if uncertain is not None else "Not available",
        "reports_assessed_for_full_text_eligibility": "Not assessed",
        "studies_finally_included": "Not determined",
    }

    qa = {
        "limitations": [
            "The literature search was capped and does not demonstrate comprehensive coverage.",
            "Study inclusion is provisional; full-text eligibility has not been assessed.",
            "Publication and peer-review status have not been independently verified.",
            "Extracted evidence is based on available abstracts and requires source-level validation.",
            "Some studies contain automated extraction flags requiring manual review.",
        ]
    }

    agent = PDFReportAgent(output_dir=str(OUTPUTS))
    pdf = agent.generate(
        protocol=protocol,
        synthesis=synthesis,
        qa=qa,
        prisma=prisma,
        prisma_image=None,  # No unverified or stale PRISMA image.
        filename="systematic_review_revised_preliminary.pdf",
    )
    print(f"\nSUCCESS: {pdf}")
    print(f"Studies in saved synthesis: {len(studies)}")
    print("No searches, screening, or Ollama inference were executed.")


if __name__ == "__main__":
    main()
