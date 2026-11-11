
"""
STEP 7 — GENERIC SCIENTIFIC SCREENING AGENT

Works with any research topic.

Features:
- Uses dynamically generated protocol criteria.
- Checks publication years.
- Detects secondary reviews when excluded.
- Screens title and abstract using Qwen.
- Separates scientific relevance from metadata checks.
- Preserves verification warnings.
- Never treats provisional inclusion as final eligibility.

Compatible with existing workflow:
    ScreeningAgent().screen_paper(
        paper,
        research_topic,
        inclusion_criteria,
        exclusion_criteria
    )
"""

import json
import re
from datetime import date

from langchain_ollama import ChatOllama


class ScreeningAgent:

    VALID_DECISIONS = {
        "include",
        "exclude",
        "uncertain",
    }

    def __init__(self):
        self.llm = ChatOllama(
            model="qwen3:4b",
            temperature=0,
            reasoning=False,
            format="json",
        )

    # ==========================================
    # RESULT FORMAT
    # ==========================================

    def _result(
        self,
        title,
        decision,
        reason,
        verification_flags=None,
        content_decision=None,
    ):
        return {
            "title": title,
            "decision": decision,
            "reason": reason,
            "content_decision": (
                content_decision or decision
            ),
            "verification_flags": (
                verification_flags or []
            ),
            "eligibility_status": "provisional",
            "requires_human_review": True,
        }

    # ==========================================
    # CRITERIA NORMALIZATION
    # ==========================================

    def _criteria_list(self, criteria):
        if criteria is None:
            return []

        if isinstance(criteria, str):
            return [criteria]

        if isinstance(criteria, dict):
            return [
                str(value)
                for value in criteria.values()
                if value is not None
            ]

        if isinstance(criteria, (list, tuple, set)):
            return [
                str(item)
                for item in criteria
                if item is not None
            ]

        return [str(criteria)]

    # ==========================================
    # YEAR REQUIREMENTS
    # ==========================================

    def _year_limits(self, inclusion_criteria):
        text = " ".join(
            self._criteria_list(inclusion_criteria)
        )

        match = re.search(
            r"\b((?:19|20)\d{2})\s*"
            r"(?:and|to|through|-|–|—)\s*"
            r"((?:19|20)\d{2})\b",
            text,
            re.IGNORECASE,
        )

        if match:
            return (
                int(match.group(1)),
                int(match.group(2)),
            )

        match = re.search(
            r"\b(?:from|since)\s+"
            r"((?:19|20)\d{2})\b",
            text,
            re.IGNORECASE,
        )

        if match:
            return (
                int(match.group(1)),
                date.today().year,
            )

        match = re.search(
            r"\b((?:19|20)\d{2})\s*"
            r"(?:onwards|onward|or later|"
            r"or newer|and later)\b",
            text,
            re.IGNORECASE,
        )

        if match:
            return (
                int(match.group(1)),
                date.today().year,
            )

        return None, None

    # ==========================================
    # LANGUAGE REQUIREMENTS
    # ==========================================

    def _required_language(self, inclusion_criteria):
        text = " ".join(
            self._criteria_list(inclusion_criteria)
        ).lower()

        if re.search(
            r"\benglish[\s-]+language\b|"
            r"\b(?:published|written)\s+in\s+english\b|"
            r"\b(?:studies|publications)\s+"
            r"(?:published|written)\s+in\s+english\b|"
            r"\benglish[\s-]+only\b",
            text,
        ):
            return "en"

        return None

    def _language_status(
        self,
        paper,
        required_language,
    ):
        if required_language is None:
            return True

        if paper.get("language_verified") is not True:
            return None

        raw = str(
            paper.get("language")
            or paper.get("publication_language")
            or ""
        ).strip().lower()

        if not raw:
            return None

        aliases = {
            "english": "en",
            "eng": "en",
            "en": "en",
        }

        language = aliases.get(raw, raw)

        return language == required_language

    # ==========================================
    # PEER-REVIEW REQUIREMENTS
    # ==========================================

    def _peer_review_required(
        self,
        inclusion_criteria,
        exclusion_criteria,
    ):
        text = " ".join(
            self._criteria_list(inclusion_criteria)
            + self._criteria_list(exclusion_criteria)
        ).lower()

        return bool(
            re.search(
                r"peer[\s-]?review",
                text,
            )
        )

    def _peer_review_status(self, paper):
        if paper.get("peer_review_verified") is not True:
            return None

        value = paper.get("peer_reviewed")

        if isinstance(value, bool):
            return value

        return None

    # ==========================================
    # SECONDARY REVIEW RULES
    # ==========================================

    def _secondary_reviews_excluded(
        self,
        exclusion_criteria,
    ):
        """
        Determine whether the generated
        protocol excludes secondary studies.
        """

        text = " ".join(
            self._criteria_list(exclusion_criteria)
        ).lower()

        return bool(
            re.search(
                r"\bsecondary\s+reviews?\b|"
                r"\bsystematic\s+reviews?\b|"
                r"\bliterature\s+reviews?\b|"
                r"\bscoping\s+reviews?\b|"
                r"\bmeta[\s-]?analys(?:is|es)\b|"
                r"\bsurveys?\b",
                text,
            )
        )

    def _is_secondary_review(self, paper):
        """
        Detect strong indications that a paper
        is a secondary review.

        A title that merely contains 'review'
        in another context is not automatically
        excluded.

        Ambiguous cases are assessed by the LLM.
        """

        title = " ".join(
            str(
                paper.get("title") or ""
            ).split()
        ).lower()

        publication_type = str(
            paper.get("publication_type")
            or paper.get("study_type")
            or ""
        ).strip().lower()

        explicit_type = re.search(
            r"\b(?:systematic review|"
            r"literature review|"
            r"scoping review|"
            r"meta-analysis|"
            r"meta-analyses|"
            r"review article|"
            r"survey article)\b",
            publication_type,
        )

        if explicit_type:
            return True

        title_patterns = [
            r"\bsystematic\s+review\b",
            r"\bliterature\s+review\b",
            r"\bscoping\s+review\b",
            r"\bmeta[\s-]?analys(?:is|es)\b",
            r"\bcomprehensive\s+(?:review|survey)\b",
            r"\b(?:a|an)\s+(?:critical\s+)?review\s*$",
            r"\b(?:a|an)\s+(?:comprehensive\s+)?survey\s*$",
            r"\breview\s+of\s+(?:the\s+)?literature\b",
        ]

        return any(
            re.search(pattern, title)
            for pattern in title_patterns
        )

    # ==========================================
    # EMPIRICAL STUDY REQUIREMENTS
    # ==========================================

    def _empirical_required(
        self,
        inclusion_criteria,
    ):
        text = " ".join(
            self._criteria_list(inclusion_criteria)
        ).lower()

        return bool(
            re.search(
                r"\bempirical\b|"
                r"\boriginal\s+research\b|"
                r"\boriginal\s+studies\b|"
                r"\bexperimental\s+evaluation\b",
                text,
            )
        )

    # ==========================================
    # LLM RESPONSE PARSING
    # ==========================================

    def _parse_ai_response(self, content):
        if not isinstance(content, str):
            raise ValueError(
                "AI response is not text."
            )

        content = re.sub(
            r"<think>.*?</think>",
            "",
            content,
            flags=re.DOTALL,
        ).strip()

        if "</think>" in content:
            content = content.split(
                "</think>"
            )[-1].strip()

        content = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            content,
            flags=re.IGNORECASE,
        ).strip()

        try:
            data = json.loads(content)

        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")

            if start == -1 or end <= start:
                raise ValueError(
                    "No JSON object found."
                )

            data = json.loads(
                content[start:end + 1]
            )

        if not isinstance(data, dict):
            raise ValueError(
                "AI response must be a JSON object."
            )

        decision = str(
            data.get("decision") or ""
        ).strip().lower()

        reason = str(
            data.get("reason") or ""
        ).strip()

        if decision not in self.VALID_DECISIONS:
            raise ValueError(
                "Invalid screening decision."
            )

        if not reason:
            raise ValueError(
                "Missing screening reason."
            )

        return decision, reason

    # ==========================================
    # SCIENTIFIC CONTENT CRITERIA
    # ==========================================

    def _content_criteria(self, criteria):
        """
        Remove only clearly administrative
        criteria from the LLM content task.
        """

        result = []

        for criterion in self._criteria_list(criteria):
            if re.search(
                r"\b(?:19|20)\d{2}\b|"
                r"peer[\s-]?review|"
                r"\benglish\b",
                criterion,
                re.IGNORECASE,
            ):
                continue

            result.append(criterion)

        return result

    # ==========================================
    # MAIN SCREENING METHOD
    # ==========================================

    def screen_paper(
        self,
        paper,
        research_topic,
        inclusion_criteria,
        exclusion_criteria,
    ):
        title = " ".join(
            str(
                paper.get("title") or ""
            ).split()
        )

        abstract = " ".join(
            str(
                paper.get("abstract") or ""
            ).split()
        )

        inclusion_criteria = self._criteria_list(
            inclusion_criteria
        )

        exclusion_criteria = self._criteria_list(
            exclusion_criteria
        )

        verification_flags = []

        # --------------------------------------
        # 1. BASIC RECORD VALIDATION
        # --------------------------------------

        if not title:
            return self._result(
                title,
                "uncertain",
                "Paper title is missing.",
            )

        if not abstract:
            return self._result(
                title,
                "uncertain",
                "Paper abstract is unavailable.",
            )

        # --------------------------------------
        # 2. YEAR ELIGIBILITY
        # --------------------------------------

        min_year, max_year = self._year_limits(
            inclusion_criteria
        )

        try:
            year = int(
                paper.get("year")
            )
        except (TypeError, ValueError):
            year = None

        if year is None:
            verification_flags.append(
                "Publication year is unknown."
            )

        elif year < 1800 or year > date.today().year:
            verification_flags.append(
                "Publication year requires verification."
            )

        elif (
            min_year is not None
            and max_year is not None
            and not (
                min_year <= year <= max_year
            )
        ):
            return self._result(
                title,
                "exclude",
                f"Publication year {year} "
                f"is outside the protocol range "
                f"{min_year}-{max_year}.",
            )

        if min_year is None or max_year is None:
            verification_flags.append(
                "Protocol year range was not "
                "identified reliably."
            )

        # --------------------------------------
        # 3. SECONDARY REVIEW EXCLUSION
        # --------------------------------------

        exclude_reviews = (
            self._secondary_reviews_excluded(
                exclusion_criteria
            )
        )

        if exclude_reviews:
            if self._is_secondary_review(paper):
                return self._result(
                    title,
                    "exclude",
                    "Paper is identified as a "
                    "secondary review, which is "
                    "excluded by the protocol.",
                    verification_flags,
                )

        # --------------------------------------
        # 4. PEER-REVIEW VERIFICATION
        # --------------------------------------

        peer_review_required = (
            self._peer_review_required(
                inclusion_criteria,
                exclusion_criteria,
            )
        )

        peer_status = self._peer_review_status(
            paper
        )

        if peer_review_required:
            if peer_status is False:
                return self._result(
                    title,
                    "exclude",
                    "Publication is independently "
                    "verified as not peer reviewed.",
                    verification_flags,
                )

            if peer_status is None:
                verification_flags.append(
                    "Peer-review status requires "
                    "independent verification."
                )

        # --------------------------------------
        # 5. LANGUAGE VERIFICATION
        # --------------------------------------

        required_language = (
            self._required_language(
                inclusion_criteria
            )
        )

        language_status = self._language_status(
            paper,
            required_language,
        )

        if language_status is False:
            return self._result(
                title,
                "exclude",
                "Verified publication language "
                "does not meet the protocol.",
                verification_flags,
            )

        if language_status is None:
            verification_flags.append(
                "Publication language requires "
                "independent verification."
            )

        # --------------------------------------
        # 6. SCIENTIFIC SCREENING
        # --------------------------------------

        empirical_required = (
            self._empirical_required(
                inclusion_criteria
            )
        )

        content_inclusion = (
            self._content_criteria(
                inclusion_criteria
            )
        )

        content_exclusion = (
            self._content_criteria(
                exclusion_criteria
            )
        )

        prompt = f"""
You are an academic systematic literature
review title-and-abstract screening agent.

RESEARCH TOPIC:
{research_topic}

CONTENT INCLUSION CRITERIA:
{json.dumps(content_inclusion, ensure_ascii=False)}

CONTENT EXCLUSION CRITERIA:
{json.dumps(content_exclusion, ensure_ascii=False)}

EMPIRICAL EVIDENCE REQUIRED:
{empirical_required}

SECONDARY REVIEWS EXCLUDED:
{exclude_reviews}

PAPER TITLE:
{title}

PAPER ABSTRACT:
{abstract}

SCREENING INSTRUCTIONS:

1. Evaluate whether the paper is relevant
   to the user's research topic.

2. Apply the scientific inclusion and
   exclusion criteria.

3. Consider semantic relevance and
   synonyms, not only exact keywords.

4. If empirical evidence is required,
   include only when the title or abstract
   provides evidence of an original
   empirical contribution or evaluation.

5. If the study appears non-empirical
   and empirical evidence is required,
   exclude it when clearly established.
   Otherwise choose uncertain.

6. If secondary reviews are excluded,
   exclude papers clearly identified
   as literature reviews, systematic
   reviews, surveys or meta-analyses.

7. Do not confuse a comparison of models
   with a literature review.

8. Include when sufficient positive
   evidence supports the scientific
   eligibility criteria.

9. Exclude when a criterion is clearly
   violated or the paper is unrelated.

10. Use uncertain when the evidence
    is ambiguous or insufficient.

11. Do not invent datasets, methods,
    results, statistics, or experiments.

12. Do not judge publication year,
    language, or peer-review status.
    These are checked separately.

13. Base the decision only on the
    provided title and abstract.

Return ONLY a JSON object:

{{
  "decision": "include",
  "reason": "Short evidence-based explanation"
}}

Allowed decisions:
include, exclude, uncertain.

/no_think
"""

        try:
            response = self.llm.invoke(
                prompt
            )

            decision, reason = (
                self._parse_ai_response(
                    response.content
                )
            )

        except Exception as error:
            return self._result(
                title,
                "uncertain",
                "AI screening could not be "
                "completed reliably: "
                + str(error)[:160],
                verification_flags,
            )

        # --------------------------------------
        # 7. FINAL PROVISIONAL DECISION
        # --------------------------------------

        # Scientific relevance is separate
        # from publication verification.
        #
        # An include decision is provisional,
        # not final eligibility approval.

        return self._result(
            title=title,
            decision=decision,
            reason=reason,
            verification_flags=verification_flags,
            content_decision=decision,
        )
