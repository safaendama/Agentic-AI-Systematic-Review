"""Regenerate the preliminary SLR PDF from saved, validated evidence only.

Run from the project root: python generate_validated_pdf.py
Does not invoke LangGraph, search, screening, or Ollama.
"""
import json
from pathlib import Path

from agents.pdf_report import PDFReportAgent

OUTPUT = Path('data/outputs')


def load_json(name, required=True):
    path = OUTPUT / name
    if not path.is_file():
        if required:
            raise FileNotFoundError(f'Missing {path}. Keep your saved workflow outputs in data/outputs/.')
        print(f'[INFO] Optional file not found: {path}')
        return {}
    with path.open(encoding='utf-8') as f:
        result = json.load(f)
    if not isinstance(result, dict):
        raise ValueError(f'{path} must contain a JSON object.')
    return result


def main():
    synthesis = load_json('synthesis_report_batched_improved_validated.json')
    protocol = load_json('review_protocol.json')
    qa = load_json('quality_assurance.json')
    prisma = load_json('prisma_preliminary.json')

    studies = synthesis.get('study_summaries')
    if not isinstance(studies, list) or not studies:
        raise ValueError('Validated synthesis has no study_summaries; PDF not generated.')
    if not isinstance(synthesis.get('academic_sections'), dict):
        raise ValueError('Validated synthesis has no academic_sections; PDF not generated.')

    protocol_topic = protocol.get('research_topic')
    synthesis_topic = synthesis.get('research_topic')
    if protocol_topic and synthesis_topic and protocol_topic.strip().casefold() != synthesis_topic.strip().casefold():
        raise ValueError('Protocol and synthesis topics differ; refusing to combine unrelated runs.')

    image = OUTPUT / 'prisma_flow.png'
    image_path = str(image) if image.is_file() else None
    if image_path is None:
        print('[INFO] PRISMA image not found; the PDF will display the available counts.')

    filename = 'systematic_review_preliminary_validated.pdf'
    pdf = PDFReportAgent(output_dir=str(OUTPUT))
    generated = pdf.generate(
        protocol=protocol,
        synthesis=synthesis,
        qa=qa,
        prisma=prisma,
        prisma_image=image_path,
        filename=filename,
    )
    print(f'\nSUCCESS: {generated}')
    print(f'Studies included in preliminary overview: {len(studies)}')
    print('IMPORTANT: Preliminary abstract-based review; full-text human verification required.')


if __name__ == '__main__':
    main()
