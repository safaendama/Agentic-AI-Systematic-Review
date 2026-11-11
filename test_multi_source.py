
from agents.multi_source_search import MultiSourceSearchAgent

agent = MultiSourceSearchAgent()

topic = "Explainable AI Credit Risk"

print("MULTI-SOURCE SEARCH TEST")
print("=" * 45)

papers = agent.search_papers(
    research_topic=topic,
    max_results=5
)

print(f"\nTotal records retrieved: {len(papers)}")

for index, paper in enumerate(papers, start=1):
    print(f"\nPAPER {index}")
    print(f"Title: {paper['title']}")
    print(f"Year: {paper['year']}")
    print(f"Source: {paper['source']}")
    print("-" * 45)
