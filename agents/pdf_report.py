
"""
STEP 10 — PDF REPORT AGENT

Generate a preliminary systematic literature review PDF.

Compatible with Step 9 — ReviewReportingAgent.

IMPORTANT:
The report is based on preliminary automated evidence.
It is not a completed, independently verified SLR.
"""

import json
import re
from pathlib import Path
from collections import Counter
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    LongTable,
    TableStyle,
    HRFlowable,
)


class PDFReportAgent:

    def __init__(self, output_dir="data/outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.styles = getSampleStyleSheet()

        self.styles.add(ParagraphStyle(
            name="SLRTitle",
            parent=self.styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=23,
            alignment=TA_CENTER,
            spaceAfter=18,
        ))

        self.styles.add(ParagraphStyle(
            name="SLRHeading",
            parent=self.styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=18,
            spaceBefore=18,
            spaceAfter=9,
            keepWithNext=True,
        ))

        self.styles.add(ParagraphStyle(
            name="SLRSubheading",
            parent=self.styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=15,
            spaceBefore=12,
            spaceAfter=7,
            keepWithNext=True,
        ))

        self.styles.add(ParagraphStyle(
            name="SLRBody",
            parent=self.styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=15,
            alignment=TA_JUSTIFY,
            spaceAfter=10,
        ))

        self.styles.add(ParagraphStyle(
            name="SLRSmall",
            parent=self.styles["BodyText"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=11,
            spaceAfter=3,
        ))

    # ==========================================
    # TEXT HELPERS
    # ==========================================

    @staticmethod
    def _string(value, default="Not reported"):
        if value is None or value == "":
            return default

        if isinstance(value, (list, dict)):
            return json.dumps(
                value,
                ensure_ascii=False,
                default=str,
            )

        return str(value)

    def _paragraph(self, value, style="SLRBody"):
        text = self._string(value)

        safe = escape(self._clean_display(text)).replace(
            "\n", "<br/>"
        )

        return Paragraph(
            safe,
            self.styles[style],
        )

    def _heading(self, text):
        return self._paragraph(
            text, "SLRHeading"
        )

    def _subheading(self, text):
        return self._paragraph(
            text, "SLRSubheading"
        )

    def _paragraphs(self, story, values):
        if isinstance(values, (str, dict)):
            values = [values]

        for value in values or []:
            if self._string(value).strip():
                story.append(
                    self._paragraph(value)
                )

    def _items(self, story, values):
        if isinstance(values, (str, dict)):
            values = [values]

        for value in values or []:
            story.append(
                self._paragraph(
                    "- " + self._string(value)
                )
            )

    # ==========================================
    # TABLES
    # ==========================================

    def _table(self, headers, rows, widths):
        data = [
            [
                self._paragraph(
                    h, "SLRSmall"
                )
                for h in headers
            ]
        ]

        for row in rows:
            data.append([
                self._paragraph(
                    value, "SLRSmall"
                )
                for value in row
            ])

        table = LongTable(
            data,
            colWidths=widths,
            repeatRows=1,
            hAlign="LEFT",
        )

        table.setStyle(TableStyle([
            (
                "BACKGROUND",
                (0, 0), (-1, 0),
                colors.HexColor("#E8EEF5"),
            ),
            (
                "LINEBELOW",
                (0, 0), (-1, 0),
                0.7,
                colors.HexColor("#72869A"),
            ),
            (
                "LINEBELOW",
                (0, 1), (-1, -1),
                0.25,
                colors.HexColor("#D5DDE5"),
            ),
            (
                "VALIGN",
                (0, 0), (-1, -1),
                "TOP",
            ),
            (
                "LEFTPADDING",
                (0, 0), (-1, -1), 5,
            ),
            (
                "RIGHTPADDING",
                (0, 0), (-1, -1), 5,
            ),
            (
                "TOPPADDING",
                (0, 0), (-1, -1), 6,
            ),
            (
                "BOTTOMPADDING",
                (0, 0), (-1, -1), 6,
            ),
        ]))

        return table

    # ==========================================
    # STUDY HELPERS
    # ==========================================

    # Presentation-only normalization. Unknown methods are retained, so this
    # works across research domains without imposing a fixed vocabulary.
    @staticmethod
    def _clean_display(value):
        text = str(value or "").strip()
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"(?<=\w):(?=\w)", "-", text)
        text = re.sub(r"\bROC-A:UC\b", "ROC-AUC", text, flags=re.I)
        return text

    @classmethod
    def _canonical_method(cls, value):
        text = cls._clean_display(value).strip(" ,;:.-")
        if not text or text.casefold() in {"none", "n/a", "not reported", "unknown", "null"}:
            return None
        if not any(c.isalnum() for c in text):
            return None
        key = re.sub(r"[^a-z0-9]+", " ", text.casefold()).strip()
        aliases = {
            "svm": "Support Vector Machine (SVM)",
            "support vector machine": "Support Vector Machine (SVM)",
            "support vector machines": "Support Vector Machine (SVM)",
            "support vector machine svm": "Support Vector Machine (SVM)",
            "support vector machines svm": "Support Vector Machine (SVM)",
            "knn": "K-Nearest Neighbors (KNN)",
            "k nearest neighbor": "K-Nearest Neighbors (KNN)",
            "k nearest neighbors": "K-Nearest Neighbors (KNN)",
            "k nearest neighbour": "K-Nearest Neighbors (KNN)",
            "k nearest neighbours": "K-Nearest Neighbors (KNN)",
            "k nearest neighbors knn": "K-Nearest Neighbors (KNN)",
            "k nearest neighbor knn": "K-Nearest Neighbors (KNN)",
            "smote": "SMOTE",
            "synthetic minority over sampling technique smote": "SMOTE",
            "synthetic minority oversampling technique smote": "SMOTE",
            "smote oversampling": "SMOTE",
            "random forest": "Random Forest",
            "random forests": "Random Forest",
            "logistic regression": "Logistic Regression",
            "decision tree": "Decision Tree",
            "decision trees": "Decision Tree",
            "xgboost": "XGBoost",
            "xg boost": "XGBoost",
            "extreme gradient boost": "XGBoost",
            "neural network": "Neural Networks",
            "neural networks": "Neural Networks",
            "artificial neural network": "Artificial Neural Networks",
            "artificial neural networks": "Artificial Neural Networks",
            "gnn": "Graph Neural Networks (GNN)",
            "graph neural networks": "Graph Neural Networks (GNN)",
            "graph neural networks gnn": "Graph Neural Networks (GNN)",
            "cnn": "Convolutional Neural Networks (CNN)",
            "convolutional neural network cnn": "Convolutional Neural Networks (CNN)",
            "convolutional neural networks cnn": "Convolutional Neural Networks (CNN)",
            "lstm": "LSTM",
            "long short term memory lstm": "LSTM",
            "lightgbm": "LightGBM",
            "gradient boosting": "Gradient Boosting",
        }
        return aliases.get(key, text)

    @classmethod
    def _methods(cls, study):
        raw = study.get("methods_mentioned_in_abstract") or []
        if isinstance(raw, str):
            raw = [raw]
        if not isinstance(raw, list):
            return []
        unique = {}
        for item in raw:
            if not isinstance(item, str):
                continue
            canonical = cls._canonical_method(item)
            if canonical:
                unique.setdefault(canonical.casefold(), canonical)
        return list(unique.values())

    @staticmethod
    def _publication_trends(studies):
        years = []

        for study in studies:
            try:
                year = int(
                    study.get("year")
                )

                if 1900 <= year <= 2100:
                    years.append(year)

            except (ValueError, TypeError):
                continue

        return sorted(
            Counter(years).items()
        )

    @staticmethod
    def _authors(study):
        authors = study.get("authors")

        if not authors:
            return ""

        if isinstance(authors, str):
            return authors.strip()

        if isinstance(authors, list):
            names = []

            for author in authors:
                if isinstance(author, str):
                    names.append(author)

                elif isinstance(author, dict):
                    name = (
                        author.get("name")
                        or author.get("display_name")
                        or author.get("author_name")
                    )

                    if (
                        not name
                        and isinstance(
                            author.get("author"),
                            dict,
                        )
                    ):
                        name = author[
                            "author"
                        ].get("display_name")

                    if name:
                        names.append(str(name))

            return ", ".join(names)

        return ""

    def _reference(self, index, study):
        authors = self._authors(study)

        title = self._string(
            study.get("title"),
            "Untitled",
        )

        year = self._string(
            study.get("year"),
            "n.d.",
        )

        parts = [f"[{index}]"]

        if authors:
            parts.append(authors + ".")

        parts.append(f"({year}).")
        parts.append(title + ".")

        venue = (
            study.get("journal")
            or study.get("venue")
            or study.get("publication")
            or study.get("venue_name")
        )

        if venue:
            parts.append(
                self._string(venue) + "."
            )

        doi = self._string(
            study.get("doi"), ""
        )

        if doi:
            if doi.startswith(
                ("http://", "https://")
            ):
                parts.append(doi)
            else:
                parts.append(
                    "https://doi.org/" + doi
                )
        else:
            url = (
                study.get("url")
                or study.get("paper_url")
                or study.get("arxiv_url")
            )

            if url:
                parts.append(
                    self._string(url)
                )

        return " ".join(parts)

    # ==========================================
    # NORMALIZE RESEARCH QUESTIONS
    # ==========================================

    @staticmethod
    def _questions(protocol):
        questions = (
            protocol.get("research_questions")
            or []
        )

        if isinstance(questions, str):
            questions = [questions]

        normalized = []

        for question in questions:
            if isinstance(question, dict):
                text = (
                    question.get("question")
                    or question.get("text")
                    or ""
                )
            else:
                text = question

            text = str(text).strip()

            if text:
                normalized.append(text)

        return normalized

    # ==========================================
    # PRISMA COUNTS
    # ==========================================

    def _prisma_section(
        self,
        story,
        prisma,
        prisma_image,
    ):
        story.append(
            self._subheading(
                "5.1. PRISMA Flow Diagram"
            )
        )

        if (
            prisma_image
            and Path(prisma_image).is_file()
        ):
            figure = Image(
                str(prisma_image)
            )

            scale = min(
                490 / figure.imageWidth,
                510 / figure.imageHeight,
                1,
            )

            figure.drawWidth = (
                figure.imageWidth * scale
            )

            figure.drawHeight = (
                figure.imageHeight * scale
            )

            story.append(figure)

            story.append(
                self._paragraph(
                    "Figure 1. Preliminary "
                    "study-selection flow."
                )
            )

        else:
            story.append(
                self._paragraph(
                    "A PRISMA flow diagram "
                    "was not provided. "
                    "Available preliminary "
                    "counts are shown below."
                )
            )

        fields = [
            (
                "Records identified",
                "records_identified",
            ),
            (
                "Duplicates removed",
                "duplicates_removed",
            ),
            (
                "Records after deduplication",
                "records_after_deduplication",
            ),
            (
                "Title/abstract records screened",
                "records_screened_title_abstract",
            ),
            (
                "Provisionally included",
                "records_provisionally_included",
            ),
            (
                "Excluded at title/abstract stage",
                "records_excluded_title_abstract",
            ),
            (
                "Uncertain screening decisions",
                "records_uncertain",
            ),
            (
                "Full texts assessed",
                "reports_assessed_for_full_text_eligibility",
            ),
            (
                "Finally included studies",
                "studies_finally_included",
            ),
        ]

        rows = [
            (
                label,
                self._string(
                    prisma.get(key)
                ),
            )
            for label, key in fields
        ]

        story.append(
            self._table(
                ["Selection stage", "Count"],
                rows,
                [350, 150],
            )
        )

        story.append(
            self._paragraph(
                "These are preliminary "
                "PRISMA-style counts. "
                "Missing full-text values "
                "must not be interpreted "
                "as zero. A complete PRISMA "
                "2020 flow requires verified "
                "selection records."
            )
        )

    # ==========================================
    # PDF GENERATION
    # ==========================================

    def generate(
        self,
        protocol,
        synthesis,
        qa,
        prisma,
        prisma_image=None,
        filename="systematic_review_preliminary.pdf",
    ):

        protocol = (
            protocol
            if isinstance(protocol, dict)
            else {}
        )

        synthesis = (
            synthesis
            if isinstance(synthesis, dict)
            else {}
        )

        qa = (
            qa
            if isinstance(qa, dict)
            else {}
        )

        prisma = (
            prisma
            if isinstance(prisma, dict)
            else {}
        )

        academic = (
            synthesis.get("academic_sections")
            or {}
        )

        topic = (
            protocol.get("research_topic")
            or synthesis.get("research_topic")
            or "Systematic Literature Review"
        )

        studies = (
            synthesis.get("study_summaries")
            or []
        )

        summary = (
            synthesis.get("screening_summary")
            or {}
        )

        questions = self._questions(
            protocol
        )

        method_counts = Counter()

        for study in studies:
            # Count each canonical method at most once per study.
            method_counts.update(set(self._methods(study)))

        output_path = (
            self.output_dir / filename
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            leftMargin=46,
            rightMargin=46,
            topMargin=48,
            bottomMargin=48,
        )

        story = []

        # ======================================
        # TITLE
        # ======================================

        story.append(
            self._paragraph(
                topic,
                "SLRTitle",
            )
        )

        story.append(
            self._paragraph(
                "PRELIMINARY SYSTEMATIC "
                "LITERATURE REVIEW"
            )
        )

        story.append(
            HRFlowable(
                width="100%",
                thickness=0.6,
                color=colors.HexColor(
                    "#A9B7C6"
                ),
            )
        )

        story.append(Spacer(1, 14))

        # ======================================
        # 1. ABSTRACT
        # ======================================

        story.append(
            self._heading("1. Abstract")
        )

        abstract = academic.get(
            "abstract"
        ) or (
            f"This preliminary review "
            f"examines research on {topic}. "
            "It summarizes automatically "
            "retrieved and extracted evidence. "
            "The findings require full-text "
            "and independent verification."
        )

        self._paragraphs(
            story,
            abstract,
        )

        keywords = [
            name
            for name, _ in (
                method_counts.most_common(6)
            )
        ]

        story.append(
            self._paragraph(
                "Keywords: "
                + (
                    ", ".join(keywords)
                    if keywords
                    else topic
                )
            )
        )

        # ======================================
        # 2. INTRODUCTION
        # ======================================

        story.append(
            self._heading(
                "2. Introduction"
            )
        )

        self._paragraphs(
            story,
            academic.get("introduction")
            or (
                f"This review investigates "
                f"{topic} and organizes "
                "the preliminary evidence "
                "around the defined "
                "research questions."
            ),
        )

        # ======================================
        # 3. BACKGROUND
        # ======================================

        story.append(
            self._heading(
                "3. Background and Related Work"
            )
        )

        self._paragraphs(
            story,
            academic.get(
                "background_related_work"
            ) or (
                "The available records "
                "describe research methods, "
                "datasets, evaluation "
                "practices, and findings."
            ),
        )

        # ======================================
        # 4. RESEARCH METHODOLOGY
        # ======================================

        story.append(
            self._heading(
                "4. Research Methodology"
            )
        )

        story.append(
            self._subheading(
                "4.1. Research Objectives"
            )
        )

        self._paragraphs(
            story,
            protocol.get(
                "research_objective"
            ) or (
                "Identify, organize, "
                "and synthesize relevant "
                "scientific evidence."
            ),
        )

        story.append(
            self._subheading(
                "4.2. Research Questions"
            )
        )

        if questions:
            for index, question in enumerate(
                questions, start=1
            ):
                story.append(
                    self._paragraph(
                        f"RQ{index}: {question}"
                    )
                )
        else:
            story.append(
                self._paragraph(
                    "Research questions "
                    "were not available."
                )
            )

        story.append(
            self._subheading(
                "4.3. Review Protocol"
            )
        )

        self._paragraphs(
            story,
            [
                (
                    "The workflow uses "
                    "structured literature "
                    "identification, screening, "
                    "extraction, and synthesis."
                ),
                (
                    "PRISMA 2020 provides "
                    "a reporting framework. "
                    "Full PRISMA compliance "
                    "has not been established."
                ),
            ],
        )

        story.append(
            self._subheading(
                "4.4. Search Strategy "
                "and Keywords"
            )
        )

        keywords = (
            protocol.get("search_keywords")
            or []
        )

        if keywords:
            self._items(
                story,
                keywords,
            )
        else:
            story.append(
                self._paragraph(
                    "Search keywords "
                    "were not available."
                )
            )

        story.append(
            self._paragraph(
                "Executed search queries, "
                "search dates, filters, "
                "and retrieval limits "
                "should be verified "
                "against search logs."
            )
        )

        story.append(
            self._subheading(
                "4.5. Information Sources "
                "and Databases"
            )
        )

        sources = (
            synthesis.get(
                "searched_databases"
            )
            or synthesis.get(
                "actual_databases"
            )
            or protocol.get(
                "searched_databases"
            )
        )

        if sources:
            self._items(story, sources)
            if synthesis.get("search_completed_at_utc"):
                story.append(self._paragraph(
                    "Report generation / search completion recorded (UTC): "
                    + self._string(synthesis["search_completed_at_utc"])
                    + ". Exact API queries and filters must be checked against the search logs."
                ))
        else:
            story.append(
                self._paragraph(
                    "Executed database "
                    "information was not "
                    "available in the report."
                )
            )

        story.append(
            self._subheading(
                "4.6. Study Selection Process"
            )
        )

        story.append(
            self._paragraph(
                "Screened records: "
                + self._string(
                    summary.get("total")
                )
                + ". Provisionally included: "
                + self._string(
                    summary.get(
                        "provisionally_included"
                    )
                )
                + ". Excluded: "
                + self._string(
                    summary.get("excluded")
                )
                + ". Uncertain: "
                + self._string(
                    summary.get("uncertain")
                )
                + "."
            )
        )

        story.append(
            self._subheading(
                "4.7. Data Extraction "
                "and Synthesis"
            )
        )

        self._paragraphs(
            story,
            [
                (
                    "The system extracts "
                    "available methodological "
                    "information, datasets, "
                    "metrics, findings, "
                    "and reported limitations."
                ),
                (
                    "Evidence is organized "
                    "by study and research "
                    "question. Missing results "
                    "are not inferred."
                ),
            ],
        )

        # ======================================
        # 5. RESULTS
        # ======================================

        story.append(
            self._heading("5. Results")
        )

        self._prisma_section(
            story,
            prisma,
            prisma_image,
        )

        # 5.2 STUDIES

        story.append(
            self._subheading(
                "5.2. Overview of Selected Studies"
            )
        )

        if studies:
            rows = []

            for index, study in enumerate(
                studies, start=1
            ):
                methods = ", ".join(
                    self._methods(study)
                )

                rows.append((
                    f"[{index}] "
                    + self._string(
                        study.get("title"),
                        "Untitled",
                    ),
                    study.get("year"),
                    methods or "Not reported",
                ))

            story.append(
                self._table(
                    ["Study", "Year", "Methods"],
                    rows,
                    [255, 45, 200],
                )
            )
        else:
            story.append(
                self._paragraph(
                    "No study records available."
                )
            )

        story.append(
            self._paragraph(
                "The records shown are "
                "provisionally selected. "
                "Final full-text eligibility "
                "has not been verified."
            )
        )

        # 5.3 PUBLICATION TRENDS

        story.append(
            self._subheading(
                "5.3. Publication Trends"
            )
        )

        trends = self._publication_trends(
            studies
        )

        if trends:
            story.append(
                self._table(
                    [
                        "Publication Year",
                        "Number of Records",
                    ],
                    trends,
                    [250, 250],
                )
            )
        else:
            story.append(
                self._paragraph(
                    "Publication years "
                    "were unavailable."
                )
            )

        story.append(
            self._paragraph(
                "These counts describe "
                "only the retrieved sample, "
                "not the entire research field."
            )
        )

        # 5.4 METHOD CLASSIFICATION

        story.append(
            self._subheading(
                "5.4. Classification "
                "and Categorization of Studies"
            )
        )

        if method_counts:
            story.append(
                self._table(
                    [
                        "Method Mentioned",
                        "Number of Records",
                    ],
                    method_counts.most_common(25),
                    [250, 250],
                )
            )
        else:
            story.append(
                self._paragraph(
                    "No structured method "
                    "information was available."
                )
            )

        if len(method_counts) > 25:
            story.append(self._paragraph(
                f"Showing the 25 most frequently mentioned distinct method labels "
                f"out of {len(method_counts)}. Other labels are retained in the underlying evidence."
            ))

        story.append(
            self._paragraph(
                "Method mentions indicate "
                "the presence of methods "
                "in the extracted evidence, "
                "not their effectiveness."
            )
        )

        # 5.5 COMPARATIVE ANALYSIS

        story.append(
            self._subheading(
                "5.5. Comparative Analysis"
            )
        )

        if studies:
            rows = []

            for index, study in enumerate(
                studies, start=1
            ):
                rows.append((
                    f"[{index}] "
                    + self._string(
                        study.get("title"),
                        "Untitled",
                    ),
                    study.get("dataset"),
                    study.get(
                        "evaluation_metrics"
                    ),
                    study.get(
                        "reported_findings"
                    ),
                ))

            story.append(
                self._table(
                    [
                        "Study",
                        "Dataset",
                        "Metrics",
                        "Reported Findings",
                    ],
                    rows,
                    [125, 100, 105, 170],
                )
            )
        else:
            story.append(
                self._paragraph(
                    "Comparative evidence "
                    "was unavailable."
                )
            )

        story.append(
            self._paragraph(
                "Reported findings are "
                "automatically extracted "
                "and require source-level "
                "verification. Differences "
                "in datasets and experimental "
                "conditions may prevent "
                "direct comparison."
            )
        )

        # 5.6 RQ FINDINGS

        story.append(
            self._subheading(
                "5.6. Findings by "
                "Research Question"
            )
        )

        discussions = (
            synthesis.get(
                "research_question_discussion"
            )
            or []
        )

        if discussions:
            for index, discussion in enumerate(
                discussions, start=1
            ):
                if not isinstance(
                    discussion, dict
                ):
                    continue

                question = self._string(
                    discussion.get("question"),
                    "Unspecified question",
                )

                story.append(
                    self._subheading(
                        f"RQ{index}: {question}"
                    )
                )

                observation = (
                    discussion.get(
                        "evidence_based_observation"
                    )
                    or "Insufficient evidence."
                )

                for paragraph in str(
                    observation
                ).split("\n\n"):
                    if paragraph.strip():
                        story.append(
                            self._paragraph(
                                paragraph
                            )
                        )

                supporting = (
                    discussion.get(
                        "supporting_studies"
                    )
                    or []
                )

                story.append(
                    self._paragraph(
                        "Candidate supporting "
                        "studies: "
                        + str(len(supporting))
                        + ". Relevance requires "
                        "human verification."
                    )
                )

        else:
            story.append(
                self._paragraph(
                    "Research-question "
                    "synthesis was unavailable."
                )
            )

        # ======================================
        # 6. DISCUSSION
        # ======================================

        story.append(
            self._heading(
                "6. Discussion"
            )
        )

        discussion_sections = [
            (
                "6.1. Interpretation "
                "of Main Findings",
                "discussion_main_findings",
            ),
            (
                "6.2. Comparison "
                "with Existing Literature",
                "comparison_existing_literature",
            ),
            (
                "6.3. Strengths and "
                "Weaknesses of Approaches",
                "strengths_weaknesses",
            ),
            (
                "6.4. Implications "
                "of the Findings",
                "implications",
            ),
        ]

        for heading, key in discussion_sections:
            story.append(
                self._subheading(heading)
            )

            self._paragraphs(
                story,
                academic.get(key)
                or (
                    "Insufficient verified "
                    "evidence is available "
                    "for a definitive "
                    "interpretation."
                ),
            )

        # ======================================
        # 7. RESEARCH GAPS
        # ======================================

        story.append(
            self._heading(
                "7. Research Gaps "
                "and Future Directions"
            )
        )

        story.append(
            self._subheading(
                "7.1. Identified Research Gaps"
            )
        )

        self._items(
            story,
            synthesis.get("research_gaps")
            or [
                "Research gaps require "
                "further verification."
            ],
        )

        story.append(
            self._subheading(
                "7.2. Open Challenges"
            )
        )

        self._paragraphs(
            story,
            academic.get("open_challenges")
            or (
                "Challenges require "
                "further source-level "
                "assessment."
            ),
        )

        story.append(
            self._subheading(
                "7.3. Recommendations "
                "for Future Research"
            )
        )

        self._paragraphs(
            story,
            academic.get(
                "future_recommendations"
            )
            or (
                "Future research should "
                "prioritize reproducibility "
                "and transparent reporting."
            ),
        )

        # ======================================
        # 8. LIMITATIONS
        # ======================================

        story.append(
            self._heading(
                "8. Limitations "
                "and Threats to Validity"
            )
        )

        limitations = (
            qa.get("limitations")
            or academic.get(
                "limitations_threats_to_validity"
            )
            or []
        )

        self._items(
            story,
            limitations,
        )

        story.append(
            self._paragraph(
                "This preliminary review "
                "does not establish "
                "comprehensive search "
                "coverage, verified "
                "full-text eligibility, "
                "or independently validated "
                "scientific findings."
            )
        )

        # ======================================
        # 9. CONCLUSION
        # ======================================

        story.append(
            self._heading(
                "9. Conclusion"
            )
        )

        conclusion = (
            academic.get("conclusion")
            or synthesis.get("conclusion")
            or (
                "The preliminary findings "
                "require additional "
                "verification."
            )
        )

        self._paragraphs(
            story,
            conclusion,
        )

        # ======================================
        # 10. REFERENCES
        # ======================================

        story.append(
            self._heading(
                "10. References"
            )
        )

        if studies:
            for index, study in enumerate(
                studies, start=1
            ):
                story.append(
                    self._paragraph(
                        self._reference(
                            index,
                            study,
                        )
                    )
                )
        else:
            story.append(
                self._paragraph(
                    "No references available."
                )
            )

        # ======================================
        # PAGE NUMBERS
        # ======================================

        def add_page_number(
            canvas,
            document,
        ):
            canvas.saveState()

            canvas.setFont(
                "Helvetica", 8
            )

            canvas.setFillColor(
                colors.grey
            )

            canvas.drawRightString(
                A4[0] - 46,
                28,
                f"Page {document.page}",
            )

            canvas.restoreState()

        # ======================================
        # BUILD PDF
        # ======================================

        doc.build(
            story,
            onFirstPage=add_page_number,
            onLaterPages=add_page_number,
        )

        print(
            "[PDF] Report generated:",
            output_path,
        )

        return str(output_path)
