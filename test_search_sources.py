
from agents.search import SearchAgent
from agents.arxiv_search import ArxivSearchAgent


TOPIC = (
    "Explainable Artificial Intelligence "
    "for Credit Risk Assessment"
)


def main():

    openalex = SearchAgent(
        start_year=2022,
        end_year=2026
    )

    arxiv = ArxivSearchAgent(
        start_year=2022,
        end_year=2026
    )

    print("\nTESTING OPENALEX")

    openalex_papers = openalex.search_papers(
        research_topic=TOPIC,
        max_results=5
    )

    print("Papers found:", len(openalex_papers))

    for paper in openalex_papers:
        print(paper["year"], "-", paper["title"])
        assert 2022 <= paper["year"] <= 2026

    print("\nTESTING ARXIV")

    arxiv_papers = arxiv.search_papers(
        research_topic=TOPIC,
        max_results=5
    )

    print("Papers found:", len(arxiv_papers))

    for paper in arxiv_papers:
        print(paper["year"], "-", paper["title"])
        assert 2022 <= paper["year"] <= 2026

    print("\nSOURCE SEARCH TEST PASSED!")


if __name__ == "__main__":
    main()
