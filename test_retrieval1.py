
from collections import Counter

from agents.multi_source_search import MultiSourceSearchAgent
from agents.deduplication import DeduplicationAgent
from agents.publication_verification import PublicationVerificationAgent
from agents.retrieval import RetrievalAgent


topic = (
    "Explainable Artificial Intelligence for Credit Risk "
    "Assessment: Methods, Performance, and Challenges"
)

search_agent = MultiSourceSearchAgent()
deduplication_agent = DeduplicationAgent()
verification_agent = PublicationVerificationAgent()
retrieval_agent = RetrievalAgent()

print("\nSTEP 6 — RETRIEVAL TEST")
print("=" * 50)

# STEP 3 — Search
papers = search_agent.search_papers(
    research_topic=topic,
    max_results=20
)

# STEP 4 — Deduplication
deduplication_result = (
    deduplication_agent.remove_duplicates(papers)
)

unique_papers = deduplication_result["unique_papers"]

# STEP 5 — Publication verification
verified_papers = verification_agent.verify_papers(
    unique_papers
)

# STEP 6 — Metadata retrieval and enrichment
enriched_papers = retrieval_agent.enrich_papers(
    verified_papers
)

print("\nFINAL RETRIEVAL RESULTS")
print("=" * 50)

print("Retrieved:", len(papers))
print("Unique:", len(unique_papers))
print("Verified records processed:", len(verified_papers))
print("Enriched records:", len(enriched_papers))

print(
    "Papers with abstracts:",
    sum(bool(p.get("abstract")) for p in enriched_papers)
)

print(
    "Papers without abstracts:",
    sum(not bool(p.get("abstract")) for p in enriched_papers)
)

print("\nRecords by source:")
for source, count in Counter(
    p.get("source", "Unknown") for p in enriched_papers
).items():
    print(f"  {source}: {count}")

print("\nRetrieval errors:")
errors = [
    p for p in enriched_papers
    if p.get("retrieval_error")
]

if errors:
    for paper in errors:
        print(
            "-",
            paper.get("title"),
            "|",
            paper.get("retrieval_error")
        )
else:
    print("None")

# Verify that no records were lost.
assert len(enriched_papers) == len(unique_papers), (
    "Error: Paper count changed during enrichment."
)

print("\nTEST COMPLETED SUCCESSFULLY")
