"""Regenerate topic-independent academic prose from saved synthesis using Ollama.
Run from project root: python regenerate_discussion_from_saved.py
Does not rerun search, screening, or evidence extraction.
"""
import json
from pathlib import Path
from agents.review_reporting import ReviewReportingAgent

OUT = Path('data/outputs')
source = OUT / 'synthesis_report.json'
if not source.exists():
    raise SystemExit(f'Missing {source}; copy your saved synthesis JSON there first.')
synthesis = json.loads(source.read_text(encoding='utf-8'))
studies = synthesis.get('study_summaries') or []
if not studies:
    raise SystemExit('No study_summaries in synthesis JSON.')
questions = [r.get('question','') for r in synthesis.get('research_question_discussion',[]) if isinstance(r,dict)]
agent = ReviewReportingAgent(output_dir=str(OUT), use_llm=True, model='qwen3:4b')
agent._narrative_source = 'deterministic_fallback'
agent._ollama_failed = False
agent._ollama_error = None
print(f'Generating topic-specific academic discussion from {len(studies)} saved studies...')
sections = agent._generate_academic_narrative(synthesis['research_topic'], studies, questions, {})
if agent._narrative_source != 'ollama' or agent._ollama_failed:
    raise SystemExit('Ollama did not generate a valid discussion: ' + str(agent._ollama_error) + '\nNo output was overwritten. Check Ollama is running and qwen3:4b is installed.')
updated = dict(synthesis)
updated['academic_sections'] = {**synthesis.get('academic_sections',{}), **sections}
updated['academic_narrative_source'] = 'ollama'
path = OUT / 'synthesis_report_discussion_improved.json'
path.write_text(json.dumps(updated, indent=2, ensure_ascii=False), encoding='utf-8')
print('SUCCESS:', path)
for key in ('discussion_main_findings','comparison_existing_literature','strengths_weaknesses','implications'):
    print('\n'+key.upper()+'\n'+ '\n'.join(sections[key]))
print('\nNOTE: This updates academic narrative sections, not full-text validation, gap-list generation, or final conclusions.')
