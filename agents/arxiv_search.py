
"""
STEP 3 — GENERIC ARXIV SEARCH AGENT

Searches arXiv for scientific papers related to
any user-provided research topic.

Improvements:
- Topic-independent search queries
- Avoids requiring every word in long titles
- Uses focused and broader search strategies
- Supports pagination
- Preserves publication-date filtering
- Removes duplicate arXiv records
- Handles API failures and retries
- Preserves the existing search_papers() interface
"""

import re
import time
import requests
import xml.etree.ElementTree as ET

from datetime import date


class ArxivSearchAgent:

    STOPWORDS = {
        "a", "an", "the", "and", "or", "of",
        "in", "on", "at", "to", "for",
        "from", "with", "without", "by",
        "using", "based", "through", "into",
        "towards", "toward", "via", "its",
        "their", "study", "studies",
        "research", "review", "systematic",
        "methods", "method", "performance",
        "challenges", "challenge",
        "analysis", "evaluation", "overview",
    }

    def __init__(
        self,
        start_year=2022,
        end_year=2026
    ):

        self.base_url = (
            "https://export.arxiv.org/api/query"
        )

        self.namespace = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom",
            "opensearch": (
                "http://a9.com/-/spec/opensearch/1.1/"
            )
        }

        self.start_year = int(start_year)
        self.end_year = int(end_year)

        if self.start_year > self.end_year:
            raise ValueError(
                "start_year cannot exceed end_year."
            )

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": (
                "AcademicSLRResearch/1.0 "
                "(academic literature retrieval)"
            )
        })

    # ========================================================
    # EXTRACT TOPIC KEYWORDS
    # ========================================================

    def _extract_keywords(self, research_topic):
        """
        Extract meaningful keywords from any topic.
        """

        if not isinstance(research_topic, str):
            raise ValueError(
                "Research topic must be a string."
            )

        topic = " ".join(
            research_topic.split()
        )

        if not topic:
            raise ValueError(
                "Research topic cannot be empty."
            )

        words = re.findall(
            r"[A-Za-z0-9]+",
            topic.lower()
        )

        keywords = []

        for word in words:

            if len(word) < 3:
                continue

            if word in self.STOPWORDS:
                continue

            if word not in keywords:
                keywords.append(word)

        if not keywords:
            raise ValueError(
                "No searchable keywords found."
            )

        return keywords

    # ========================================================
    # DATE FILTER
    # ========================================================

    def _date_filter(self):
        """
        Build arXiv submission-date filter.
        """

        today = date.today()

        if self.start_year > today.year:
            raise ValueError(
                "The publication range is "
                "entirely in the future."
            )

        effective_end = min(
            self.end_year,
            today.year
        )

        start_date = (
            f"{self.start_year}01010000"
        )

        if effective_end == today.year:

            end_date = (
                today.strftime("%Y%m%d")
                + "2359"
            )

        else:

            end_date = (
                f"{effective_end}12312359"
            )

        return (
            f"submittedDate:[{start_date} "
            f"TO {end_date}]"
        )

    # ========================================================
    # SEARCH STRATEGIES
    # ========================================================

    def _build_queries(self, research_topic):
        """
        Build focused-to-broader search strategies.

        Strategy 1:
            Core topic keywords combined with AND.

        Strategy 2:
            Adjacent keyword pairs from the core topic.

        Strategy 3:
            The first two core keywords combined with AND.

        The topic's subtitle is excluded from the
        core search when a colon is present.

        No research domain is hardcoded.
        """

        core_topic = (
            research_topic.split(":", 1)[0]
            .strip()
        )

        keywords = self._extract_keywords(
            core_topic
        )

        date_filter = self._date_filter()

        queries = []

        # Strategy 1: Focused core concepts.
        # Limit the number of mandatory terms.

        focused_terms = keywords[:4]

        focused_query = " AND ".join(
            f"all:{word}"
            for word in focused_terms
        )

        queries.append(
            f"({focused_query}) AND {date_filter}"
        )

        # Strategy 2: Adjacent concept pairs.
        # Use pairs rather than all keywords.

        if len(keywords) >= 3:

            pairs = []

            for index in range(
                min(len(keywords) - 1, 5)
            ):

                left = keywords[index]
                right = keywords[index + 1]

                pairs.append(
                    f"(all:{left} AND all:{right})"
                )

            pair_query = " OR ".join(
                pairs
            )

            queries.append(
                f"({pair_query}) AND {date_filter}"
            )

        # Strategy 3: Broad core search.
        # Retain two meaningful concepts.

        if len(keywords) >= 2:

            broad_terms = keywords[:2]

            broad_query = " AND ".join(
                f"all:{word}"
                for word in broad_terms
            )

            queries.append(
                f"({broad_query}) AND {date_filter}"
            )

        return list(
            dict.fromkeys(queries)
        )

    def _build_query(self, research_topic):
        """
        Preserve compatibility with callers
        expecting one query.
        """

        return self._build_queries(
            research_topic
        )[0]

    # ========================================================
    # PARSE ARXIV RESPONSE
    # ========================================================

    def _parse_response(self, content):
        """
        Parse arXiv Atom XML into paper records.
        """

        root = ET.fromstring(content)

        papers = []

        today = date.today()

        for entry in root.findall(
            "atom:entry",
            self.namespace
        ):

            title = entry.findtext(
                "atom:title",
                "",
                self.namespace
            )

            abstract = entry.findtext(
                "atom:summary",
                "",
                self.namespace
            )

            published = entry.findtext(
                "atom:published",
                "",
                self.namespace
            )

            paper_id = entry.findtext(
                "atom:id",
                "",
                self.namespace
            )

            authors = [
                author.findtext(
                    "atom:name",
                    "",
                    self.namespace
                )
                for author in entry.findall(
                    "atom:author",
                    self.namespace
                )
            ]

            doi = entry.findtext(
                "arxiv:doi",
                "",
                self.namespace
            )

            if not published:
                continue

            try:

                publication_date = (
                    date.fromisoformat(
                        published[:10]
                    )
                )

            except ValueError:
                continue

            latest_date = min(
                date(self.end_year, 12, 31),
                today
            )

            if not (
                date(self.start_year, 1, 1)
                <= publication_date
                <= latest_date
            ):
                continue

            clean_title = " ".join(
                title.split()
            )

            clean_abstract = " ".join(
                abstract.split()
            )

            if not clean_title:
                continue

            papers.append({
                "title": clean_title,
                "year": publication_date.year,
                "publication_date": published,
                "doi": doi or None,
                "arxiv_id": paper_id,
                "url": paper_id,
                "authors": [
                    author
                    for author in authors
                    if author
                ],
                "abstract": clean_abstract,
                "language": None,
                "language_verified": False,
                "peer_reviewed": None,
                "peer_review_verified": False,
                "source": "arXiv"
            })

        return papers

    # ========================================================
    # DUPLICATE DETECTION
    # ========================================================

    def _paper_key(self, paper):
        """
        Create a stable duplicate-detection key.
        """

        doi = str(
            paper.get("doi") or ""
        ).strip().lower()

        doi = re.sub(
            r"^https?://(?:dx\.)?doi\.org/",
            "",
            doi
        )

        if doi:
            return "doi:" + doi

        arxiv_id = str(
            paper.get("arxiv_id") or ""
        ).strip().lower()

        if arxiv_id:

            arxiv_id = re.sub(
                r"v\d+$",
                "",
                arxiv_id
            )

            return "arxiv:" + arxiv_id

        title = re.sub(
            r"[^a-z0-9]+",
            "",
            str(
                paper.get("title") or ""
            ).lower()
        )

        return "title:" + title

    # ========================================================
    # API REQUEST
    # ========================================================

    def _fetch_page(
        self,
        query,
        start,
        max_results
    ):
        """
        Fetch one page with retry handling.
        """

        params = {
            "search_query": query,
            "start": start,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending"
        }

        for attempt in range(3):

            try:

                response = self.session.get(
                    self.base_url,
                    params=params,
                    timeout=60
                )

                response.raise_for_status()

                return response.content

            except requests.RequestException as exc:

                if attempt == 2:

                    raise RuntimeError(
                        "arXiv request failed "
                        f"after 3 attempts: {exc}"
                    ) from exc

                wait_time = 3 * (
                    attempt + 1
                )

                print(
                    "[arXiv] Request failed. "
                    f"Retrying in {wait_time}s..."
                )

                time.sleep(wait_time)

        return b""

    # ========================================================
    # SEARCH PAPERS
    # ========================================================

    def search_papers(
        self,
        research_topic,
        max_results=75
    ):
        """
        Search arXiv using multiple strategies.

        Supports pagination and deduplication.

        Returns up to max_results records.
        """

        max_results = int(max_results)

        if max_results < 1:
            raise ValueError(
                "max_results must be positive."
            )

        queries = self._build_queries(
            research_topic
        )

        print(
            "\nSearching arXiv for:",
            research_topic
        )

        print(
            "Search strategies:",
            len(queries)
        )

        papers = []
        seen = set()

        request_count = 0

        for index, query in enumerate(
            queries,
            start=1
        ):

            if len(papers) >= max_results:
                break

            print(
                f"\narXiv strategy "
                f"{index}/{len(queries)}"
            )

            print(
                "arXiv query:",
                query
            )

            offset = 0
            page_size = 50

            # Limit the number of pages per strategy
            # to prevent excessively broad searches.

            max_pages = 5

            for page in range(max_pages):

                if len(papers) >= max_results:
                    break

                remaining = (
                    max_results - len(papers)
                )

                batch_size = min(
                    page_size,
                    max(10, remaining)
                )

                # Respect the arXiv API request interval.
                if request_count > 0:
                    time.sleep(3)

                try:

                    content = self._fetch_page(
                        query=query,
                        start=offset,
                        max_results=batch_size
                    )

                    request_count += 1

                    results = self._parse_response(
                        content
                    )

                except (
                    RuntimeError,
                    ET.ParseError
                ) as error:

                    print(
                        "[arXiv] Search failed:",
                        error
                    )

                    break

                if not results:
                    print(
                        "[arXiv] No records returned "
                        "on this page."
                    )
                    break

                added = 0

                for paper in results:

                    key = self._paper_key(
                        paper
                    )

                    if key in seen:
                        continue

                    seen.add(key)
                    papers.append(paper)

                    added += 1

                    if len(papers) >= max_results:
                        break

                print(
                    f"[arXiv] Page {page + 1}: "
                    f"{len(results)} returned, "
                    f"{added} new, "
                    f"{len(papers)} total"
                )

                offset += batch_size

                if len(results) < batch_size:
                    break

        print(
            "\nARXIV SEARCH COMPLETED"
        )

        print(
            "Unique papers retrieved:",
            len(papers)
        )

        return papers
