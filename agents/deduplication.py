
import re
import unicodedata


class DeduplicationAgent:

    def normalize_title(self, title):
        """
        Normalize a publication title for comparison.

        Handles:
        - Case differences
        - Unicode differences
        - Punctuation
        - Extra spaces
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

        title = " ".join(
            title.split()
        )

        return title

    def normalize_doi(self, doi):
        """
        Normalize DOI identifiers.

        Handles DOI URLs, DOI prefixes,
        uppercase letters, and whitespace.
        """

        if not doi:
            return None

        doi = str(doi).strip().lower()

        doi = re.sub(
            r"^https?://(?:dx\.)?doi\.org/",
            "",
            doi
        )

        doi = re.sub(
            r"^doi:\s*",
            "",
            doi
        )

        doi = doi.strip().rstrip("/")

        return doi or None

    def normalize_arxiv_id(self, arxiv_id):
        """
        Normalize arXiv identifiers.

        Removes:
        - arXiv URL prefix
        - arXiv: prefix
        - Version suffix such as v1 or v2
        """

        if not arxiv_id:
            return None

        arxiv_id = str(
            arxiv_id
        ).strip().lower()

        arxiv_id = re.sub(
            r"^https?://(?:www\.)?arxiv\.org/abs/",
            "",
            arxiv_id
        )

        arxiv_id = re.sub(
            r"^arxiv:",
            "",
            arxiv_id
        )

        arxiv_id = re.sub(
            r"v\d+$",
            "",
            arxiv_id
        )

        return arxiv_id or None

    def remove_duplicates(self, papers):
        """
        Remove duplicate publications.

        Matching priority:
        1. DOI
        2. arXiv ID
        3. Exact normalized title

        The title comparison is independent
        of publication year because different
        sources may report different years.

        Preserves the existing output structure.
        """

        if not isinstance(papers, list):
            raise ValueError(
                "papers must be a list."
            )

        unique_papers = []
        duplicates = []

        seen_dois = set()
        seen_arxiv_ids = set()
        seen_titles = set()

        for paper in papers:

            if not isinstance(paper, dict):
                continue

            doi = self.normalize_doi(
                paper.get("doi")
            )

            arxiv_id = self.normalize_arxiv_id(
                paper.get("arxiv_id")
            )

            title = self.normalize_title(
                paper.get("title")
            )

            is_duplicate = (
                (doi is not None and doi in seen_dois)
                or
                (
                    arxiv_id is not None
                    and arxiv_id in seen_arxiv_ids
                )
                or
                (
                    bool(title)
                    and title in seen_titles
                )
            )

            if is_duplicate:

                duplicates.append(paper)

                continue

            unique_papers.append(paper)

            if doi:
                seen_dois.add(doi)

            if arxiv_id:
                seen_arxiv_ids.add(arxiv_id)

            if title:
                seen_titles.add(title)

        return {
            "unique_papers": unique_papers,
            "duplicates": duplicates,
            "total_records": len(papers),
            "unique_count": len(unique_papers),
            "duplicate_count": len(duplicates)
        }
