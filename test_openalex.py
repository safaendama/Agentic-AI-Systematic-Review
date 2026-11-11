
import requests

# Our test research topic
topic = "Explainable Artificial Intelligence for Credit Risk Assessment"

# OpenAlex API endpoint
url = "https://api.openalex.org/works"

params = {
    "search": topic,
    "per-page": 5
}

print("Searching OpenAlex...\n")

try:
    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()
    papers = data.get("results", [])

    print(f"Papers retrieved: {len(papers)}\n")

    for index, paper in enumerate(papers, start=1):
        print(f"PAPER {index}")
        print(f"Title: {paper.get('title')}")
        print(f"Year: {paper.get('publication_year')}")
        print(f"DOI: {paper.get('doi')}")
        print(f"OpenAlex ID: {paper.get('id')}")
        print("-" * 45)

except requests.exceptions.RequestException as error:
    print(f"API request failed: {error}")
