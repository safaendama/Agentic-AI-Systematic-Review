
import re
import time
import requests


class RetrievalAgent:

    def __init__(self):

        self.base_url = (
            "https://api.openalex.org/works"
        )

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": (
                "AgenticSystematicReview/1.0 "
                "(academic metadata research)"
            )
        })

        self.cache = {}

    # ==========================================
    # ABSTRACT RECONSTRUCTION
    # ==========================================

    def reconstruct_abstract(
        self,
        inverted_index
    ):
        """
        Convert an OpenAlex abstract inverted
        index into readable text.
        """

        if not isinstance(
            inverted_index,
            dict
        ):
            return None

        positions = {}

        for word, indices in inverted_index.items():

            if not isinstance(indices, list):
                continue

            for position in indices:

                if isinstance(position, int):
                    positions[position] = word

        if not positions:
            return None

        return " ".join(
            positions[position]
            for position in sorted(positions)
        )

    # ==========================================
    # OPENALEX IDENTIFIER
    # ==========================================

    def normalize_openalex_id(
        self,
        openalex_id
    ):
        """
        Normalize an OpenAlex work identifier.

        Accepts:
        - W123456789
        - https://openalex.org/W123456789
        """

        if not openalex_id:
            raise ValueError(
                "OpenAlex ID cannot be empty."
            )

        paper_id = str(
            openalex_id
        ).strip().rstrip("/").split("/")[-1]

        if not re.fullmatch(
            r"W\d+",
            paper_id,
            flags=re.IGNORECASE
        ):
            raise ValueError(
                "Invalid OpenAlex work identifier."
            )

        return paper_id.upper()

    # ==========================================
    # API REQUEST
    # ==========================================

    def _fetch_openalex(
        self,
        paper_id
    ):
        """
        Retrieve OpenAlex metadata with retries.
        """

        if paper_id in self.cache:
            return self.cache[paper_id]

        url = (
            f"{self.base_url}/{paper_id}"
        )

        for attempt in range(3):

            try:

                response = self.session.get(
                    url,
                    timeout=30
                )

                response.raise_for_status()

                data = response.json()

                self.cache[paper_id] = data

                return data

            except requests.RequestException as exc:

                if attempt == 2:
                    raise RuntimeError(
                        "OpenAlex metadata retrieval "
                        f"failed: {exc}"
                    ) from exc

                wait_time = 2 ** attempt

                print(
                    "[Retrieval] OpenAlex request "
                    f"failed. Retrying in {wait_time}s..."
                )

                time.sleep(wait_time)

    # ==========================================
    # RETRIEVE ONE OPENALEX PAPER
    # ==========================================

    def retrieve_paper(
        self,
        openalex_id
    ):
        """
        Retrieve detailed publication metadata
        from OpenAlex.

        Does not independently verify language
        or peer-review status.
        """

        paper_id = self.normalize_openalex_id(
            openalex_id
        )

        paper = self._fetch_openalex(
            paper_id
        )

        abstract = self.reconstruct_abstract(
            paper.get(
                "abstract_inverted_index"
            )
        )

        primary_location = (
            paper.get("primary_location")
            or {}
        )

        source = (
            primary_location.get("source")
            or {}
        )

        best_oa_location = (
            paper.get("best_oa_location")
            or {}
        )

        publication_type = paper.get(
            "type"
        )

        source_type = source.get(
            "type"
        )

        language = paper.get(
            "language"
        )

        return {
            "title": paper.get("title"),
            "year": paper.get(
                "publication_year"
            ),
            "doi": paper.get("doi"),
            "openalex_id": paper.get("id"),
            "abstract": abstract,
            "publication_date": paper.get(
                "publication_date"
            ),

            # Existing fields
            "type": publication_type,
            "cited_by_count": paper.get(
                "cited_by_count"
            ),
            "source": "OpenAlex",

            # Publication venue
            "venue_name": source.get(
                "display_name"
            ),
            "venue_type": source_type,
            "venue_id": source.get("id"),
            "venue_issn": (
                source.get("issn") or []
            ),
            "venue_issn_l": source.get(
                "issn_l"
            ),

            # Publication metadata
            "publication_version": (
                primary_location.get("version")
            ),
            "primary_landing_page_url": (
                primary_location.get(
                    "landing_page_url"
                )
            ),
            "primary_pdf_url": (
                primary_location.get(
                    "pdf_url"
                )
            ),
            "best_oa_pdf_url": (
                best_oa_location.get(
                    "pdf_url"
                )
            ),

            # Language
            "language": language,
            "language_verified": False,

            # Peer review
            "peer_reviewed": None,
            "peer_review_verified": False,

            # Verification tracking
            "verification_status": "pending",
            "verification_notes": (
                "Publication metadata retrieved "
                "from OpenAlex. Peer-review and "
                "language status require "
                "independent verification."
            )
        }

    # ==========================================
    # ENRICH AN EXISTING PAPER
    # ==========================================

    def enrich_paper(
        self,
        paper
    ):
        """
        Enrich an existing publication record.

        OpenAlex records:
            Retrieve additional metadata.

        Other records:
            Preserve existing information.

        This method does not overwrite
        previously verified information.
        """

        if not isinstance(paper, dict):
            raise ValueError(
                "paper must be a dictionary."
            )

        enriched = paper.copy()

        openalex_id = paper.get(
            "openalex_id"
        )

        if not openalex_id:
            return enriched

        details = self.retrieve_paper(
            openalex_id
        )

        for key, value in details.items():

            if (
                key not in enriched
                or enriched[key] is None
                or enriched[key] == ""
            ):
                enriched[key] = value

        return enriched

    # ==========================================
    # ENRICH MULTIPLE PAPERS
    # ==========================================

    def enrich_papers(
        self,
        papers
    ):
        """
        Enrich a list of paper records.

        Preserves ordering and record count.
        """

        if not isinstance(papers, list):
            raise ValueError(
                "papers must be a list."
            )

        enriched_papers = []

        for index, paper in enumerate(
            papers,
            start=1
        ):

            print(
                f"[Retrieval] Paper "
                f"{index}/{len(papers)}"
            )

            try:

                enriched = self.enrich_paper(
                    paper
                )

            except (
                RuntimeError,
                ValueError
            ) as error:

                print(
                    "[Retrieval] Enrichment failed:",
                    error
                )

                enriched = paper.copy()

                enriched["retrieval_error"] = (
                    str(error)
                )

            enriched_papers.append(
                enriched
            )

        print(
            "\nRETRIEVAL SUMMARY"
        )

        print(
            "Papers processed:",
            len(enriched_papers)
        )

        print(
            "Papers with abstracts:",
            sum(
                bool(paper.get("abstract"))
                for paper in enriched_papers
            )
        )

        return enriched_papers
