
from langchain_ollama import ChatOllama
from rag.retriever import ResearchRetriever


class RAGAnswerGenerator:


    def __init__(
        self,
        documents=None,
        collection_name="scientific_papers"
    ):
        self.retriever = ResearchRetriever(
            documents=documents,
            collection_name=collection_name
        )

        self.llm = ChatOllama(
            model="qwen3:4b",
            temperature=0,
            reasoning=False
        )


    def generate_answer(self, research_question, k=3):

        evidence = self.retriever.retrieve_evidence(
            research_question=research_question,
            k=k
        )

        if not evidence:
            return {
                "question": research_question,
                "answer": "No relevant evidence was retrieved.",
                "sources": []
            }

        context_parts = []

        for index, paper in enumerate(evidence, start=1):
            context_parts.append(
                f"[{index}] Title: {paper['title']}\n"
                f"Year: {paper['year']}\n"
                f"Paper ID: {paper['paper_id']}\n"
                f"Abstract: {paper['abstract']}"
            )

        context = "\n\n".join(context_parts)

        prompt = f"""
You are a scientific research assistant.

Answer the research question using ONLY the
scientific abstracts provided below.

Rules:
- Do not invent findings, methods, or citations.
- Support factual claims with references such as [1], [2].
- If the abstracts do not contain enough information,
  explicitly state that the evidence is insufficient.
- Distinguish what the abstracts report from your own
  interpretation.
- Do not treat an abstract as full-text evidence.

Research question:
{research_question}

Scientific evidence:
{context}

Write a clear, concise, evidence-grounded answer.

/no_think
"""

        response = self.llm.invoke(prompt)

        answer = response.content

        if "</think>" in answer:
            answer = answer.split("</think>")[-1].strip()

        return {
            "question": research_question,
            "answer": answer,
            "sources": evidence
        }
