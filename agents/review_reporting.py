
"""
STEP 9 — REVIEW REPORTING AGENT V4

Topic-independent preliminary systematic literature review.

Outputs:
    data/outputs/synthesis_report.json
    data/outputs/quality_assurance.json
    data/outputs/prisma_preliminary.json

Main improvements:
- Ollama JSON-schema structured output
- Explicit non-thinking mode for Qwen3
- One Ollama request for all six academic sections
- Validation of generated paragraphs and citations
- Deterministic fallback if Ollama fails
- Improved research-question evidence matching
- Preservation of existing workflow and PDF output keys

IMPORTANT:
This is an automated abstract-level preliminary review.
It does not replace full-text assessment or human validation.
"""

import json
import re
import urllib.request
import urllib.error

from collections import Counter
from pathlib import Path


# ============================================================
# CONSTANTS
# ============================================================

MISSING = {
    "",
    "none",
    "null",
    "unknown",
    "n/a",
    "not reported",
    "not specified",
    "not available",
    "not applicable",
}

STOPWORDS = set("""
a an the and or of to in on for with from by at as is
are was were be been this that these those which what how
why when where can could do does did using used use based
among between their its into through study studies research
paper papers different main most existing results
""".split())

GENERIC = set("""
method methods algorithm algorithms approach approaches
technique techniques model models framework frameworks
metric metrics measure measures evaluation evaluate
performance comparison comparative compare compared
findings reported classification
""".split())

ACADEMIC_SECTIONS = [
    "introduction",
    "background_related_work",
    "discussion_main_findings",
    "comparison_existing_literature",
    "strengths_weaknesses",
    "implications",
]


# ============================================================
# TEXT UTILITIES
# ============================================================

def clean_text(value):

    if value is None:
        return ""

    if isinstance(value, (dict, list)):
        return json.dumps(
            value,
            ensure_ascii=False,
            default=str
        )

    text = " ".join(str(value).split())

    text = re.sub(
        r"\bF\s*:\s*score\b",
        "F1-score",
        text,
        flags=re.I
    )

    text = re.sub(
        r"state-of-the:art",
        "state-of-the-art",
        text,
        flags=re.I
    )

    return re.sub(r"\.{2,}", ".", text)


def is_reported(value):

    if isinstance(value, (dict, list)):
        return bool(value)

    return clean_text(value).casefold() not in MISSING


def display_value(value):

    if is_reported(value):
        return clean_text(value)

    return "not reported"


def clean_list(value):

    if isinstance(value, list):
        return [
            clean_text(item)
            for item in value
            if is_reported(item)
        ]

    if is_reported(value):
        return [clean_text(value)]

    return []


def shorten(value, limit=350):

    text = clean_text(value)

    if len(text) <= limit:
        return text

    shortened = text[:limit].rsplit(" ", 1)[0]

    return shortened + "..."


def sentence(value, limit=350):

    text = shorten(value, limit).rstrip(" .")

    return text + "." if text else ""


def tokenize(value):

    words = re.findall(
        r"[a-z][a-z0-9-]*",
        clean_text(value).lower()
    )

    return {
        word
        for word in words
        if len(word) >= 3
        and word not in STOPWORDS
    }


def record_id(paper):

    doi = clean_text(
        paper.get("doi")
    ).lower()

    doi = re.sub(
        r"^https?://(?:dx\.)?doi\.org/",
        "",
        doi
    )

    if doi:
        return "doi:" + doi

    title = re.sub(
        r"\W+",
        "",
        clean_text(
            paper.get("title")
        ).lower()
    )

    return "title:" + title


def normalize_questions(protocol):

    questions = (
        protocol.get("research_questions")
        or []
    )

    if isinstance(questions, str):
        questions = [questions]

    result = []

    for item in questions:

        if isinstance(item, dict):
            question = (
                item.get("question")
                or item.get("text")
                or ""
            )
        else:
            question = item

        if clean_text(question):
            result.append(
                clean_text(question)
            )

    return result


def canonical_method(name):
    """Conservatively merge spelling variants, without merging different models."""
    value = clean_text(name)
    low = value.casefold()
    if re.search(r"\bshap\b|shapley additive", low):
        return "SHAP"
    if re.search(r"\blime\b|local interpretable model-agnostic", low):
        return "LIME"
    if re.search(r"\bxgboost\b", low):
        return "XGBoost"
    if re.search(r"\blightgbm\b", low):
        return "LightGBM"
    if re.search(r"\brandom forests?\b", low):
        return "Random Forest"
    if re.search(r"\bdecision trees?\b", low):
        return "Decision Tree"
    if re.search(r"\blogistic regression\b", low):
        return "Logistic Regression"
    return value


def unique_strings(items):

    result = []
    seen = set()

    for item in items:

        value = clean_text(item)
        key = value.lower()

        if value and key not in seen:
            seen.add(key)
            result.append(value)

    return result


# ============================================================
# REVIEW REPORTING AGENT
# ============================================================

class ReviewReportingAgent:

    def __init__(
        self,
        output_dir="data/outputs",
        model="qwen3:4b",
        use_llm=True,
        ollama_url="http://127.0.0.1:11434/api/generate",
        timeout=600
    ):

        self.output_dir = Path(output_dir)

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.model = model
        self.use_llm = use_llm
        self.ollama_url = ollama_url
        self.timeout = timeout

        self._ollama_failed = False
        self._ollama_error = None
        self._narrative_source = "deterministic_fallback"

    # ========================================================
    # SAVE JSON
    # ========================================================

    def save(self, filename, data):

        path = self.output_dir / filename

        path.write_text(
            json.dumps(
                data,
                indent=2,
                ensure_ascii=False,
                default=str
            ),
            encoding="utf-8"
        )

        return str(path)

    # ========================================================
    # OLLAMA — STRUCTURED ACADEMIC OUTPUT
    # ========================================================

    def _call_ollama(
        self,
        prompt,
        max_tokens=1000
    ):

        section_properties = {
            name: {
                "type": "string"
            }
            for name in ACADEMIC_SECTIONS
        }

        schema = {
            "type": "object",
            "properties": section_properties,
            "required": ACADEMIC_SECTIONS,
            "additionalProperties": False
        }

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "format": schema,
            "options": {
                "temperature": 0.1,
                "num_predict": max_tokens,
                "num_ctx": 4096
            }
        }

        request = urllib.request.Request(
            self.ollama_url,
            data=json.dumps(
                payload
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json"
            }
        )

        try:

            with urllib.request.urlopen(
                request,
                timeout=self.timeout
            ) as response:

                outer = json.loads(
                    response.read().decode("utf-8")
                )

        except urllib.error.HTTPError as exc:

            detail = exc.read().decode(
                "utf-8",
                errors="replace"
            )

            raise RuntimeError(
                f"Ollama HTTP {exc.code}: "
                f"{detail[:300]}"
            ) from exc

        content = outer.get("response") or ""

        content = re.sub(
            r"<think>.*?</think>",
            "",
            content,
            flags=re.S
        ).strip()

        if not content:

            raise ValueError(
                "Ollama returned an empty response."
            )

        try:

            result = json.loads(content)

        except json.JSONDecodeError as exc:

            raise ValueError(
                "Ollama returned invalid JSON: "
                + content[:250]
            ) from exc

        if not isinstance(result, dict):

            raise ValueError(
                "Ollama returned JSON that is not an object."
            )

        return result

    # ========================================================
    # EVIDENCE VALIDATION
    # ========================================================

    def _usable_extraction(
        self,
        analysis,
        extraction
    ):

        status = clean_text(
            analysis.get("status")
        ).lower()

        if status not in {
            "analyzed",
            "manual_review_required"
        }:
            return False

        quality = (
            analysis.get("quality_appraisal")
            or {}
        )

        reason = clean_text(
            quality.get("reason")
        ).lower()

        if (
            "only verbatim abstract" in reason
            or "structured evidence extraction failed" in reason
        ):
            return False

        fields = [
            "research_objective",
            "methodology",
            "dataset",
            "evaluation_metrics",
            "main_findings",
            "limitations",
            "method_names",
            "algorithms",
            "models_or_methods",
            "quantitative_results",
            "reported_comparisons",
            "research_gaps",
            "future_directions"
        ]

        return any(
            is_reported(extraction.get(field))
            for field in fields
        )

    # ========================================================
    # BUILD STUDY SUMMARIES
    # ========================================================

    def _build_studies(self, evidence):

        studies = []
        issues = []
        methods = Counter()

        for index, item in enumerate(
            evidence,
            start=1
        ):

            paper = item.get("paper") or {}

            analysis = (
                item.get("analysis")
                or {}
            )

            extraction = (
                analysis.get("extraction")
                or {}
            )

            quality = (
                analysis.get("quality_appraisal")
                or {}
            )

            usable = self._usable_extraction(
                analysis,
                extraction
            )

            data = extraction if usable else {}

            names = clean_list(
                data.get("method_names")
                or data.get("algorithms")
                or data.get("models_or_methods")
            )

            if len(names) == 1 and (
                "," in names[0]
                or ";" in names[0]
            ):

                names = [
                    value.strip()
                    for value in re.split(
                        r"[,;]",
                        names[0]
                    )
                    if value.strip()
                ]

            names = unique_strings(
                canonical_method(name)
                for name in names
                if len(name) <= 100
            )

            methods.update(names)

            flags = []

            if paper.get(
                "peer_review_verified"
            ) is not True:

                flags.append(
                    "Peer-review status requires verification."
                )

            if clean_text(
                paper.get("source")
            ).lower() == "arxiv":

                flags.append(
                    "Preprint publication status requires verification."
                )

            if analysis.get(
                "requires_full_text_review",
                True
            ):

                flags.append(
                    "Full-text verification required."
                )

            if not usable:

                flags.append(
                    "Structured evidence extraction unavailable."
                )

            if analysis.get(
                "status"
            ) == "manual_review_required":

                flags.append(
                    "Automated extraction requires manual review."
                )

            for concern in clean_list(
                quality.get("concerns")
            ):

                flags.append(
                    "Extraction concern: "
                    + shorten(concern, 180)
                )

            study = {
                "reference_number": index,
                "record_id": record_id(paper),
                "title": (
                    paper.get("title")
                    or "Untitled"
                ),
                "year": paper.get("year"),
                "source": paper.get("source"),
                "doi": paper.get("doi"),
                "url": (
                    paper.get("url")
                    or paper.get("paper_url")
                    or paper.get("arxiv_url")
                ),
                "authors": paper.get("authors"),
                "abstract": clean_text(
                    paper.get("abstract")
                ),
                "methods_mentioned_in_abstract": names,
                "research_objective": display_value(
                    data.get("research_objective")
                ),
                "methodology": display_value(
                    data.get("methodology")
                ),
                "dataset": display_value(
                    data.get("dataset")
                ),
                "evaluation_metrics": display_value(
                    data.get("evaluation_metrics")
                ),
                "reported_findings": display_value(
                    data.get("main_findings")
                ),
                "quantitative_results": clean_list(
                    data.get("quantitative_results")
                ),
                "reported_comparisons": clean_list(
                    data.get("reported_comparisons")
                ),
                "limitations": display_value(
                    data.get("limitations")
                ),
                "research_gaps": clean_list(
                    data.get("research_gaps")
                ),
                "future_directions": clean_list(
                    data.get("future_directions")
                ),
                "evidence_snippets": clean_list(
                    extraction.get("evidence_snippets")
                ),
                "quality_status": quality.get(
                    "rating",
                    "not_assessable"
                ),
                "quality_concerns": clean_list(
                    quality.get("concerns")
                ),
                "analysis_status": analysis.get(
                    "status",
                    "unknown"
                ),
                "structured_evidence_available": usable,
                "verification_flags": unique_strings(flags),
                "eligibility_status": "provisional"
            }

            studies.append(study)

            if flags:

                issues.append({
                    "title": study["title"],
                    "issues": study[
                        "verification_flags"
                    ]
                })

        return studies, issues, methods

    # ========================================================
    # RESEARCH QUESTION MATCHING
    # ========================================================

    def _match_rq_studies(
        self,
        question,
        studies
    ):

        question_terms = tokenize(question)

        specific_terms = (
            question_terms - GENERIC
        )

        matches = []

        for study in studies:

            if not study[
                "structured_evidence_available"
            ]:
                continue

            evidence_text = " ".join(
                clean_text(study.get(field))
                for field in [
                    "title",
                    "research_objective",
                    "methodology",
                    "dataset",
                    "evaluation_metrics",
                    "reported_findings",
                    "methods_mentioned_in_abstract",
                    "reported_comparisons",
                    "quantitative_results"
                ]
            )

            evidence_terms = tokenize(
                evidence_text
            )

            overlap = (
                question_terms & evidence_terms
            )

            specific_overlap = (
                specific_terms & evidence_terms
            )

            coverage = (
                len(overlap)
                / max(1, len(question_terms))
            )

            specific_coverage = (
                len(specific_overlap)
                / len(specific_terms)
                if specific_terms
                else coverage
            )

            score = (
                0.45 * coverage
                + 0.55 * specific_coverage
            )

            # Generic evidence-type questions need
            # special handling. These checks require
            # actual extracted fields, not just keywords.

            question_lower = question.lower()

            generic_match = False

            if not specific_terms:

                if any(
                    word in question_lower
                    for word in [
                        "method",
                        "algorithm",
                        "classification",
                        "technique",
                        "model"
                    ]
                ):

                    generic_match = bool(
                        study[
                            "methods_mentioned_in_abstract"
                        ]
                    )

                elif any(
                    word in question_lower
                    for word in [
                        "metric",
                        "measure",
                        "evaluation"
                    ]
                ):

                    generic_match = is_reported(
                        study["evaluation_metrics"]
                    )

                elif any(
                    word in question_lower
                    for word in [
                        "compar",
                        "finding",
                        "result"
                    ]
                ):

                    generic_match = bool(
                        study["reported_comparisons"]
                    ) or is_reported(
                        study["reported_findings"]
                    )

                if generic_match:
                    score = max(score, 0.60)

            # For substantive RQs, require overlap
            # with their specific terminology.

            if specific_terms:

                if not specific_overlap:
                    continue

                if score < 0.20:
                    continue

            elif not generic_match and score < 0.20:
                continue

            matches.append({
                "study": study,
                "relevance_score": round(
                    score,
                    4
                ),
                "matched_terms": sorted(
                    overlap
                )
            })

        matches.sort(
            key=lambda item: (
                -item["relevance_score"],
                item["study"]["reference_number"]
            )
        )

        return matches

    # ========================================================
    # RESEARCH QUESTION ANSWERS
    # ========================================================

    def _rq_answer(self, question, studies):
        """Summarize only evidence relevant to the requested RQ dimension."""
        matches = self._match_rq_studies(question, studies)
        q = question.lower()

        if not matches:
            return {
                "question": question,
                "supporting_studies": [],
                "answer_status": "Insufficient matched evidence",
                "evidence_based_observation": (
                    "No sufficiently relevant abstract-level evidence was "
                    "identified for this research question. Further retrieval "
                    "and full-text verification are required."
                ),
            }

        challenge_terms = (
            "challenge", "limitation", "ethical", "operational",
            "barrier", "adoption", "fairness", "bias", "regulatory",
            "compliance", "constraint", "obstacle",
        )
        performance_terms = (
            "performance", "accuracy", "precision", "recall",
            "f1", "auc", "metric", "effectiveness", "predictive",
            "evaluation", "benchmark",
        )
        method_terms = (
            "method", "technique", "algorithm", "approach",
            "interpretability", "explainability", "classification",
        )

        # Challenge questions take precedence over questions also
        # mentioning models or their performance.
        is_challenge = any(term in q for term in challenge_terms)
        is_performance = not is_challenge and any(
            term in q for term in performance_terms
        )
        is_method = not is_challenge and not is_performance and any(
            term in q for term in method_terms
        )

        supporting = []
        observations = []
        for match in matches:
            study = match["study"]
            ref = f"[{study['reference_number']}]"
            details = []

            if is_challenge:
                if is_reported(study["limitations"]):
                    details.append(sentence(study["limitations"], 220))
                details.extend(
                    "Author-reported gap: " + sentence(gap, 180)
                    for gap in study["research_gaps"][:2]
                    if is_reported(gap)
                    and "not reported" not in gap.lower()
                )
                # Do not convert a generic method list into evidence of a challenge.
            elif is_performance:
                if is_reported(study["evaluation_metrics"]):
                    details.append(
                        "Reported evaluation measures: "
                        + sentence(study["evaluation_metrics"], 220)
                    )
                details.extend(
                    "Reported quantitative result: " + sentence(value, 150)
                    for value in study["quantitative_results"][:2]
                )
                details.extend(
                    "Reported comparison: " + sentence(value, 180)
                    for value in study["reported_comparisons"][:1]
                )
            elif is_method:
                names = study["methods_mentioned_in_abstract"]
                if names:
                    details.append("Methods identified: " + ", ".join(names) + ".")
                details.extend(
                    "Reported comparison: " + sentence(value, 180)
                    for value in study["reported_comparisons"][:1]
                )
            elif is_reported(study["reported_findings"]):
                details.append(sentence(study["reported_findings"], 250))

            # A keyword match is not enough to claim RQ-specific support.
            if not details:
                continue

            supporting.append({
                "reference_number": study["reference_number"],
                "title": study["title"],
                "doi": study["doi"],
                "year": study["year"],
                "relevance_score": match["relevance_score"],
            })
            observations.append(f"{ref} " + " ".join(details))

        if not observations:
            return {
                "question": question,
                "supporting_studies": [],
                "answer_status": "Insufficient RQ-specific extracted evidence",
                "evidence_based_observation": (
                    "Candidate studies were identified by keyword matching, "
                    "but their extracted information does not directly "
                    "answer this research question. This is an evidence "
                    "gap in the current sample, not proof that the issue "
                    "has not been studied."
                ),
            }

        intro = (
            f"{len(supporting)} candidate studies provide extracted "
            "information relevant to this research question. "
            "The following observations are preliminary."
        )
        conclusion = (
            "These observations require source-level verification; "
            "missing details must not be interpreted as negative findings."
        )
        return {
            "question": question,
            "supporting_studies": supporting,
            "answer_status": "Preliminary RQ-specific evidence map",
            "evidence_based_observation": "\n\n".join(
                [intro] + observations[:8] + [conclusion]
            ),
        }

    # ========================================================
    # ACADEMIC WRITING — SINGLE OLLAMA REQUEST
    # ========================================================

    def _generate_academic_narrative(self, topic, studies, questions, fallback):
        """Topic-independent synthesis of every usable study in resumable batches."""
        if not self.use_llm:
            return fallback
        try:
            from agents.batch_synthesis import synthesize
            sections, audit = synthesize(self, topic, studies, questions)
            self._batch_synthesis_audit = audit
            self._batch_extra_sections = sections
            self._narrative_source = "ollama_batched_all_studies"
            return {key: [sections[key]] for key in ACADEMIC_SECTIONS}
        except Exception as exc:
            self._ollama_failed = True
            self._ollama_error = str(exc)
            print("[Reporting] Batch synthesis incomplete:", str(exc)[:250])
            print("[Reporting] Using preliminary deterministic fallback; no partial LLM claims.")
            return fallback

    # ========================================================
    # ACADEMIC SECTIONS
    # ========================================================

    def _academic_sections(
        self,
        topic,
        studies,
        questions,
        methods,
        gaps,
        limitations
    ):

        usable = [
            study
            for study in studies
            if study[
                "structured_evidence_available"
            ]
        ]

        total = len(studies)

        with_dataset = sum(
            is_reported(study["dataset"])
            for study in usable
        )

        with_metrics = sum(
            is_reported(study["evaluation_metrics"])
            for study in usable
        )

        with_quantitative = sum(
            bool(study["quantitative_results"])
            for study in usable
        )

        method_summary = ", ".join(
            f"{name} ({count})"
            for name, count in methods.most_common(8)
        )

        if not method_summary:
            method_summary = (
                "no reliably extracted methods"
            )

        abstract = (
            f"This preliminary literature review examines "
            f"{topic}. The automated workflow produced "
            f"{total} provisional study records, of which "
            f"{len(usable)} contain structured abstract-level "
            f"evidence. Identified method mentions include "
            f"{method_summary}. Dataset descriptions were "
            f"available for {with_dataset} records, "
            f"evaluation metrics for {with_metrics}, "
            f"and quantitative results for "
            f"{with_quantitative}. The resulting evidence "
            "map is descriptive and requires full-text "
            "verification before definitive conclusions."
        )

        fallback = {
            "introduction": [
                (
                    f"This preliminary review investigates "
                    f"{topic} through {len(questions)} "
                    "research questions. Its purpose is to "
                    "identify candidate studies, summarize "
                    "available methodological evidence, and "
                    "highlight issues requiring further "
                    "investigation. The current synthesis "
                    "is based on abstracts and therefore "
                    "remains provisional."
                )
            ],
            "background_related_work": [
                (
                    "The extracted records describe "
                    f"methods including {method_summary}. "
                    "These observations provide an initial "
                    "description of the approaches represented "
                    "in the retrieved sample. Their frequency "
                    "of mention does not establish either "
                    "field-wide prevalence or comparative "
                    "effectiveness."
                )
            ],
            "discussion_main_findings": [
                (
                    f"Among {total} provisional records, "
                    f"{len(usable)} yielded usable structured "
                    "evidence. The extracted information "
                    "identifies candidate methods and "
                    "reported observations, but incomplete "
                    "experimental details restrict "
                    "interpretation. Claims about effectiveness "
                    "must therefore be checked against the "
                    "original publications."
                )
            ],
            "comparison_existing_literature": [
                (
                    "Meaningful comparisons across studies "
                    "require compatible datasets, evaluation "
                    "metrics, experimental conditions, and "
                    "verified outcomes. These conditions "
                    "cannot be assumed from the available "
                    "abstracts. Consequently, the present "
                    "review does not establish an overall "
                    "ranking of methods."
                )
            ],
            "strengths_weaknesses": [
                (
                    "The available evidence provides an "
                    "initial basis for identifying reported "
                    "methodological contributions. However, "
                    "the completeness of experimental design, "
                    "validation procedures, and potential "
                    "sources of bias cannot be established "
                    "without examining full texts."
                )
            ],
            "implications": [
                (
                    "The preliminary synthesis can guide "
                    "the selection of studies for full-text "
                    "assessment and identify candidate "
                    "directions for further investigation. "
                    "Practical recommendations remain "
                    "tentative until reported findings, "
                    "study eligibility, and methodological "
                    "quality have been verified."
                )
            ]
        }

        generated = self._generate_academic_narrative(
            topic,
            studies,
            questions,
            fallback
        )

        challenges = [
            (
                f"{total - len(usable)} of {total} "
                "provisional records lack usable "
                "structured evidence."
            ),
            (
                "Abstract-level information is insufficient "
                "for comprehensive risk-of-bias assessment."
            ),
            (
                "Cross-study comparisons require verification "
                "of datasets, metrics, and evaluation settings."
            )
        ]

        future = [
            (
                "Verify publication status, full-text "
                "availability, and eligibility decisions."
            ),
            (
                "Validate numerical findings against "
                "the original scientific publications."
            ),
            (
                "Expand and document searches and complete "
                "the required PRISMA reporting information."
            ),
            (
                "Validate research-question matches before "
                "drawing definitive conclusions."
            )
        ]

        conclusion = (
            f"This preliminary review mapped {total} "
            f"provisional records concerning {topic}. "
            f"Structured abstract-level evidence was "
            f"available for {len(usable)} records. "
            "The synthesis identifies candidate methods, "
            "observations, and research gaps, but does "
            "not constitute a completed systematic review. "
            "Broader retrieval, full-text assessment, "
            "and independent verification remain necessary."
        )

        extras = getattr(self, "_batch_extra_sections", {})
        if extras:
            challenges = [extras["open_challenges"]]
            future = [extras["future_recommendations"]]
            conclusion = extras["conclusion"]
        return {
            "abstract": abstract,
            **generated,
            "open_challenges": challenges,
            "future_recommendations": future,
            "limitations_threats_to_validity": limitations,
            "conclusion": conclusion
        }

    # ========================================================
    # MAIN WORKFLOW
    # ========================================================

    def run(self, state):

        self._ollama_failed = False
        self._ollama_error = None
        self._narrative_source = "deterministic_fallback"
        self._batch_extra_sections = {}
        self._batch_synthesis_audit = {}

        screening = (
            state.get("screening_results")
            or []
        )

        evidence = (
            state.get("evidence_results")
            or []
        )

        protocol = (
            state.get("protocol")
            or {}
        )

        retrieved = (
            state.get("retrieved_papers")
            or []
        )

        dedup = (
            state.get("deduplication_result")
            or {}
        )

        topic = (
            state.get("research_topic")
            or protocol.get("research_topic")
            or "Unknown research topic"
        )

        studies, issues, method_counts = (
            self._build_studies(evidence)
        )

        # Record only sources actually present in executed retrieval.
        searched_databases = sorted({
            clean_text(p.get("source"))
            for p in retrieved if isinstance(p, dict)
            and clean_text(p.get("source")) in {"OpenAlex", "arXiv"}
        })

        decisions = Counter(
            clean_text(
                item.get(
                    "decision",
                    "uncertain"
                )
            ).lower()
            for item in screening
        )

        included = decisions["include"]
        excluded = decisions["exclude"]
        uncertain = decisions["uncertain"]

        unique = dedup.get("unique_papers")

        after_dedup = (
            len(unique)
            if isinstance(unique, list)
            else None
        )

        duplicates_removed = (
            max(
                0,
                len(retrieved) - after_dedup
            )
            if retrieved and after_dedup is not None
            else None
        )

        # ----------------------------------------------------
        # PRELIMINARY PRISMA
        # ----------------------------------------------------

        prisma = {
            "report_type": (
                "preliminary_prisma_style_counts"
            ),
            "status": "provisional",
            "records_identified": (
                len(retrieved)
                if retrieved
                else None
            ),
            "duplicates_removed": duplicates_removed,
            "records_after_deduplication": after_dedup,
            "records_screened_title_abstract": len(screening),
            "records_provisionally_included": included,
            "records_excluded_title_abstract": excluded,
            "records_uncertain": uncertain,
            "reports_sought_for_retrieval": None,
            "reports_not_retrieved": None,
            "reports_assessed_for_full_text_eligibility": None,
            "reports_excluded_after_full_text": None,
            "studies_finally_included": None,
            "requires_human_review": True,
            "note": (
                "Preliminary abstract-based screening only. "
                "Full-text PRISMA counts are unavailable."
            )
        }

        # ----------------------------------------------------
        # RESEARCH QUESTIONS
        # ----------------------------------------------------

        questions = normalize_questions(
            protocol
        )

        rq_discussion = [
            self._rq_answer(
                question,
                studies
            )
            for question in questions
        ]

        # ----------------------------------------------------
        # RESEARCH GAPS
        # ----------------------------------------------------

        gaps = []

        for study in studies:

            if not study[
                "structured_evidence_available"
            ]:
                continue

            for gap in study["research_gaps"]:
                if not is_reported(gap) or "not reported" in gap.lower():
                    continue
                gaps.append(
                    f"Author-reported in "
                    f"[{study['reference_number']}]: "
                    f"{sentence(gap)}"
                )

        if not gaps:

            gaps.append(
                "No explicit author-reported research "
                "gaps were reliably extracted from "
                "the available abstracts."
            )

        gaps.extend([
            (
                "Review-level inference: abstract-only "
                "extraction limits synthesis completeness."
            ),
            (
                "Review-level inference: incomplete "
                "methodological information limits "
                "cross-study comparison."
            )
        ])

        # ----------------------------------------------------
        # LIMITATIONS
        # ----------------------------------------------------

        limitations = [
            "The current retrieval may miss relevant studies.",
            "Screening decisions remain provisional.",
            "Peer-review status requires verification.",
            (
                "Evidence was extracted from abstracts "
                "rather than verified full texts."
            ),
            (
                "Research-question matching requires "
                "human validation."
            ),
            (
                "Numerical findings require source-level "
                "verification."
            ),
            (
                "A complete risk-of-bias assessment "
                "has not been performed."
            ),
            (
                "PRISMA-style counts are preliminary "
                "rather than final."
            )
        ]

        # ----------------------------------------------------
        # SCIENTIFIC WRITING
        # ----------------------------------------------------

        academic = self._academic_sections(
            topic,
            studies,
            questions,
            method_counts,
            gaps,
            limitations
        )

        # ----------------------------------------------------
        # THEMATIC SYNTHESIS
        # ----------------------------------------------------

        usable_count = sum(
            study[
                "structured_evidence_available"
            ]
            for study in studies
        )

        themes = []

        for method, count in (
            method_counts.most_common()
        ):

            themes.append({
                "theme": method,
                "studies_mentioning_theme": count,
                "interpretation": (
                    f"{count} of {usable_count} records "
                    "with structured evidence mention "
                    f"{method}. This does not establish "
                    "comparative effectiveness."
                )
            })

        # ----------------------------------------------------
        # QUALITY ASSURANCE
        # ----------------------------------------------------

        qa = {
            "status": "requires_human_validation",
            "protocol_status": protocol.get(
                "status",
                "unknown"
            ),
            "screening_status": "provisional",
            "evidence_records_processed": len(evidence),
            "records_with_structured_evidence": usable_count,
            "records_without_structured_evidence": (
                len(studies) - usable_count
            ),
            "records_requiring_verification": len(issues),
            "uncertain_screening_records": uncertain,
            "issues": issues,
            "limitations": limitations,
            "academic_narrative_source": (
                self._narrative_source
            ),
            "ollama_error": self._ollama_error
        }

        # ----------------------------------------------------
        # SYNTHESIS REPORT
        # ----------------------------------------------------

        synthesis = {
            "research_topic": topic,
            "searched_databases": searched_databases,
            "search_completed_at_utc": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).isoformat(),
            "status": "preliminary",
            "protocol_status": protocol.get(
                "status",
                "unknown"
            ),
            "screening_summary": {
                "total": len(screening),
                "provisionally_included": included,
                "excluded": excluded,
                "uncertain": uncertain
            },
            "evidence_records": len(evidence),
            "records_with_structured_evidence": usable_count,
            "method_mentions_in_abstracts": dict(
                method_counts
            ),
            "study_summaries": studies,
            "thematic_synthesis": themes,
            "research_question_discussion": rq_discussion,
            "research_gaps": ([self._batch_extra_sections["open_challenges"]] if self._batch_extra_sections else gaps),
            "synthesis_coverage": self._batch_synthesis_audit,
            "academic_sections": academic,
            "conclusion": academic["conclusion"],
            "note": (
                "Preliminary automated abstract-based "
                "evidence map. Not a verified final "
                "systematic review."
            )
        }

        # ----------------------------------------------------
        # SAVE REPORTS
        # ----------------------------------------------------

        paths = {
            "synthesis": self.save(
                "synthesis_report.json",
                synthesis
            ),
            "quality_assurance": self.save(
                "quality_assurance.json",
                qa
            ),
            "prisma": self.save(
                "prisma_preliminary.json",
                prisma
            )
        }

        # ----------------------------------------------------
        # TERMINAL SUMMARY
        # ----------------------------------------------------

        print(
            "\n[Reporting] Provisional records:",
            len(studies)
        )

        print(
            "[Reporting] Structured evidence:",
            usable_count
        )

        print(
            "[Reporting] Missing structured evidence:",
            len(studies) - usable_count
        )

        print(
            "[Reporting] Research questions:",
            len(rq_discussion)
        )

        print(
            "[Reporting] Academic narrative source:",
            self._narrative_source
        )

        # ----------------------------------------------------
        # RETURN WORKFLOW STATE
        # ----------------------------------------------------

        return {
            "synthesis_report": synthesis,
            "qa_report": qa,
            "prisma_report": prisma,
            "report_paths": paths
        }
