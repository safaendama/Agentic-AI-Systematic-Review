
import json
import requests
from urllib.parse import unquote


def normalize_doi(doi):
    if not doi:
        return None

    doi = unquote(str(doi).strip())

    for prefix in (
        "https://doi.org/",
        "http://doi.org/",
        "doi:"
    ):
        if doi.lower().startswith(prefix):
            doi = doi[len(prefix):]

    return doi.strip()


def get_crossref_metadata(doi):
    doi = normalize_doi(doi)

    if not doi:
        return None

    response = requests.get(
        "https://api.crossref.org/works/" + doi,
        timeout=30,
        headers={
            "User-Agent": (
                "AgenticSystematicReview/1.0 "
                "(academic research metadata test)"
            )
        }
    )

    if response.status_code == 404:
        return None

    response.raise_for_status()

    data = response.json()["message"]

    return {
        "doi": data.get("DOI"),
        "title": (data.get("title") or [None])[0],
        "publisher": data.get("publisher"),
        "publication_type": data.get("type"),
        "venue_name": (
            data.get("container-title") or [None]
        )[0],
        "issn": data.get("ISSN", []),
        "publication_date": data.get("published"),
        "url": data.get("URL"),
    }


def main():
    with open(
        "data/outputs/enriched_papers_verified.json",
        "r",
        encoding="utf-8"
    ) as file:
        papers = json.load(file)

    results = []

    for index, paper in enumerate(papers, 1):
        print(f"\nPAPER {index}: {paper.get('title')}")

        doi = paper.get("doi")

        if not doi:
            print("No DOI available.")
            continue

        try:
            metadata = get_crossref_metadata(doi)

            if metadata:
                print("Publisher:", metadata["publisher"])
                print("Venue:", metadata["venue_name"])
                print("Type:", metadata["publication_type"])

                results.append({
                    "paper_title": paper.get("title"),
                    "crossref": metadata
                })

            else:
                print("No Crossref record found.")

        except requests.RequestException as error:
            print("Crossref request failed:", error)

    with open(
        "data/outputs/crossref_metadata.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            results,
            file,
            indent=2,
            ensure_ascii=False
        )

    print("\nCROSSREF METADATA TEST COMPLETED")
    print("Records retrieved:", len(results))


if __name__ == "__main__":
    main()
