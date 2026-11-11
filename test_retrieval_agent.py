
from agents.search import SearchAgent
from agents.retrieval import RetrievalAgent

topic = "Explainable Artificial Intelligence for Credit Risk Assessment"

search_agent = SearchAgent()
retrieval_agent = RetrievalAgent()

print("RETRIEVAL AGENT TEST")
print("=" * 45)

papers = search_agent.search_papers(
    research_topic=topic,
    max_results=2
)

for index, paper in enumerate(papers, start=1):
    details = retrieval_agent.retrieve_paper(
        paper["openalex_id"]
    )

    print(f"\nPAPER {index}")
    print(f"Title: {details['title']}")
    print(f"Year: {details['year']}")
    print(f"Publication date: {details['publication_date']}")
    print(f"Type: {details['type']}")
    print(f"Citations: {details['cited_by_count']}")
    print(f"DOI: {details['doi']}")

    if details["abstract"]:
        print(f"Abstract: {details['abstract'][:500]}...")
    else:
        print("Abstract: Not available in OpenAlex")

    print("-" * 45)
