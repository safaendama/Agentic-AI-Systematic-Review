
import json
import uuid

from pathlib import Path
from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from agents.coordinator import CoordinatorAgent
from agents.protocol import ProtocolAgent
from agents.multi_source_search import MultiSourceSearchAgent
from agents.deduplication import DeduplicationAgent
from agents.retrieval import RetrievalAgent
from agents.publication_verification import PublicationVerificationAgent
from agents.screening import ScreeningAgent
from agents.evidence_analysis import EvidenceAnalysisAgent
from agents.review_reporting import ReviewReportingAgent
from agents.prisma_visualization import PRISMAVisualizationAgent
from agents.pdf_report import PDFReportAgent

from rag.document_loader import DocumentLoaderAgent
from rag.answer_generator import RAGAnswerGenerator


# ==========================================
# OUTPUT DIRECTORY
# ==========================================

OUTPUT_DIR = Path("data/outputs")


# ==========================================
# LANGGRAPH STATE
# ==========================================

class ReviewState(TypedDict, total=False):

    research_topic: str
    review_plan: dict
    protocol: dict
    retrieved_papers: list
    deduplication_result: dict
    enriched_papers: list
    rag_result: dict
    screening_results: list
    screening_summary: dict
    evidence_results: list
    synthesis_report: dict
    qa_report: dict
    prisma_report: dict
    report_paths: dict
    prisma_image_path: str
    pdf_report_path: str


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def save_json(filename, data):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path = OUTPUT_DIR / filename

    with output_path.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False,
            default=str
        )

    return str(output_path)


# ==========================================
# 1. COORDINATOR AGENT
# ==========================================

def coordinator_node(state: ReviewState):

    print("\n[1/10] Starting Coordinator Agent...")

    agent = CoordinatorAgent(
        state["research_topic"]
    )

    plan = agent.create_plan()

    return {
        "review_plan": plan
    }


# ==========================================
# 2. PROTOCOL AGENT
# ==========================================

def protocol_node(state: ReviewState):

    print("\n[2/10] Starting Protocol Agent...")

    agent = ProtocolAgent(
        start_year=2022,
        end_year=2026
    )

    protocol = agent.generate_protocol(
        state["research_topic"]
    )

    required_fields = [
        "research_objective",
        "research_questions",
        "inclusion_criteria",
        "exclusion_criteria",
        "recommended_databases",
        "search_keywords",
        "publication_start_year",
        "publication_end_year"
    ]

    for field in required_fields:

        if not protocol.get(field):

            raise ValueError(
                f"Protocol missing required field: {field}"
            )

    start_year = int(
        protocol["publication_start_year"]
    )

    end_year = int(
        protocol["publication_end_year"]
    )

    if start_year > end_year:

        raise ValueError(
            "Invalid protocol publication range."
        )

    print(
        f"Protocol publication range: "
        f"{start_year}–{end_year}"
    )

    # Protocol remains a draft until human approval.

    protocol["status"] = "draft"
    protocol["requires_human_review"] = True

    save_json(
        "review_protocol.json",
        protocol
    )

    print(
        "Protocol generated and saved successfully!"
    )

    return {
        "protocol": protocol
    }


# ==========================================
# 3. MULTI-SOURCE SEARCH AGENT
# ==========================================

def search_node(state: ReviewState):

    print("\n[3/10] Starting Multi-Source Search...")

    protocol = state["protocol"]

    start_year = int(
        protocol["publication_start_year"]
    )

    end_year = int(
        protocol["publication_end_year"]
    )

    print(
        f"Protocol publication range: "
        f"{start_year}–{end_year}"
    )

    agent = MultiSourceSearchAgent(
        start_year=start_year,
        end_year=end_year
    )

    papers = agent.search_papers(
        research_topic=state["research_topic"],
        max_results=70
    )

    if not isinstance(papers, list):

        raise ValueError(
            "Search Agent must return a list of papers."
        )

    save_json(
        "retrieved_papers.json",
        papers
    )

    print(
        f"Retrieved records: {len(papers)}"
    )

    return {
        "retrieved_papers": papers
    }


# ==========================================
# 4. DEDUPLICATION AGENT
# ==========================================

def deduplication_node(state: ReviewState):

    print("\n[4/10] Starting Deduplication Agent...")

    agent = DeduplicationAgent()

    result = agent.remove_duplicates(
        state["retrieved_papers"]
    )

    if not isinstance(result, dict):

        raise ValueError(
            "Deduplication Agent must return a dictionary."
        )

    unique_papers = result.get(
        "unique_papers"
    )

    if not isinstance(unique_papers, list):

        raise ValueError(
            "Deduplication result must contain "
            "a list of unique_papers."
        )

    save_json(
        "deduplication_result.json",
        result
    )

    print(
        "Unique records after deduplication:",
        len(unique_papers)
    )

    return {
        "deduplication_result": result
    }


# ==========================================
# 5. RETRIEVAL AGENT
# ==========================================

def retrieval_node(state: ReviewState):

    print("\n[5/10] Starting Retrieval and Publication Verification...")

    retrieval_agent = RetrievalAgent()
    verification_agent = PublicationVerificationAgent()

    enriched_papers = []

    unique_papers = state[
        "deduplication_result"
    ]["unique_papers"]

    for index, paper in enumerate(unique_papers, start=1):

        print(
            f"Retrieving and verifying metadata for paper "
            f"{index}/{len(unique_papers)}"
        )

        enriched = paper.copy()

        if paper.get("source") == "OpenAlex":

            openalex_id = paper.get("openalex_id")

            if openalex_id:
                try:
                    details = retrieval_agent.retrieve_paper(openalex_id)

                    if isinstance(details, dict):
                        # Do not replace existing values with missing metadata.
                        # Do not erase independently verified decisions.
                        protected = {
                            "peer_reviewed",
                            "peer_review_verified",
                            "language_verified",
                            "verification_evidence",
                        }

                        for key, value in details.items():
                            if value is None:
                                continue
                            if key in protected and key in enriched:
                                continue
                            enriched[key] = value

                except Exception as error:
                    print(
                        "OpenAlex retrieval failed for "
                        f"{paper.get('title', 'Unknown')}: {error}"
                    )

        # Crossref enrichment works for OpenAlex and arXiv records
        # with a DOI. Missing metadata and unverified statuses stay pending.
        try:
            enriched = verification_agent.verify_paper(enriched)
        except Exception as error:
            print(
                "Publication verification failed for "
                f"{paper.get('title', 'Unknown')}: {error}"
            )
            enriched["verification_status"] = "pending"
            enriched["verification_error"] = str(error)

        enriched_papers.append(enriched)

    save_json("enriched_papers.json", enriched_papers)
    save_json("publication_verification.json", enriched_papers)

    pending = sum(
        paper.get("verification_status") != "verified"
        for paper in enriched_papers
    )

    print("Metadata enrichment completed:", len(enriched_papers))
    print("Publication verification pending:", pending)

    return {
        "enriched_papers": enriched_papers
    }


# ==========================================
# 6. EXPLORATORY RAG AGENT
# ==========================================

def rag_node(state: ReviewState):

    print("\n[6/10] Starting Exploratory RAG...")

    loader = DocumentLoaderAgent()

    documents = loader.convert_papers_to_documents(
        state["enriched_papers"]
    )

    if not documents:

        print(
            "No documents available for RAG analysis."
        )

        return {
            "rag_result": {
                "question": state["research_topic"],
                "answer": (
                    "No abstracts available "
                    "for RAG analysis."
                ),
                "sources": [],
                "status": "insufficient_data"
            }
        }

    collection_name = (
        f"review_{uuid.uuid4().hex}"
    )

    generator = RAGAnswerGenerator(
        documents=documents,
        collection_name=collection_name
    )

    research_question = (
        "What are the main methods, findings, "
        "and research challenges related to "
        f"{state['research_topic']}?"
    )

    result = generator.generate_answer(
        research_question=research_question,
        k=min(5, len(documents))
    )

    print(
        "Exploratory RAG analysis completed!"
    )

    return {
        "rag_result": result
    }


# ==========================================
# 7. SCREENING AGENT
# ==========================================

def screening_node(state: ReviewState):

    print("\n[7/10] Starting Provisional Screening...")

    agent = ScreeningAgent()

    protocol = state["protocol"]
    papers = state["enriched_papers"]

    results = []

    for index, paper in enumerate(
        papers,
        start=1
    ):

        print(
            f"Screening paper "
            f"{index}/{len(papers)}"
        )

        decision = agent.screen_paper(
            paper=paper,
            research_topic=state["research_topic"],
            inclusion_criteria=protocol[
                "inclusion_criteria"
            ],
            exclusion_criteria=protocol[
                "exclusion_criteria"
            ]
        )

        if decision["decision"] not in {
            "include",
            "exclude",
            "uncertain"
        }:

            raise ValueError(
                "Screening Agent returned "
                "an invalid decision."
            )

        results.append({
            "paper": paper,
            "decision": decision["decision"],
            "reason": decision["reason"],
            "screening_status": "provisional",
            "requires_human_review": True
        })

    summary = {
        "total": len(results),
        "included": sum(
            item["decision"] == "include"
            for item in results
        ),
        "excluded": sum(
            item["decision"] == "exclude"
            for item in results
        ),
        "uncertain": sum(
            item["decision"] == "uncertain"
            for item in results
        ),
        "status": "provisional",
        "final_included": None,
        "final_excluded": None,
        "requires_human_review": True
    }

    save_json(
        "screening_results.json",
        results
    )

    save_json(
        "screening_summary.json",
        summary
    )

    print("\nPROVISIONAL SCREENING SUMMARY")
    print(summary)

    return {
        "screening_results": results,
        "screening_summary": summary
    }


# ==========================================
# 8. EVIDENCE ANALYSIS AGENT
# ==========================================

def evidence_analysis_node(state: ReviewState):

    print("\n[8/10] Starting Evidence Analysis...")

    agent = EvidenceAnalysisAgent()

    results = []

    included_papers = [
        item["paper"]
        for item in state["screening_results"]
        if item["decision"] == "include"
    ]

    for index, paper in enumerate(
        included_papers,
        start=1
    ):

        print(
            f"Analyzing paper "
            f"{index}/{len(included_papers)}"
        )

        analysis = agent.analyze_paper(
            paper=paper,
            research_topic=state["research_topic"]
        )

        results.append({
            "paper": paper,
            "analysis": analysis,
            "status": "provisional"
        })

    save_json(
        "evidence_results.json",
        results
    )

    print(
        "Provisional evidence analysis completed:",
        len(results)
    )

    if not results:

        print(
            "No provisionally included papers. "
            "This does not mean no eligible "
            "studies exist."
        )

    return {
        "evidence_results": results
    }


# ==========================================
# 9. REVIEW REPORTING AGENT
# ==========================================

def reporting_node(state: ReviewState):

    print("\n[9/10] Starting Review Reporting...")

    agent = ReviewReportingAgent(
        output_dir=str(OUTPUT_DIR)
    )

    result = agent.run(state)

    print(
        "Preliminary synthesis, QA and "
        "PRISMA reports generated!"
    )

    for name, path in result.get(
        "report_paths", {}
    ).items():

        print(
            f"  {name}: {path}"
        )

    return result


# ==========================================
# 10. DOCUMENT GENERATION AGENT
# ==========================================

def document_generation_node(state: ReviewState):

    print(
        "\n[10/10] Generating PRISMA "
        "Diagram and PDF Report..."
    )

    # Always use the current workflow state.

    protocol = state["protocol"]
    synthesis = state["synthesis_report"]
    qa = state["qa_report"]
    prisma = state["prisma_report"]

    visualization_agent = PRISMAVisualizationAgent(
        output_dir=str(OUTPUT_DIR)
    )

    prisma_image_path = visualization_agent.generate(
        prisma_data=prisma,
        filename="prisma_flow.png"
    )

    pdf_agent = PDFReportAgent(
        output_dir=str(OUTPUT_DIR)
    )

    pdf_report_path = pdf_agent.generate(
        protocol=protocol,
        synthesis=synthesis,
        qa=qa,
        prisma=prisma,
        prisma_image=prisma_image_path,
        filename="systematic_review_preliminary.pdf"
    )

    report_paths = {
        **state.get("report_paths", {}),
        "prisma_image": prisma_image_path,
        "pdf": pdf_report_path
    }

    print("\nDOCUMENT GENERATION COMPLETED!")

    print(
        "PRISMA diagram:",
        prisma_image_path
    )

    print(
        "PDF report:",
        pdf_report_path
    )

    return {
        "prisma_image_path": prisma_image_path,
        "pdf_report_path": pdf_report_path,
        "report_paths": report_paths
    }


# ==========================================
# BUILD LANGGRAPH WORKFLOW
# ==========================================

builder = StateGraph(ReviewState)

# Register all 10 nodes.

builder.add_node(
    "coordinator",
    coordinator_node
)

builder.add_node(
    "protocol",
    protocol_node
)

builder.add_node(
    "search",
    search_node
)

builder.add_node(
    "deduplication",
    deduplication_node
)

builder.add_node(
    "retrieval",
    retrieval_node
)

builder.add_node(
    "rag",
    rag_node
)

builder.add_node(
    "screening",
    screening_node
)

builder.add_node(
    "evidence_analysis",
    evidence_analysis_node
)

builder.add_node(
    "reporting",
    reporting_node
)

builder.add_node(
    "document_generation",
    document_generation_node
)


# ==========================================
# CONNECT WORKFLOW NODES
# ==========================================

builder.add_edge(
    START,
    "coordinator"
)

builder.add_edge(
    "coordinator",
    "protocol"
)

builder.add_edge(
    "protocol",
    "search"
)

builder.add_edge(
    "search",
    "deduplication"
)

builder.add_edge(
    "deduplication",
    "retrieval"
)

builder.add_edge(
    "retrieval",
    "rag"
)

builder.add_edge(
    "rag",
    "screening"
)

builder.add_edge(
    "screening",
    "evidence_analysis"
)

builder.add_edge(
    "evidence_analysis",
    "reporting"
)

builder.add_edge(
    "reporting",
    "document_generation"
)

builder.add_edge(
    "document_generation",
    END
)


# ==========================================
# COMPILE WORKFLOW
# ==========================================

review_workflow = builder.compile()
