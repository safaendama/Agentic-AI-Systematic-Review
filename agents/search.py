
import requests
import re
import time

from datetime import date


class SearchAgent:

    def __init__(
        self,
        start_year=2022,
        end_year=2026
    ):
        self.base_url = (
            "https://api.openalex.org/works"
        )

        self.start_year = int(start_year)
        self.end_year = int(end_year)

        if self.start_year > self.end_year:
            raise ValueError(
                "start_year cannot exceed end_year."
            )

        self.session = requests.Session()

    def _reconstruct_abstract(self, inverted_index):
        """
        Convert OpenAlex's abstract inverted index
        into readable text.
        """

        if not isinstance(inverted_index, dict):
            return ""

        positions = {}

        for word, indices in inverted_index.items():

            if not isinstance(indices, list):
                continue

            for position in indices:
                positions[position] = word

        return " ".join(
            positions[position]
            for position in sorted(positions)
        )

    def _build_search_queries(self, research_topic):
        """
        Create two search queries:

        1. Full research topic.
        2. Shorter topic containing its main concepts.

        This is topic-independent and avoids
        hardcoding a specific research domain.
        """

        full_query = research_topic.strip()

        # Remove descriptive subtitles after a colon.
        core_query = full_query.split(":")[0].strip()

        # Remove punctuation and normalize whitespace.
        core_query = re.sub(
            r"[^\w\s-]",
            " ",
            core_query
        )

        core_query = " ".join(core_query.split())

        queries = [full_query]

        if (
            core_query
            and core_query.lower() != full_query.lower()
        ):
            queries.append(core_query)

        return queries

    def _fetch_page(
        self,
        query,
        start_date,
        end_date,
        per_page,
        page
    ):
        """
        Fetch one OpenAlex results page.
        """

        params = {
            "search": query,
            "filter": (
                f"from_publication_date:"
                f"{start_date.isoformat()},"
                f"to_publication_date:"
                f"{end_date.isoformat()}"
            ),
            "per-page": per_page,
            "page": page
        }

        for attempt in range(3):

            try:

                response = self.session.get(
                    self.base_url,
                    params=params,
                    timeout=30
                )

                response.raise_for_status()

                return response.json()

            except requests.RequestException as exc:

                if attempt == 2:
                    raise RuntimeError(
                        "OpenAlex request failed after "
                        f"3 attempts: {exc}"
                    ) from exc

                wait_time = 2 ** attempt

                print(
                    "[OpenAlex] Request failed. "
                    f"Retrying in {wait_time}s..."
                )

                time.sleep(wait_time)

        return {}

    def _parse_paper(self, paper):
        """
        Convert an OpenAlex work into the
        metadata structure expected by
        the remaining agents.
        """

        authors = [
            authorship.get(
                "author", {}
            ).get("display_name")
            for authorship in paper.get(
                "authorships", []
            )
        ]

        authors = [
            author
            for author in authors
            if author
        ]

        abstract = self._reconstruct_abstract(
            paper.get(
                "abstract_inverted_index"
            )
        )

        return {
            "title": paper.get("title"),
            "year": paper.get(
                "publication_year"
            ),
            "publication_date": paper.get(
                "publication_date"
            ),
            "doi": paper.get("doi"),
            "openalex_id": paper.get("id"),
            "authors": authors,
            "abstract": abstract,
            "language": paper.get("language"),
            "language_verified": False,
            "peer_reviewed": None,
            "peer_review_verified": False,
            "source": "OpenAlex"
        }

    def search_papers(
        self,
        research_topic,
        max_results=75
    ):
        """
        Search OpenAlex within the configured
        publication-year range.

        Supports pagination and multiple
        topic-based search strategies.

        Returns up to max_results papers.
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

        end_date = min(
            date.today(),
            date(self.end_year, 12, 31)
        )

        start_date = date(
            self.start_year, 1, 1
        )

        if start_date > end_date:
            raise ValueError(
                "The publication range is entirely "
                "in the future."
            )

        queries = self._build_search_queries(
            research_topic
        )

        papers = []
        seen_ids = set()

        print(
            "\n[OpenAlex] Publication range:",
            f"{start_date} to {end_date}"
        )

        print(
            "[OpenAlex] Search strategies:",
            len(queries)
        )

        for strategy_number, query in enumerate(
            queries,
            start=1
        ):

            if len(papers) >= max_results:
                break

            print(
                f"\n[OpenAlex] Strategy "
                f"{strategy_number}/{len(queries)}"
            )

            print(
                "[OpenAlex] Query:",
                query
            )

            page = 1

            while len(papers) < max_results:

                remaining = (
                    max_results - len(papers)
                )

                per_page = min(
                    100,
                    remaining
                )

                data = self._fetch_page(
                    query=query,
                    start_date=start_date,
                    end_date=end_date,
                    per_page=per_page,
                    page=page
                )

                results = data.get(
                    "results", []
                )

                if not results:
                    break

                added = 0

                for item in results:

                    paper = self._parse_paper(item)

                    identifier = (
                        paper.get("openalex_id")
                        or paper.get("doi")
                        or paper.get("title")
                    )

                    if not identifier:
                        continue

                    identifier = str(
                        identifier
                    ).strip().lower()

                    if identifier in seen_ids:
                        continue

                    seen_ids.add(identifier)

                    papers.append(paper)
                    added += 1

                    if len(papers) >= max_results:
                        break

                print(
                    f"[OpenAlex] Page {page}: "
                    f"{len(results)} returned, "
                    f"{added} new, "
                    f"{len(papers)} total"
                )

                if len(results) < per_page:
                    break

                page += 1

                # Small pause between API requests.
                time.sleep(0.3)

        print(
            "\n[OpenAlex] Search completed."
        )

        print(
            "[OpenAlex] Unique papers retrieved:",
            len(papers)
        )

        return papers
