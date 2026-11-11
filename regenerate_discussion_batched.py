"""Run from project root. Uses cached study summaries; no search or screening."""
import json
from pathlib import Path
from agents.review_reporting import ReviewReportingAgent
from agents.batch_synthesis import synthesize

OUT=Path('data/outputs')
source=OUT/'synthesis_report.json'
if not source.exists():
    raise SystemExit(f'Missing {source}')
synthesis=json.loads(source.read_text(encoding='utf-8'))
studies=synthesis.get('study_summaries') or []
if not studies:
    raise SystemExit('No saved study_summaries found.')
questions=[r.get('question','') for r in synthesis.get('research_question_discussion',[]) if isinstance(r,dict)]
agent=ReviewReportingAgent(output_dir=str(OUT),use_llm=True,model='qwen3:4b',timeout=600)
print(f'Synthesizing all {len(studies)} saved studies in resumable batches...')
try:
    sections,audit=synthesize(agent,synthesis['research_topic'],studies,questions,batch_size=8)
except Exception as exc:
    raise SystemExit(f'Batch synthesis incomplete: {exc}\nOriginal files unchanged. Rerun to resume cached batches.')
updated=dict(synthesis)
academic=dict(updated.get('academic_sections') or {})
for k,v in sections.items():
    academic[k]=v if k=='conclusion' else [v]
updated['academic_sections']=academic
updated['conclusion']=sections['conclusion']
updated['research_gaps']=[sections['open_challenges']]
updated['academic_narrative_source']='ollama_batched_all_studies'
updated['synthesis_coverage']=audit
path=OUT/'synthesis_report_batched_improved.json'
path.write_text(json.dumps(updated,indent=2,ensure_ascii=False),encoding='utf-8')
print('\nSUCCESS:',path)
print('COVERAGE:',audit)
for k in ('discussion_main_findings','comparison_existing_literature','strengths_weaknesses',
          'implications','open_challenges','future_recommendations','conclusion'):
    print('\n'+k.upper()+'\n'+sections[k])
print('\nPreliminary abstract-based synthesis only. No source-level factual verification or PDF regeneration performed.')
