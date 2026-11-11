
from agents.arxiv_search import ArxivSearchAgent

agent = ArxivSearchAgent()

topic = "explainable AI credit risk"

print("ARXIV SEARCH AGENT TEST")
print("=" * 45)

papers = agent.search_papers(
    research_topic=topic,
    max_results=5
)

print(f"\nTotal papers retrieved: {len(papers)}")

for index, paper in enumerate(papers, start=1):
    print(f"\nPAPER {index}")
    print(f"Title: {paper['title']}")
    print(f"Year: {paper['year']}")
    print(f"Authors: {', '.join(paper['authors'])}")
    print(f"Source: {paper['source']}")
    print("-" * 45)
