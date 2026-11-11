
from collections import Counter

from agents.multi_source_search import MultiSourceSearchAgent
from agents.deduplication import DeduplicationAgent
from agents.publication_verification import PublicationVerificationAgent


topic = (
    "Explainable Artificial Intelligence for Credit Risk "
    "Assessment: Methods, Performance, and Challenges"
)

search_agent = MultiSourceSearchAgent()
deduplication_agent = DeduplicationAgent()
verification_agent = PublicationVerificationAgent()

print("\nSTEP 5 — PUBLICATION VERIFICATION TEST")
print("=" * 50)

# Step 3: Search
papers = search_agent.search_papers(
    research_topic=topic,
    max_results=20
)

# Step 4: Deduplication
deduplication_result = (
    deduplication_agent.remove_duplicates(papers)
)

unique_papers = deduplication_result["unique_papers"]

# Step 5: Verification
verified_papers = verification_agent.verify_papers(
    unique_papers
)

print("\nFINAL VERIFICATION RESULTS")
print("=" * 50)

print("Retrieved:", len(papers))
print("Unique:", len(unique_papers))
print("Verified records processed:", len(verified_papers))

crossref_counts = Counter(
    paper.get("crossref_lookup_status")
    for paper in verified_papers
)

title_counts = Counter(
    paper.get("title_match_status")
    for paper in verified_papers
)

print("\nCrossref lookup results:")
for status, count in crossref_counts.items():
    print(f"  {status}: {count}")

print("\nTitle comparison results:")
for status, count in title_counts.items():
    print(f"  {status}: {count}")

print("\nPapers needing title review:")
for paper in verified_papers:
    if paper.get("title_match_status") == "needs_review":
        print("-", paper.get("title"))
