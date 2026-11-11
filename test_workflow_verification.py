
import json
from workflow import retrieval_node


with open(
    "data/outputs/deduplication_result.json",
    "r",
    encoding="utf-8"
) as file:
    deduplication_result = json.load(file)


result = retrieval_node({
    "deduplication_result": deduplication_result
})

papers = result["enriched_papers"]

print("\nINTEGRATION TEST SUMMARY")
print("Papers processed:", len(papers))

print(
    "Crossref records:",
    sum(
        bool(paper.get("crossref_metadata"))
        for paper in papers
    )
)

print(
    "Verification pending:",
    sum(
        paper.get("verification_status") == "pending"
        for paper in papers
    )
)

print("\nRetrieval integration test completed!")
