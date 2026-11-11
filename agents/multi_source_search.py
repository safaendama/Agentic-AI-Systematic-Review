
from datetime import date

from agents.search import SearchAgent
from agents.arxiv_search import ArxivSearchAgent


class MultiSourceSearchAgent:

    def __init__(
        self,
        start_year=2022,
        end_year=2026
    ):
        self.start_year = int(start_year)
        self.end_year = int(end_year)

        if self.start_year > self.end_year:
            raise ValueError(
                "start_year cannot be greater than end_year."
            )

        self.openalex_agent = SearchAgent(
            start_year=self.start_year,
            end_year=self.end_year
        )

        self.arxiv_agent = ArxivSearchAgent(
            start_year=self.start_year,
            end_year=self.end_year
        )

    def _filter_by_year(self, papers, source_name):
        """
        Keep papers within the configured year range.

        Records with missing or invalid years are
        retained for manual verification.
        """

        filtered = []
        excluded_count = 0
        unknown_count = 0

        latest_year = min(
            self.end_year,
            date.today().year
        )

        for paper in papers:

            if not isinstance(paper, dict):
                unknown_count += 1
                continue

            try:
                year = int(paper.get("year"))

            except (TypeError, ValueError):
                enriched = paper.copy()
                enriched["year_filter_status"] = (
                    "year_unverified"
                )

                filtered.append(enriched)
                unknown_count += 1
                continue

            if self.start_year <= year <= latest_year:
                enriched = paper.copy()
                enriched["year_filter_status"] = (
                    "within_range"
                )

                filtered.append(enriched)

            else:
                excluded_count += 1

        print(
            f"{source_name}: "
            f"{len(filtered)} retained, "
            f"{excluded_count} outside range, "
            f"{unknown_count} missing/invalid year"
        )

        return filtered

    def search_papers(
        self,
        research_topic,
        max_results=75
    ):
        """
        Search OpenAlex and arXiv.

        Default target:
            OpenAlex: up to 75 papers
            arXiv: up to 75 papers

        Combined target:
            Up to 150 records before deduplication.

        Actual retrieval depends on source availability,
        search strategies, and API limits.
        """

        if not isinstance(research_topic, str):
            raise ValueError(
                "research_topic must be a string."
            )

        research_topic = research_topic.strip()

        if not research_topic:
            raise ValueError(
                "research_topic cannot be empty."
            )

        max_results = int(max_results)

        if max_results < 1:
            raise ValueError(
                "max_results must be at least 1."
            )

        all_papers = []

        print(
            "\nPublication range:",
            f"{self.start_year}–{self.end_year}"
        )

        print(
            "Maximum records requested per source:",
            max_results
        )

        # ==================================
        # OPENALEX SEARCH
        # ==================================

        print("\nSearching OpenAlex...")

        openalex_papers = (
            self.openalex_agent.search_papers(
                research_topic=research_topic,
                max_results=max_results
            )
        )

        if not isinstance(openalex_papers, list):
            raise ValueError(
                "OpenAlex Search Agent must "
                "return a list."
            )

        openalex_filtered = self._filter_by_year(
            openalex_papers,
            "OpenAlex"
        )

        all_papers.extend(openalex_filtered)

        # ==================================
        # ARXIV SEARCH
        # ==================================

        print("\nSearching arXiv...")

        arxiv_papers = (
            self.arxiv_agent.search_papers(
                research_topic=research_topic,
                max_results=max_results
            )
        )

        if not isinstance(arxiv_papers, list):
            raise ValueError(
                "arXiv Search Agent must "
                "return a list."
            )

        arxiv_filtered = self._filter_by_year(
            arxiv_papers,
            "arXiv"
        )

        all_papers.extend(arxiv_filtered)

        # ==================================
        # SEARCH SUMMARY
        # ==================================

        print("\nMULTI-SOURCE SEARCH SUMMARY")

        print(
            "OpenAlex records retained:",
            len(openalex_filtered)
        )

        print(
            "arXiv records retained:",
            len(arxiv_filtered)
        )

        print(
            "Total records retained:",
            len(all_papers)
        )

        print(
            "Note: Duplicate removal is handled "
            "by Step 4."
        )

        return all_papers
