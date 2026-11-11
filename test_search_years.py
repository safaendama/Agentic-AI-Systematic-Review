
from agents.multi_source_search import MultiSourceSearchAgent


def main():

    agent = MultiSourceSearchAgent(
        start_year=2022,
        end_year=2026
    )

    sample_papers = [
        {"title": "Paper 2020", "year": 2020},
        {"title": "Paper 2021", "year": 2021},
        {"title": "Paper 2022", "year": 2022},
        {"title": "Paper 2024", "year": 2024},
        {"title": "Paper 2026", "year": 2026},
        {"title": "Paper Unknown", "year": None}
    ]

    filtered = agent._filter_by_year(
        sample_papers,
        "Test source"
    )

    retained_titles = {
        paper["title"]
        for paper in filtered
    }

    assert "Paper 2020" not in retained_titles
    assert "Paper 2021" not in retained_titles
    assert "Paper 2022" in retained_titles
    assert "Paper 2024" in retained_titles
    assert "Paper 2026" in retained_titles

    unknown = next(
        paper
        for paper in filtered
        if paper["title"] == "Paper Unknown"
    )

    assert (
        unknown["year_filter_status"]
        == "year_unverified"
    )

    print("\nSEARCH YEAR FILTER TEST PASSED!")


if __name__ == "__main__":
    main()
