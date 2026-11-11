
from langchain_ollama import ChatOllama

# Connect to our local Qwen3 model
llm = ChatOllama(
    model="qwen3:4b",
    temperature=0
)

# Research topic
topic = "Explainable Artificial Intelligence for Credit Risk Assessment"

# Send a request to the LLM
prompt = f"""
You are an academic research assistant.

Create three research questions for a systematic
literature review on the following topic:

{topic}

Return exactly three numbered research questions.
Be clear, precise, and academically relevant.
"""

print("Connecting to Qwen3...\n")

response = llm.invoke(prompt)

print("AI-GENERATED RESEARCH QUESTIONS")
print("=" * 45)
print(response.content)
