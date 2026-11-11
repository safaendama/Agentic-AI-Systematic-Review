
from agents.multi_source_search import MultiSourceSearchAgent
from agents.deduplication import DeduplicationAgent

topic = (
    "Explainable Artificial Intelligence for Credit Risk "
    "Assessment: Methods, Performance, and Challenges"
)

search_agent = MultiSourceSearchAgent()
deduplication_agent = DeduplicationAgent()

print("DEDUPLICATION AGENT TEST")
print("=" * 45)

papers = search_agent.search_papers(
    research_topic=topic,
    max_results=20
)

result = deduplication_agent.remove_duplicates(papers)

print("\nDEDUPLICATION RESULTS")
print("-" * 45)

print(f"Total records: {result['total_records']}")
print(f"Unique records: {result['unique_count']}")
print(f"Duplicates removed: {result['duplicate_count']}")

print("\nDUPLICATE RECORDS")

for paper in result["duplicates"]:
    print(
        f"- {paper['title']} "
        f"({paper['year']})"
    )

print("\nUNIQUE RECORDS")

for index, paper in enumerate(
    result["unique_papers"],
    start=1
):
    print(
        f"{index}. {paper['title']} "
        f"({paper['year']}) - {paper['source']}"
    )
