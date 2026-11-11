
import re
import time
import requests
import unicodedata

from copy import deepcopy
from datetime import datetime, timezone
from difflib import SequenceMatcher
from urllib.parse import unquote, quote


class PublicationVerificationAgent:

    def __init__(self):

        self.crossref_url = (
            "https://api.crossref.org/works/"
        )

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": (
                "AgenticSystematicReview/1.0 "
                "(academic metadata research)"
            )
        })

        self.crossref_cache = {}

    # ==================================================
    # NORMALIZATION
    # ==================================================

    def normalize_doi(self, doi):

        if not doi:
            return None

        doi = unquote(
            str(doi).strip()
        )

        doi = re.sub(
            r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)",
            "",
            doi,
            flags=re.IGNORECASE
        )

        return doi.strip() or None

    def normalize_title(self, title):
        """
        Normalize titles for metadata comparison.
        """

        title = unicodedata.normalize(
            "NFKC",
            str(title or "")
        ).casefold()

        title = re.sub(
            r"[^\w\s]",
            " ",
            title
        )

        return " ".join(
            title.split()
        )

    def title_similarity(self, title_a, title_b):
        """
        Compare titles without changing them.
        """

        normalized_a = self.normalize_title(
            title_a
        )

        normalized_b = self.normalize_title(
            title_b
        )

        if not normalized_a or not normalized_b:
            return None

        return round(
            SequenceMatcher(
                None,
                normalized_a,
                normalized_b
            ).ratio(),
            3
        )

    # ==================================================
    # CROSSREF LOOKUP
    # ==================================================

    def fetch_crossref(self, doi):
        """
        Retrieve Crossref metadata by DOI.

        Uses caching and retries to reduce
        unnecessary API requests.
        """

        doi = self.normalize_doi(doi)

        if not doi:
            return None

        cache_key = doi.lower()

        if cache_key in self.crossref_cache:
            return self.crossref_cache[cache_key]

        url = (
            self.crossref_url
            + quote(doi, safe="/")
        )

        for attempt in range(3):

            try:

                response = self.session.get(
                    url,
                    timeout=30
                )

                if response.status_code == 404:
                    self.crossref_cache[cache_key] = None
                    return None

                response.raise_for_status()

                data = response.json().get(
                    "message", {}
                )

                metadata = {
                    "doi": data.get("DOI"),
                    "title": (
                        data.get("title") or [None]
                    )[0],
                    "publisher": data.get("publisher"),
                    "publication_type": data.get("type"),
                    "venue_name": (
                        data.get("container-title") or [None]
                    )[0],
                    "publication_date": data.get(
                        "published"
                    ),
                    "source_url": data.get("URL"),
                    "metadata_source": "Crossref"
                }

                self.crossref_cache[cache_key] = (
                    metadata
                )

                return metadata

            except requests.RequestException:

                if attempt == 2:
                    raise

                wait_time = 2 ** attempt

                time.sleep(wait_time)

        return None

    # ==================================================
    # VERIFY ONE PAPER
    # ==================================================

    def verify_paper(self, paper):
        """
        Verify metadata while preserving the
        original publication record.

        Crossref verification does not imply
        peer-review verification.
        """

        if not isinstance(paper, dict):
            raise ValueError(
                "Each paper must be a dictionary."
            )

        result = deepcopy(paper)

        result.setdefault(
            "language_verified",
            False
        )

        result.setdefault(
            "peer_reviewed",
            None
        )

        result.setdefault(
            "peer_review_verified",
            False
        )

        result.setdefault(
            "verification_evidence",
            []
        )

        doi = self.normalize_doi(
            result.get("doi")
        )

        result["doi_normalized"] = doi

        result["crossref_lookup_status"] = (
            "not_attempted"
        )

        result["title_match_status"] = (
            "not_checked"
        )

        result["title_similarity_score"] = None

        # ----------------------------------
        # CROSSREF VERIFICATION
        # ----------------------------------

        if doi:

            try:

                crossref = self.fetch_crossref(
                    doi
                )

                if crossref:

                    result["crossref_lookup_status"] = (
                        "found"
                    )

                    result["crossref_metadata"] = (
                        crossref
                    )

                    if not result.get("venue_name"):
                        result["venue_name"] = (
                            crossref.get("venue_name")
                        )

                    if not result.get("publisher"):
                        result["publisher"] = (
                            crossref.get("publisher")
                        )

                    result["crossref_type"] = (
                        crossref.get("publication_type")
                    )

                    similarity = self.title_similarity(
                        result.get("title"),
                        crossref.get("title")
                    )

                    result["title_similarity_score"] = (
                        similarity
                    )

                    if similarity is None:

                        result["title_match_status"] = (
                            "unverified"
                        )

                    elif similarity >= 0.90:

                        result["title_match_status"] = (
                            "matched"
                        )

                    else:

                        result["title_match_status"] = (
                            "needs_review"
                        )

                    result[
                        "verification_evidence"
                    ].append({
                        "source": "Crossref",
                        "url": crossref.get(
                            "source_url"
                        ),
                        "purpose": (
                            "DOI metadata and "
                            "title comparison"
                        ),
                        "checked_at": datetime.now(
                            timezone.utc
                        ).isoformat()
                    })

                else:

                    result["crossref_lookup_status"] = (
                        "not_found"
                    )

            except (
                requests.RequestException,
                ValueError
            ) as error:

                result["crossref_lookup_status"] = (
                    "error"
                )

                result["crossref_error"] = str(
                    error
                )

        # ----------------------------------
        # MISSING VERIFICATION INFORMATION
        # ----------------------------------

        missing = []

        if not result.get("title"):
            missing.append("title")

        if not result.get("year"):
            missing.append("publication year")

        if not result.get("abstract"):
            missing.append("abstract")

        if result.get("language_verified") is not True:
            missing.append(
                "independent language verification"
            )

        if result.get("peer_review_verified") is not True:
            missing.append(
                "independent peer-review verification"
            )

        if not doi and not result.get("arxiv_id"):
            missing.append(
                "DOI or arXiv identifier"
            )

        if (
            doi
            and result["crossref_lookup_status"]
            != "found"
        ):
            missing.append(
                "Crossref DOI verification"
            )

        if result["title_match_status"] == "needs_review":
            missing.append(
                "Crossref title consistency review"
            )

        result["verification_missing"] = missing

        result["verification_status"] = (
            "pending" if missing else "verified"
        )

        return result

    # ==================================================
    # VERIFY MULTIPLE PAPERS
    # ==================================================

    def verify_papers(self, papers):
        """
        Verify all papers and preserve
        their original ordering.
        """

        if not isinstance(papers, list):
            raise ValueError(
                "papers must be a list."
            )

        verified_papers = []

        for index, paper in enumerate(
            papers,
            start=1
        ):

            print(
                f"[Verification] Paper "
                f"{index}/{len(papers)}"
            )

            verified = self.verify_paper(
                paper
            )

            verified_papers.append(
                verified
            )

        pending_count = sum(
            paper["verification_status"] == "pending"
            for paper in verified_papers
        )

        print(
            "\nPUBLICATION VERIFICATION SUMMARY"
        )

        print(
            "Total papers:",
            len(verified_papers)
        )

        print(
            "Verified:",
            len(verified_papers) - pending_count
        )

        print(
            "Pending verification:",
            pending_count
        )

        return verified_papers
