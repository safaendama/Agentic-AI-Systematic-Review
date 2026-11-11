
import json
import re
from datetime import date

from langchain_ollama import ChatOllama


class ProtocolAgent:
    """
    Topic-independent systematic review protocol agent.

    Publication years, language and number of
    research questions are configurable.

    The protocol is a draft, not a final
    registered systematic review protocol.
    """

    REQUIRED_LISTS = [
        "research_questions",
        "inclusion_criteria",
        "exclusion_criteria",
        "recommended_databases",
        "search_keywords",
    ]

    def __init__(
        self,
        start_year=2022,
        end_year=None,
        language="English",
        number_of_questions=3,
        empirical_only=True,
        exclude_secondary_reviews=True,
        require_peer_review=True,
    ):
        self.start_year = int(start_year)
        self.end_year = int(
            end_year if end_year is not None
            else date.today().year
        )
        self.language = str(language).strip()
        self.number_of_questions = int(number_of_questions)

        self.empirical_only = bool(empirical_only)
        self.exclude_secondary_reviews = bool(
            exclude_secondary_reviews
        )
        self.require_peer_review = bool(
            require_peer_review
        )

        if self.start_year > self.end_year:
            raise ValueError(
                "start_year cannot exceed end_year."
            )

        if self.start_year > date.today().year:
            raise ValueError(
                "Publication range starts in the future."
            )

        if not self.language:
            raise ValueError(
                "Publication language cannot be empty."
            )

        if self.number_of_questions < 1:
            raise ValueError(
                "number_of_questions must be positive."
            )

        self.llm = ChatOllama(
            model="qwen3:4b",
            temperature=0,
            reasoning=False,
            format="json",
        )

    def _effective_end_year(self):
        return min(
            self.end_year,
            date.today().year,
        )

    def _parse_json(self, content):
        if not isinstance(content, str):
            raise ValueError(
                "LLM response must be text."
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
                    "No JSON object found in response."
                )

            try:
                data = json.loads(
                    content[start:end + 1]
                )
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON response: {error}"
                ) from error

        if not isinstance(data, dict):
            raise ValueError(
                "Protocol must be a JSON object."
            )

        return data

    def _normalize_list(self, values):
        if not isinstance(values, list):
            return values

        normalized = []

        for value in values:
            if not isinstance(value, str):
                normalized.append(value)
                continue

            clean = " ".join(value.split())

            if clean and clean not in normalized:
                normalized.append(clean)

        return normalized

    def _mandatory_inclusion(self):
        """
        Generate consistent administrative criteria
        from configuration, not research-topic keywords.
        """
        end_year = self._effective_end_year()

        criteria = [
            (
                f"Studies published from "
                f"{self.start_year} to {end_year}"
            ),
            (
                f"Studies published in "
                f"{self.language}"
            ),
        ]

        if self.require_peer_review:
            criteria.append(
                "Peer-reviewed publications with "
                "independently verifiable "
                "publication status"
            )

        if self.empirical_only:
            criteria.append(
                "Original empirical studies "
                "with reported evaluation evidence"
            )

        return criteria

    def _mandatory_exclusion(self):
        criteria = [
            (
                f"Studies published outside "
                f"{self.start_year} to "
                f"{self._effective_end_year()}"
            ),
            (
                f"Studies published in languages "
                f"other than {self.language}"
            ),
        ]

        if self.require_peer_review:
            criteria.append(
                "Publications verified as not "
                "peer reviewed"
            )

        if self.empirical_only:
            criteria.append(
                "Non-empirical studies without "
                "original evaluation evidence"
            )

        if self.exclude_secondary_reviews:
            criteria.append(
                "Secondary reviews, systematic "
                "reviews, literature reviews, "
                "scoping reviews and meta-analyses"
            )

        return criteria

    def _validate_protocol(
        self,
        data,
        research_topic,
    ):
        errors = []

        objective = data.get(
            "research_objective"
        )

        if (
            not isinstance(objective, str)
            or not objective.strip()
        ):
            errors.append(
                "Missing research_objective."
            )

        for key in self.REQUIRED_LISTS:
            values = data.get(key)

            if (
                not isinstance(values, list)
                or not values
                or not all(
                    isinstance(item, str)
                    and item.strip()
                    for item in values
                )
            ):
                errors.append(
                    f"{key} must be a non-empty "
                    "list of strings."
                )

        questions = data.get(
            "research_questions",
            [],
        )

        if (
            isinstance(questions, list)
            and len(questions)
            != self.number_of_questions
        ):
            errors.append(
                "research_questions must contain "
                f"{self.number_of_questions} questions."
            )

        topic_words = {
            word
            for word in re.findall(
                r"[a-zA-Z]{4,}",
                research_topic.lower(),
            )
            if word not in {
                "research",
                "study",
                "studies",
                "review",
                "systematic",
                "using",
                "with",
                "from",
                "methods",
            }
        }

        if topic_words:
            content = " ".join([
                str(objective or ""),
                " ".join(
                    questions
                    if isinstance(questions, list)
                    else []
                ),
            ]).lower()

            if not any(
                word in content
                for word in topic_words
            ):
                errors.append(
                    "Objective and questions "
                    "do not clearly address "
                    "the research topic."
                )

        return errors

    def _build_prompt(self, research_topic):
        return f"""
You are a systematic review methodologist.

RESEARCH TOPIC:
{research_topic}

Create a topic-specific, preliminary
systematic literature review protocol.

SETTINGS:
Publication range:
{self.start_year} to {self._effective_end_year()}

Publication language:
{self.language}

Number of research questions:
{self.number_of_questions}

Original empirical studies only:
{self.empirical_only}

Exclude secondary reviews:
{self.exclude_secondary_reviews}

Require verified peer-reviewed publication:
{self.require_peer_review}

INSTRUCTIONS:

1. Write a research objective specific
   to the user's research topic.

2. Generate exactly
   {self.number_of_questions}
   research questions.

3. Generate scientific-content inclusion
   and exclusion criteria appropriate
   for this particular research topic.

4. Do not contradict the fixed settings.

5. Include research-specific terminology
   and reasonable alternative keywords.

6. Recommend suitable scholarly databases.
   Recommendations do not imply that
   those databases have been searched.

7. Provide useful search expressions.
   These are proposed strategies, not
   claims about executed searches.

8. Do not invent studies, citations,
   datasets, results, or statistics.

9. Do not assume preprints are peer reviewed.

10. Avoid generic questions that could
    apply unchanged to every research field.

Return ONLY one JSON object:

{{
  "research_objective": "...",
  "research_questions": [
    "..."
  ],
  "inclusion_criteria": [
    "..."
  ],
  "exclusion_criteria": [
    "..."
  ],
  "recommended_databases": [
    "..."
  ],
  "search_keywords": [
    "..."
  ]
}}

/no_think
"""

    def _build_repair_prompt(
        self,
        research_topic,
        previous_response,
        errors,
    ):
        error_text = "\n".join(
            f"- {error}"
            for error in errors
        )

        return f"""
Correct the following systematic
review protocol.

RESEARCH TOPIC:
{research_topic}

PREVIOUS RESPONSE:
{previous_response}

VALIDATION ERRORS:
{error_text}

REQUIREMENTS:
- Return the complete JSON object.
- Exactly {self.number_of_questions}
  research questions.
- Keep the topic-specific scientific criteria.
- Do not invent scientific evidence.
- Return valid JSON only.

/no_think
"""

    def _finalize_protocol(self, data):
        """
        Make mandatory criteria deterministic.

        This prevents the language model from
        accidentally omitting eligibility rules.
        """

        inclusion = self._mandatory_inclusion()
        exclusion = self._mandatory_exclusion()

        for item in data["inclusion_criteria"]:
            if item not in inclusion:
                inclusion.append(item)

        for item in data["exclusion_criteria"]:
            if item not in exclusion:
                exclusion.append(item)

        # Remove conflicting LLM-generated
        # administrative criteria. Mandatory
        # settings above are authoritative.
        #
        # Preserve topic-specific scientific
        # criteria whenever possible.

        def is_administrative(item):
            text = item.lower()

            return bool(
                re.search(
                    r"\b(?:19|20)\d{2}\b|"
                    r"\benglish\b|"
                    r"peer[\s-]?review",
                    text,
                )
            )

        mandatory_inclusion = (
            self._mandatory_inclusion()
        )
        mandatory_exclusion = (
            self._mandatory_exclusion()
        )

        inclusion = mandatory_inclusion + [
            item
            for item in inclusion
            if (
                item not in mandatory_inclusion
                and not is_administrative(item)
            )
        ]

        exclusion = mandatory_exclusion + [
            item
            for item in exclusion
            if (
                item not in mandatory_exclusion
                and not is_administrative(item)
            )
        ]

        data["inclusion_criteria"] = list(
            dict.fromkeys(inclusion)
        )

        data["exclusion_criteria"] = list(
            dict.fromkeys(exclusion)
        )

        return data

    def _format_protocol(
        self,
        data,
        research_topic,
    ):
        sections = [
            "# Preliminary Systematic Review Protocol",
            "",
            f"Research topic: {research_topic}",
            "",
            (
                "Publication range: "
                f"{self.start_year}–"
                f"{self._effective_end_year()}"
            ),
            (
                "Publication language: "
                f"{self.language}"
            ),
            "",
            "## 1. Research Objective",
            data["research_objective"],
            "",
            "## 2. Research Questions",
        ]

        for index, question in enumerate(
            data["research_questions"],
            start=1,
        ):
            sections.append(
                f"{index}. {question}"
            )

        definitions = [
            (
                "## 3. Inclusion Criteria",
                "inclusion_criteria",
            ),
            (
                "## 4. Exclusion Criteria",
                "exclusion_criteria",
            ),
            (
                "## 5. Recommended Databases",
                "recommended_databases",
            ),
            (
                "## 6. Search Keywords",
                "search_keywords",
            ),
        ]

        for heading, key in definitions:
            sections.extend([
                "",
                heading,
            ])

            for item in data[key]:
                sections.append(
                    f"- {item}"
                )

        sections.extend([
            "",
            "Note: This protocol is preliminary.",
            (
                "Eligibility criteria require "
                "human approval before final "
                "study inclusion."
            ),
        ])

        return "\n".join(sections)

    def generate_protocol(self, research_topic):
        if not isinstance(
            research_topic,
            str,
        ):
            raise ValueError(
                "Research topic must be text."
            )

        research_topic = research_topic.strip()

        if not research_topic:
            raise ValueError(
                "Research topic cannot be empty."
            )

        print(
            "\nGenerating systematic review protocol..."
        )

        print(
            "Publication range:",
            f"{self.start_year}–"
            f"{self._effective_end_year()}",
        )

        prompt = self._build_prompt(
            research_topic
        )

        max_attempts = 3
        last_errors = []

        for attempt in range(
            1,
            max_attempts + 1,
        ):
            print(
                "Protocol generation attempt "
                f"{attempt}/{max_attempts}"
            )

            response = self.llm.invoke(
                prompt
            )

            raw_content = str(
                response.content
            )

            try:
                data = self._parse_json(
                    raw_content
                )

                for key in self.REQUIRED_LISTS:
                    if key in data:
                        data[key] = (
                            self._normalize_list(
                                data[key]
                            )
                        )

                errors = self._validate_protocol(
                    data,
                    research_topic,
                )

            except (
                ValueError,
                TypeError,
            ) as error:
                data = None
                errors = [str(error)]

            if not errors:
                data = self._finalize_protocol(
                    data
                )

                print(
                    "Protocol generated and "
                    "validated successfully!"
                )

                return {
                    "research_topic": research_topic,
                    "publication_start_year": (
                        self.start_year
                    ),
                    "publication_end_year": (
                        self._effective_end_year()
                    ),
                    "publication_language": (
                        self.language
                    ),
                    "protocol_content": (
                        self._format_protocol(
                            data,
                            research_topic,
                        )
                    ),
                    "research_objective": (
                        data["research_objective"]
                    ),
                    "research_questions": (
                        data["research_questions"]
                    ),
                    "inclusion_criteria": (
                        data["inclusion_criteria"]
                    ),
                    "exclusion_criteria": (
                        data["exclusion_criteria"]
                    ),
                    "recommended_databases": (
                        data["recommended_databases"]
                    ),
                    "search_keywords": (
                        data["search_keywords"]
                    ),
                    "status": "draft",
                    "requires_human_review": True,
                    "generated_on": (
                        date.today().isoformat()
                    ),
                }

            last_errors = errors

            print(
                "Validation failed:"
            )

            for error in errors:
                print(
                    "  -",
                    error
                )

            if attempt < max_attempts:
                prompt = (
                    self._build_repair_prompt(
                        research_topic,
                        raw_content,
                        errors,
                    )
                )

        raise ValueError(
            "Protocol generation failed after "
            f"{max_attempts} attempts.\n"
            + "\n".join(last_errors)
        )
