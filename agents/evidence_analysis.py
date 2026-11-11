
"""
STEP 8 — GENERIC EVIDENCE ANALYSIS AGENT

Extracts preliminary scientific evidence
from paper abstracts.

Compatible with:
    EvidenceAnalysisAgent().analyze_paper(
        paper,
        research_topic
    )

All extraction is provisional.
Full-text verification remains necessary.
"""

import json
import re

from langchain_ollama import ChatOllama


class EvidenceAnalysisAgent:

    TEXT_FIELDS = [
        "research_objective",
        "methodology",
        "dataset",
        "evaluation_metrics",
        "main_findings",
        "limitations",
    ]

    LIST_FIELDS = [
        "method_names",
        "quantitative_results",
        "reported_comparisons",
        "research_gaps",
        "future_directions",
        "evidence_snippets",
    ]

    FIELD_ALIASES = {
        "research_objective": [
            "objective",
            "study_objective",
            "research_goal",
        ],
        "methodology": [
            "approach",
            "method",
            "research_methodology",
        ],
        "dataset": [
            "datasets",
            "data_source",
            "dataset_used",
            "data",
        ],
        "method_names": [
            "methods",
            "models",
            "algorithms",
            "techniques",
            "models_or_methods",
        ],
        "evaluation_metrics": [
            "metrics",
            "performance_metrics",
        ],
        "main_findings": [
            "findings",
            "results",
            "key_findings",
            "main_results",
        ],
        "quantitative_results": [
            "numerical_results",
            "performance_results",
        ],
        "reported_comparisons": [
            "comparisons",
            "comparative_results",
        ],
        "limitations": [
            "study_limitations",
            "reported_limitations",
        ],
        "research_gaps": [
            "gaps",
            "identified_gaps",
        ],
        "future_directions": [
            "future_work",
            "future_research",
        ],
        "evidence_snippets": [
            "supporting_quotes",
            "evidence_quotes",
            "supporting_evidence",
        ],
    }

    def __init__(
        self,
        model="qwen3:4b",
        max_attempts=3,
        debug=True,
    ):
        self.model = model
        self.max_attempts = max(
            1,
            int(max_attempts),
        )
        self.debug = debug

        self.llm = ChatOllama(
            model=model,
            temperature=0,
            reasoning=False,
            format="json",
            num_predict=1800,
            repeat_penalty=1.1,
        )

    # ==========================================
    # BASIC HELPERS
    # ==========================================

    @staticmethod
    def clean_text(value):
        if value is None:
            return ""

        if isinstance(value, list):
            value = "; ".join(
                str(item)
                for item in value
                if item is not None
            )

        return " ".join(
            str(value).split()
        )

    @classmethod
    def clean_list(cls, value):
        if value is None:
            return []

        if isinstance(value, str):
            value = [value]

        if not isinstance(value, list):
            return []

        result = []
        seen = set()

        for item in value:
            if not isinstance(
                item, (str, int, float)
            ):
                continue

            text = cls.clean_text(item)

            if text.lower() in {
                "",
                "none",
                "unknown",
                "not reported",
                "n/a",
                "null",
            }:
                continue

            key = text.casefold()

            if key not in seen:
                seen.add(key)
                result.append(text)

        return result

    @classmethod
    def default_extraction(cls):
        result = {
            field: "not reported"
            for field in cls.TEXT_FIELDS
        }

        result.update({
            field: []
            for field in cls.LIST_FIELDS
        })

        result["models_or_methods"] = (
            "not reported"
        )

        return result

    # ==========================================
    # RESPONSE PARSING
    # ==========================================

    @staticmethod
    def parse_response(content):
        if isinstance(content, dict):
            data = content

        else:
            if isinstance(content, list):
                content = "".join(
                    part
                    if isinstance(part, str)
                    else str(
                        part.get("text", "")
                    )
                    for part in content
                    if isinstance(part, (str, dict))
                )

            if not isinstance(content, str):
                raise ValueError(
                    "LLM response is not text."
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

                if start < 0 or end <= start:
                    raise ValueError(
                        "No JSON object found."
                    )

                data = json.loads(
                    content[start:end + 1]
                )

        if not isinstance(data, dict):
            raise ValueError(
                "Expected a JSON object."
            )

        if isinstance(
            data.get("extraction"),
            dict,
        ):
            data = data["extraction"]

        return data

    # ==========================================
    # FIELD NORMALIZATION
    # ==========================================

    @classmethod
    def normalize_fields(cls, raw_data):
        extraction = cls.default_extraction()
        warnings = []

        for field in (
            cls.TEXT_FIELDS + cls.LIST_FIELDS
        ):
            value = raw_data.get(field)

            if value is None:
                for alias in cls.FIELD_ALIASES.get(
                    field,
                    [],
                ):
                    if alias in raw_data:
                        value = raw_data[alias]
                        break

            if value is None:
                warnings.append(
                    f"Missing field: {field}"
                )
                continue

            if field in cls.LIST_FIELDS:
                extraction[field] = (
                    cls.clean_list(value)
                )

            else:
                extraction[field] = (
                    cls.clean_text(value)
                    or "not reported"
                )

        return extraction, warnings

    # ==========================================
    # NUMERICAL VALIDATION
    # ==========================================

    @staticmethod
    def extract_numbers(text):
        return re.findall(
            r"(?<![A-Za-z0-9])"
            r"\d[\d,]*(?:\.\d+)?%?",
            str(text),
        )

    @staticmethod
    def normalize_number(value):
        return value.replace(",", "")

    @classmethod
    def numbers_are_supported(
        cls,
        extracted_text,
        abstract,
    ):
        source_numbers = {
            cls.normalize_number(number)
            for number in cls.extract_numbers(
                abstract
            )
        }

        extracted_numbers = {
            cls.normalize_number(number)
            for number in cls.extract_numbers(
                extracted_text
            )
        }

        return extracted_numbers.issubset(
            source_numbers
        )

    # ==========================================
    # EXTRACTION VALIDATION
    # ==========================================

    @classmethod
    def validate_extraction(
        cls,
        extraction,
        abstract,
    ):
        warnings = []

        for field in cls.TEXT_FIELDS:
            value = extraction[field]

            if not cls.numbers_are_supported(
                value,
                abstract,
            ):
                warnings.append(
                    f"Unsupported number in {field}"
                )
                extraction[field] = (
                    "not reported"
                )

        for field in cls.LIST_FIELDS:
            if field == "evidence_snippets":
                continue

            accepted = []

            for item in extraction[field]:
                if cls.numbers_are_supported(
                    item,
                    abstract,
                ):
                    accepted.append(item)

                else:
                    warnings.append(
                        "Unsupported number in "
                        f"{field}: {item[:80]}"
                    )

            extraction[field] = accepted

        normalized_abstract = re.sub(
            r"\s+",
            " ",
            abstract,
        ).casefold()

        valid_snippets = []

        for snippet in extraction[
            "evidence_snippets"
        ]:
            normalized_snippet = re.sub(
                r"\s+",
                " ",
                snippet,
            ).casefold()

            if (
                normalized_snippet
                and normalized_snippet
                in normalized_abstract
            ):
                valid_snippets.append(
                    snippet
                )
            else:
                warnings.append(
                    "Unsupported evidence quotation."
                )

        extraction[
            "evidence_snippets"
        ] = valid_snippets

        methods = []

        for method in extraction[
            "method_names"
        ]:
            if (
                len(method) <= 80
                and len(method.split()) <= 10
                and method not in methods
            ):
                methods.append(method)

        extraction["method_names"] = methods

        extraction["models_or_methods"] = (
            ", ".join(methods)
            if methods
            else "not reported"
        )

        return extraction, warnings

    # ==========================================
    # EVIDENCE AVAILABILITY
    # ==========================================

    @classmethod
    def has_useful_evidence(cls, extraction):
        return (
            any(
                extraction[field].strip().lower()
                not in {
                    "",
                    "not reported",
                    "unknown",
                    "none",
                }
                for field in cls.TEXT_FIELDS
            )
            or any(
                extraction[field]
                for field in cls.LIST_FIELDS
            )
        )

    # ==========================================
    # PROMPT
    # ==========================================

    def _build_prompt(
        self,
        paper,
        research_topic,
        short=False,
    ):
        title = self.clean_text(
            paper.get("title")
        )

        abstract = self.clean_text(
            paper.get("abstract")
        )

        schema = {
            field: (
                ""
                if field in self.TEXT_FIELDS
                else []
            )
            for field in (
                self.TEXT_FIELDS + self.LIST_FIELDS
            )
        }

        if short:
            instructions = """
Extract only the information that is
explicitly stated in the abstract.

Keep every answer brief.

Use "not reported" for absent text fields.
Use [] for absent list fields.

Return a complete flat JSON object.
Do not return an empty object.
"""
        else:
            instructions = """
Extract:
- research objective
- methodology
- dataset
- method names
- evaluation metrics
- main findings
- quantitative results
- comparisons
- limitations
- research gaps
- future directions
- short verbatim evidence snippets

Use only the supplied abstract.

Do not invent facts.

Do not invent numerical values.

Use "not reported" for missing text.
Use [] for missing lists.

Keep all values short and factual.

Return a complete flat JSON object.
Do not return an empty object.
"""

        return f"""
You are an academic evidence extraction agent.

RESEARCH TOPIC:
{research_topic}

PAPER TITLE:
{title}

ABSTRACT:
{abstract}

INSTRUCTIONS:
{instructions}

REQUIRED JSON STRUCTURE:
{json.dumps(schema, ensure_ascii=False)}

Return JSON only.

/no_think
"""

    # ==========================================
    # CONSERVATIVE FALLBACK
    # ==========================================

    @classmethod
    def extract_verbatim_fallback(cls, abstract):
        """
        If Qwen fails, retain only exact
        sentences from the abstract.

        No inferred methods or results.
        """

        extraction = cls.default_extraction()

        sentences = re.split(
            r"(?<=[.!?])\s+",
            abstract.strip(),
        )

        sentences = [
            sentence.strip()
            for sentence in sentences
            if sentence.strip()
        ]

        if not sentences:
            return extraction

        # Preserve source sentences rather
        # than inventing a summary.

        extraction["evidence_snippets"] = (
            sentences[:3]
        )

        # These are source excerpts, not
        # independently validated findings.
        extraction["main_findings"] = (
            "not reported"
        )

        return extraction

    # ==========================================
    # EMPTY RESULT
    # ==========================================

    @classmethod
    def empty_result(
        cls,
        title,
        reason,
    ):
        return {
            "title": title,
            "status": "manual_review_required",
            "extraction": (
                cls.default_extraction()
            ),
            "quality_appraisal": {
                "rating": "not_assessable",
                "strengths": [],
                "concerns": [reason],
                "reason": reason,
            },
            "requires_full_text_review": True,
        }

    # ==========================================
    # MAIN ANALYSIS
    # ==========================================

    def analyze_paper(
        self,
        paper,
        research_topic,
    ):
        title = self.clean_text(
            paper.get("title")
        )

        abstract = self.clean_text(
            paper.get("abstract")
        )

        if not abstract:
            result = self.empty_result(
                title,
                "Abstract unavailable.",
            )

            result["status"] = (
                "insufficient_evidence"
            )

            return result

        last_error = None

        for attempt in range(
            1,
            self.max_attempts + 1,
        ):
            short_prompt = (
                attempt > 1
            )

            print(
                f"\n[Evidence] {title}"
            )

            print(
                "[Evidence] Attempt "
                f"{attempt}/{self.max_attempts}"
            )

            prompt = self._build_prompt(
                paper,
                research_topic,
                short=short_prompt,
            )

            try:
                response = self.llm.invoke(
                    prompt
                )

                if self.debug:
                    print(
                        "[Evidence DEBUG] Raw response:",
                        str(response.content)[:1200]
                    )

                raw_data = self.parse_response(
                    response.content
                )

                if self.debug:
                    print(
                        "[Evidence DEBUG] Parsed keys:",
                        list(raw_data.keys())
                    )

                extraction, warnings = (
                    self.normalize_fields(
                        raw_data
                    )
                )

                extraction, validation_warnings = (
                    self.validate_extraction(
                        extraction,
                        abstract,
                    )
                )

                warnings.extend(
                    validation_warnings
                )

                if not self.has_useful_evidence(
                    extraction
                ):
                    raise ValueError(
                        "No useful scientific evidence "
                        "was returned by Qwen."
                    )

                print(
                    "[Evidence] Dataset:",
                    extraction["dataset"]
                )

                print(
                    "[Evidence] Methods:",
                    extraction["method_names"]
                )

                print(
                    "[Evidence] Metrics:",
                    extraction[
                        "evaluation_metrics"
                    ]
                )

                print(
                    "[Evidence] Findings:",
                    extraction[
                        "main_findings"
                    ][:180]
                )

                if warnings:
                    print(
                        "[Evidence] Warnings:",
                        warnings
                    )

                return {
                    "title": title,
                    "status": (
                        "manual_review_required"
                        if warnings
                        else "analyzed"
                    ),
                    "extraction": extraction,
                    "quality_appraisal": {
                        "rating": "preliminary_only",
                        "strengths": [],
                        "concerns": warnings,
                        "reason": (
                            "Automated abstract-based "
                            "extraction. Full-text "
                            "verification required."
                        ),
                    },
                    "requires_full_text_review": True,
                }

            except Exception as error:
                last_error = error

                print(
                    "[Evidence WARNING] "
                    f"Attempt {attempt} failed: "
                    f"{error}"
                )

        # ======================================
        # FALLBACK — VERBATIM ABSTRACT EVIDENCE
        # ======================================

        fallback = self.extract_verbatim_fallback(
            abstract
        )

        if fallback["evidence_snippets"]:
            print(
                "[Evidence] Using conservative "
                "verbatim fallback."
            )

            return {
                "title": title,
                "status": "manual_review_required",
                "extraction": fallback,
                "quality_appraisal": {
                    "rating": "not_assessable",
                    "strengths": [],
                    "concerns": [
                        (
                            "Structured evidence "
                            "extraction failed."
                        ),
                        str(last_error),
                    ],
                    "reason": (
                        "Only verbatim abstract "
                        "excerpts were retained. "
                        "No structured scientific "
                        "findings were inferred."
                    ),
                },
                "requires_full_text_review": True,
            }

        return self.empty_result(
            title,
            (
                "Evidence extraction failed: "
                f"{last_error}"
            ),
        )
