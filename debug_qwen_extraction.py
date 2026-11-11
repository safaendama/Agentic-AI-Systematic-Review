
import json
from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="qwen3:4b",
    temperature=0,
    reasoning=False,
    format="json"
)

abstract = """
This study compares Random Forest and Decision Tree
models for credit risk prediction using a dataset of
10000 loan applications.

Random Forest achieved 93% accuracy, whereas
Decision Tree achieved 89% accuracy.

SHAP was used to explain predictions.

The authors identified limited external validation
as a limitation.
"""

prompt = f"""
Extract scientific information from the abstract.

ABSTRACT:
{abstract}

Return ONLY a JSON object with EXACTLY these keys:

{{
  "research_objective": "",
  "dataset": "",
  "method_names": [],
  "evaluation_metrics": "",
  "main_findings": "",
  "quantitative_results": [],
  "reported_comparisons": [],
  "limitations": ""
}}

Rules:
- Use only the abstract.
- Do not invent information.
- Use "not reported" only when information is absent.
- method_names must be a list of strings.
- quantitative_results must be a list of strings.
- reported_comparisons must be a list of strings.

/no_think
"""

response = llm.invoke(prompt)

print("\n========== RAW QWEN RESPONSE ==========\n")
print(repr(response.content))

print("\n========== PARSED JSON ==========\n")

try:
    parsed = json.loads(response.content)
    print(json.dumps(
        parsed,
        indent=2,
        ensure_ascii=False
    ))
except Exception as error:
    print("JSON parsing error:", error)

print("\n========== RESPONSE METADATA ==========\n")
print(response.response_metadata)
