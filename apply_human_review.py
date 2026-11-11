"""Apply researcher-approved screening decisions without overwriting provisional results.
Run from the project root: python apply_human_review.py
"""
import csv
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

OUTPUT_DIR = Path("data/outputs")
REVIEW_CSV = OUTPUT_DIR / "human_review_proposals.csv"
SCREENING_JSON = OUTPUT_DIR / "screening_results.json"
VALID = {"include", "exclude", "uncertain"}

def main():
    with SCREENING_JSON.open(encoding="utf-8") as f:
        original = json.load(f)
    with REVIEW_CSV.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    expected = {i for i, item in enumerate(original, 1) if item["decision"] == "uncertain"}
    seen = set()
    approved = {}
    for row in rows:
        try:
            i = int(row["paper_id"])
        except (ValueError, TypeError):
            raise ValueError("Every row must have a valid integer paper_id")
        if i not in expected or i in seen:
            raise ValueError(f"Unexpected or duplicate paper_id: {i}")
        seen.add(i)
        if row.get("title", "").strip() != original[i-1]["paper"]["title"]:
            raise ValueError(f"Title mismatch for paper {i}")
        decision = (row.get("human_decision") or "").strip().lower()
        reviewer = (row.get("reviewer") or "").strip()
        notes = (row.get("review_notes") or "").strip()
        evidence = (row.get("evidence_url") or "").strip()
        if decision and decision not in VALID:
            raise ValueError(f"Invalid human_decision for paper {i}: {decision}")
        if decision and (not reviewer or not notes):
            raise ValueError(f"Paper {i}: enter reviewer and review_notes for any decision")
        if decision == "include" and (not evidence.startswith(("https://", "http://"))):
            raise ValueError(f"Paper {i}: inclusion requires a supporting evidence_url")
        if decision:
            approved[i] = (decision, row)
    if seen != expected:
        raise ValueError(f"Missing review rows: {sorted(expected - seen)}")
    if not approved:
        print("No human decisions entered. Nothing finalized; no files changed.")
        return
    result = deepcopy(original)
    now = datetime.now(timezone.utc).isoformat()
    for i, (decision, row) in approved.items():
        item = result[i-1]
        item["automated_decision"] = item["decision"]
        item["automated_reason"] = item["reason"]
        item["decision"] = decision
        item["reason"] = (row.get("review_notes") or "").strip()
        item["screening_status"] = "human_reviewed"
        item["requires_human_review"] = decision == "uncertain"
        item["human_review"] = {
            "reviewer": row["reviewer"].strip(),
            "reviewed_at": now,
            "decision": decision,
            "evidence_url": (row.get("evidence_url") or "").strip(),
            "evidence_notes": (row.get("evidence_notes") or "").strip(),
            "review_notes": row["review_notes"].strip(),
            "evidence_category": (row.get("evidence_category") or "").strip(),
            "protocol_amendment": "Preprints may be supplementary; original empirical studies only"
        }
    summary = {
        "total": len(result),
        "included": sum(x["decision"] == "include" for x in result),
        "excluded": sum(x["decision"] == "exclude" for x in result),
        "uncertain": sum(x["decision"] == "uncertain" for x in result),
        "human_reviewed": len(approved),
        "human_review_pending": len(expected) - len(approved),
        "status": "partially_reviewed" if len(approved) < len(expected) else "human_reviewed_with_original_exclusions_provisional",
        "requires_human_review": True,
        "note": "Original exclusions remain provisional; preprints must be labeled separately in synthesis."
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for filename, value in (("screening_results_human_reviewed.json", result), ("screening_summary_human_reviewed.json", summary)):
        with (OUTPUT_DIR / filename).open("w", encoding="utf-8") as f:
            json.dump(value, f, indent=2, ensure_ascii=False)
    print("Human-reviewed screening results saved (original files unchanged).")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
