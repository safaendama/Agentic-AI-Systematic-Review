"""Create transparent, automated PROVISIONAL screening for an M1 demo.
No human review or independent peer-review verification is claimed.
Run from project root: python prepare_provisional_screening.py
"""
import json
from copy import deepcopy
from pathlib import Path

out = Path('data/outputs')
src = out / 'screening_results.json'
with src.open(encoding='utf-8') as f:
    records = json.load(f)

# Paper IDs are 1-based positions in the supplied screening_results.json.
proposals = {
    1: ('include', 'primary_candidate', 'Abstract describes XAI models and evaluation on credit-risk benchmarks; publication review still unverified.'),
    2: ('uncertain', 'full_text_required', 'Abstract proposes questionnaire/SEM research and describes expected results; completed empirical evaluation is not established.'),
    3: ('uncertain', 'full_text_required', 'Abstract missing; Zenodo record alone cannot establish empirical eligibility.'),
    4: ('include', 'primary_candidate', 'Abstract reports credit-risk experiments, accuracy results and SHAP/LIME analysis.'),
    5: ('include', 'primary_candidate', 'Abstract reports credit-risk experiments, predictive metrics and SHAP/LIME; conference review unverified.'),
    7: ('include', 'primary_candidate', 'Abstract reports Home Credit experiments and SHAP feature analysis; conference review unverified.'),
    8: ('include', 'supplementary_preprint', 'Abstract reports KAN credit-default experiments, ROC-AUC/F1 and interpretability; peer review unverified.'),
    10: ('include', 'primary_candidate', 'Abstract reports a SHAP-stability case study in credit-card default risk.'),
}

result = deepcopy(records)
for idx, item in enumerate(result, 1):
    if idx not in proposals:
        # Keep the original exclusions provisional.
        continue
    decision, category, rationale = proposals[idx]
    item['original_screening_decision'] = item['decision']
    item['original_screening_reason'] = item['reason']
    item['decision'] = decision
    item['reason'] = rationale
    item['screening_status'] = 'automated_provisional_after_protocol_amendment'
    item['requires_human_review'] = True
    item['evidence_category'] = category
    item['peer_review_verification_not_claimed'] = True

summary = {
    'total': len(result),
    'provisionally_included': sum(r['decision']=='include' for r in result),
    'provisionally_excluded': sum(r['decision']=='exclude' for r in result),
    'uncertain': sum(r['decision']=='uncertain' for r in result),
    'human_review_completed': False,
    'screening_status': 'automated_provisional_for_M1_demonstration',
    'protocol_amendment': 'Relevant original empirical preprints may be used as supplementary evidence; publication status is reported separately.',
    'limitations': 'Abstract-based eligibility only; no independent verification of peer review, language, full-text methods or data extraction. Do not describe as final PRISMA eligibility.'
}
out.mkdir(parents=True, exist_ok=True)
for name, obj in [('screening_results_provisional.json', result), ('screening_summary_provisional.json', summary)]:
    with (out/name).open('w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
print('AUTOMATED PROVISIONAL SCREENING CREATED')
print(json.dumps(summary, indent=2))
print('Saved:', out/'screening_results_provisional.json')
print('Saved:', out/'screening_summary_provisional.json')
