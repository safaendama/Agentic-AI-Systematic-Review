"""Run Steps 8-10 using saved provisional screening results.

Run from the project root: python run_final_steps.py
This is an abstract-based, provisional M1 demonstration, not a final SLR.
"""
import json
from pathlib import Path
from workflow import evidence_analysis_node, reporting_node, document_generation_node

OUT = Path('data/outputs')
TOPIC = 'Explainable Artificial Intelligence for Credit Risk Assessment'

def load(name, required=True):
    path = OUT / name
    if not path.exists():
        if required:
            raise FileNotFoundError(f'Missing {path}. Run the earlier pipeline first.')
        return None
    with path.open(encoding='utf-8') as f:
        return json.load(f)

def main():
    screening = load('screening_results_provisional.json')
    summary = load('screening_summary_provisional.json')
    protocol = load('review_protocol.json')
    dedup = load('deduplication_result.json')
    retrieved = load('retrieved_papers.json')
    enriched = load('enriched_papers.json')

    if not isinstance(screening, list):
        raise ValueError('Provisional screening must be a list.')
    counts = {k: sum(r.get('decision') == k for r in screening) for k in ('include', 'exclude', 'uncertain')}
    print('Provisional decisions:', counts)
    if counts['include'] == 0:
        raise ValueError('No provisionally included papers to analyze.')
    if len(screening) != 10 or counts != {'include': 6, 'exclude': 2, 'uncertain': 2}:
        raise ValueError('Screening counts differ from expected 10/6/2/2; review inputs before continuing.')

    # Keep the preliminary status explicit in the protocol and state.
    protocol = dict(protocol)
    protocol['status'] = 'draft_amended_for_M1_demonstration'
    protocol['requires_human_review'] = True
    protocol['protocol_amendment'] = summary.get('protocol_amendment',
        'Relevant empirical preprints are supplementary evidence.')
    protocol['limitations'] = summary.get('limitations',
        'Abstract-based provisional screening; full-text verification pending.')

    state = {
        'research_topic': TOPIC,
        'protocol': protocol,
        'retrieved_papers': retrieved,
        'deduplication_result': dedup,
        'enriched_papers': enriched,
        'screening_results': screening,
        'screening_summary': {
            **summary,
            'included': counts['include'],
            'excluded': counts['exclude'],
            'uncertain': counts['uncertain'],
            'status': 'automated_provisional_for_M1_demonstration',
            'final_included': None,
            'final_excluded': None,
            'requires_human_review': True,
        },
        'review_plan': load('review_plan.json', required=False) or {},
        'rag_result': load('rag_result.json', required=False) or {},
    }

    # The imported nodes may overwrite existing preliminary output files.
    # Back up the existing output files before running.
    names = ['evidence_results.json', 'synthesis_report.json', 'quality_assurance.json',
             'prisma_preliminary.json', 'prisma_flow.png', 'systematic_review_preliminary.pdf']
    backup = OUT / 'before_provisional_analysis'
    backup.mkdir(parents=True, exist_ok=True)
    import shutil
    for name in names:
        source = OUT / name
        if source.exists():
            shutil.copy2(source, backup / name)

    print('\nRunning Step 8: Evidence Analysis')
    state.update(evidence_analysis_node(state))
    print('\nRunning Step 9: Reporting')
    state.update(reporting_node(state))
    print('\nRunning Step 10: PRISMA and PDF')
    state.update(document_generation_node(state))
    print('\nDONE. Results are PRELIMINARY, not human-verified.')
    print('Evidence analyses:', len(state['evidence_results']))
    print('PDF:', state.get('pdf_report_path'))
    print('PRISMA:', state.get('prisma_image_path'))
    print('Previous reports backed up in:', backup)

if __name__ == '__main__':
    main()
