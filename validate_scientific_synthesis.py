"""Conservative, topic-independent abstract-level synthesis validator.
Usage: python validate_scientific_synthesis.py [input.json]
Only standard-library dependencies. Never overwrites the source file.
"""
import json, re, sys, copy
from pathlib import Path
from collections import Counter

DEFAULT = Path('data/outputs/synthesis_report_batched_improved.json')
MISSING = {'', 'not reported', 'none', 'n/a', 'unknown', 'not available'}
CITATION = re.compile(r'\[(\d+)\]')
NUMBER = re.compile(r'(?<![\w])\d+(?:[.,]\d+)?\s*%')

def clean(value):
    return ' '.join(str(value or '').split())

def present(value):
    return bool(clean(value)) and clean(value).lower() not in MISSING

def normalize_number(value):
    return re.sub(r'\s+', '', str(value)).replace(',', '.').lower()

def abstract_supports_numbers(text, abstract):
    numbers = NUMBER.findall(text)
    normalized_abstract = normalize_number(abstract)
    return all(normalize_number(n) in normalized_abstract for n in numbers)

def study_warning(study):
    return bool(study.get('quality_concerns')) or study.get('analysis_status') == 'manual_review_required'

def eligible_field(study, field):
    value = study.get(field)
    if not present(value) or study_warning(study):
        return None
    if not abstract_supports_numbers(value, study.get('abstract', '')):
        return None
    return clean(value)

def evidence_sentence(study, field, prefix):
    value = eligible_field(study, field)
    if not value:
        return None
    value = value.rstrip('.; ')
    return f'{prefix} {value} [{study["reference_number"]}].'

def paragraphs(items, max_per_paragraph=4):
    if not items:
        return ['The available abstract-level evidence is insufficient for a supported synthesis of this section; full-text verification is required.']
    return [' '.join(items[i:i+max_per_paragraph]) for i in range(0, len(items), max_per_paragraph)]

def build(input_path):
    source = json.loads(input_path.read_text(encoding='utf-8'))
    studies = source.get('study_summaries', [])
    if not isinstance(studies, list) or not studies:
        raise ValueError('No study_summaries found in input JSON')
    by_ref = {int(s['reference_number']): s for s in studies if isinstance(s, dict) and str(s.get('reference_number', '')).isdigit()}
    if len(by_ref) != len(studies):
        raise ValueError('Missing or duplicate reference_number in study_summaries')
    sections = source.get('academic_sections', {})
    original_checks = {}
    for name, content in sections.items():
        text = ' '.join(map(str, content)) if isinstance(content, list) else str(content)
        refs = [int(n) for n in CITATION.findall(text)]
        invalid = sorted(set(refs) - set(by_ref))
        numeric_without_citation = bool(NUMBER.search(text) and not refs)
        original_checks[name] = {'citation_count': len(refs), 'unique_citations': len(set(refs)), 'invalid_references': invalid, 'has_numeric_claims_without_any_citation': numeric_without_citation, 'no_citations': not bool(refs)}

    safe = [s for s in studies if not study_warning(s) and present(s.get('abstract'))]
    # Prioritize source-supported comparisons, then results, preserving source reference order.
    compared = [s for s in safe if eligible_field(s, 'reported_findings') and s.get('reported_comparisons')]
    findings = [s for s in safe if eligible_field(s, 'reported_findings')]
    # Use diverse positions, not just the first papers; capped for readable narrative.
    def sample(seq, limit=18):
        if len(seq) <= limit: return seq
        idx = sorted({round(i * (len(seq)-1)/(limit-1)) for i in range(limit)})
        return [seq[i] for i in idx]
    findings_selected = sample(findings)
    comparisons_selected = sample(compared, 16)
    findings_text = [evidence_sentence(s, 'reported_findings', 'Reported finding:') for s in findings_selected]
    findings_text = [t for t in findings_text if t]
    compare_text = []
    for s in comparisons_selected:
        comparisons = s.get('reported_comparisons') or []
        comparison = next((clean(c) for c in comparisons if present(c) and abstract_supports_numbers(c, s.get('abstract', ''))), None)
        if comparison:
            compare_text.append(f'This study reports the following within-study comparison: {comparison.rstrip(chr(46))} [{s["reference_number"]}].')
    challenges = []
    for s in sample([s for s in safe if eligible_field(s, 'limitations')], 12):
        challenges.append(evidence_sentence(s, 'limitations', 'Reported limitation:'))
    challenges = [x for x in challenges if x]
    future = []
    for s in sample([s for s in safe if s.get('future_directions')], 12):
        direction = next((clean(x) for x in s.get('future_directions', []) if present(x) and abstract_supports_numbers(x, s.get('abstract',''))), None)
        if direction:
            future.append(f'The study identifies this future direction: {direction.rstrip(chr(46))} [{s["reference_number"]}].')
    selected = sorted(set(int(n) for t in findings_text + compare_text + challenges + future for n in CITATION.findall(t)))
    preface = ('This is a preliminary, abstract-based narrative. Each statement below reports an individual study’s authors’ claims, not independently verified results. '
               'Differences in datasets, evaluation protocols and metrics prevent direct cross-study performance ranking.')
    corrected = copy.deepcopy(source)
    corrected['original_academic_sections_before_validation'] = copy.deepcopy(sections)
    corrected_sections = corrected.setdefault('academic_sections', {})
    corrected_sections['discussion_main_findings'] = [preface] + paragraphs(findings_text)
    corrected_sections['comparison_existing_literature'] = [preface] + paragraphs(compare_text)
    corrected_sections['strengths_weaknesses'] = [
        'The abstract-level evidence documents study-specific reported results, but does not establish general superiority of any model across datasets. '
        'Methodological comparability, peer-review status and full-text quality remain unverified.'
    ] + paragraphs(challenges)
    corrected_sections['implications'] = [
        'The evidence suggests candidate approaches for further evaluation, but these abstracts alone do not justify deployment recommendations or general performance rankings. '
        'Independent replication, dataset-specific validation and operational evaluation are required.'
    ]
    corrected_sections['open_challenges'] = paragraphs(challenges)
    corrected_sections['future_recommendations'] = paragraphs(future)
    conclusion = (f'This preliminary synthesis examined {len(studies)} provisionally included study records. '
                  f'It summarizes author-reported findings with explicit references to {len(selected)} studies in the rewritten evidence-based sections. '
                  'Because the review relies on abstracts and includes unverified eligibility and extraction, the results do not support universal model rankings, causal conclusions or deployment claims. '
                  'Full-text screening, quality appraisal and claim-level source verification are required before publication.')
    corrected_sections['conclusion'] = conclusion
    corrected['conclusion'] = conclusion
    corrected['research_gaps'] = challenges or ['No sufficiently supported study-specific limitations were extracted from records passing conservative screening; full-text review is required.']
    corrected['status'] = 'preliminary_validation_required'
    corrected['note'] = ('Conservative abstract-level revision. Original academic sections preserved in original_academic_sections_before_validation. '
                         'Generated narrative is not a substitute for full-text verification.')
    report = {
        'input': str(input_path), 'studies_total': len(studies),
        'studies_with_extraction_warnings': sum(study_warning(s) for s in studies),
        'studies_eligible_for_conservative_narrative': len(safe),
        'original_section_citation_checks': original_checks,
        'rewritten_section_references': selected,
        'rewritten_unique_cited_studies': len(selected),
        'important_limits': [
            'Reference presence and percentage-string matching do not establish factual correctness.',
            'Reported findings and comparisons are model-extracted; full-text checks remain necessary.',
            'Uncited high-level methodological cautions are review limitations, not claims about particular papers.',
            'Only a representative subset of safely extracted studies is narrated; all studies remain in the JSON.',
            'Thematic synthesis and research-question discussions are preserved and not independently validated.',
            'Do not describe the 111 provisionally included records as final PRISMA included studies.'
        ]
    }
    out = input_path.with_name(input_path.stem + '_validated.json')
    audit = input_path.with_name(input_path.stem + '_validation_audit.json')
    out.write_text(json.dumps(corrected, ensure_ascii=False, indent=2), encoding='utf-8')
    audit.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Saved corrected preliminary synthesis:', out)
    print('Saved validation audit:', audit)
    print(f'Studies: {len(studies)}; flagged: {report["studies_with_extraction_warnings"]}; citations in rewritten narrative: {len(selected)}')
    print('IMPORTANT: Human full-text verification still required.')

if __name__ == '__main__':
    path = Path(sys.argv[1]) if len(sys.argv)>1 else DEFAULT
    build(path)
