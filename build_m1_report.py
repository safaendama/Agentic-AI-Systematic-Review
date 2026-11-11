"""Build an M1 project report from the saved provisional screening outputs.
Run from project root: python build_m1_report.py
Requires: pip install reportlab
No claim of final systematic review or human validation.
"""
import json
from pathlib import Path
from collections import Counter
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4

ROOT=Path('data/outputs') if Path('data/outputs/screening_results_provisional.json').exists() else Path('/mnt/data')
SOURCE=ROOT/'screening_results_provisional.json'
if SOURCE.exists():
    records=json.loads(SOURCE.read_text(encoding='utf-8'))
else:
    original=json.loads((ROOT/'screening_results.json').read_text(encoding='utf-8'))
    proposals={1:'include',2:'uncertain',3:'uncertain',4:'include',5:'include',7:'include',8:'include',10:'include'}
    records=[]
    for n,item in enumerate(original,1):
        item=dict(item)
        item['decision']=proposals.get(n,'exclude')
        records.append(item)
counts=Counter(x['decision'] for x in records)
assert len(records)==10 and (counts['include'],counts['exclude'],counts['uncertain'])==(6,2,2), 'Unexpected counts; check the provisional screening input.'
OUT=ROOT/'m1_agentic_ai_project_report.pdf'
NAVY=colors.HexColor('#19334A'); BLUE=colors.HexColor('#24658A'); LIGHT=colors.HexColor('#EAF2F7'); GREY=colors.HexColor('#516273'); GREEN=colors.HexColor('#DDEFE8'); AMBER=colors.HexColor('#FFF1D1')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='HeroX',parent=styles['Title'],fontName='Helvetica-Bold',fontSize=21,leading=26,textColor=NAVY,spaceAfter=14))
styles.add(ParagraphStyle(name='SubX',fontSize=12,leading=18,textColor=BLUE,spaceAfter=12))
styles.add(ParagraphStyle(name='HX',fontName='Helvetica-Bold',fontSize=13.2,leading=17,textColor=NAVY,spaceBefore=15,spaceAfter=7,keepWithNext=True))
styles.add(ParagraphStyle(name='H2X',fontName='Helvetica-Bold',fontSize=10.3,leading=14,textColor=BLUE,spaceBefore=9,spaceAfter=4,keepWithNext=True))
styles.add(ParagraphStyle(name='BodyX',fontSize=9.3,leading=14,spaceAfter=6,textColor=colors.HexColor('#263849')))
styles.add(ParagraphStyle(name='SmallX',fontSize=8.1,leading=11,spaceAfter=4,textColor=GREY))
styles.add(ParagraphStyle(name='CellX',fontSize=8.0,leading=11,textColor=NAVY))
styles.add(ParagraphStyle(name='HeadCellX',fontName='Helvetica-Bold',fontSize=8.2,leading=11,textColor=colors.white))
P=lambda s,style='BodyX':Paragraph(escape(str(s)),styles[style])
body=[]
def add(s,style='BodyX'):body.append(P(s,style))
def section(s):add(s,'HX')
def sub(s):add(s,'H2X')
def table(rows,widths=None):
    cells=[[P(v,'HeadCellX' if i==0 else 'CellX') for v in row] for i,row in enumerate(rows)]
    t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('LINEBELOW',(0,-1),(-1,-1),0.5,colors.HexColor('#CCD8E0'))]))
    body.append(t);body.append(Spacer(1,9))

add('Agentic AI Pipeline for Systematic Literature Reviews','HeroX')
add('M1 technical report and preliminary case study','SubX')
add('Demonstration topic: Explainable Artificial Intelligence for Credit Risk Assessment')
add('Reporting status: AUTOMATED PROVISIONAL DEMONSTRATION — not a completed, independently validated systematic review.','SmallX')
body.append(Spacer(1,12))
table([['Project snapshot','Observed result'],['Workflow','10 LangGraph nodes executed successfully'],['Case-study search','10 records retrieved; 10 unique in current run'],['Abstract screening','6 provisional inclusions; 2 exclusions; 2 uncertain'],['Evidence analysis','6 abstracts processed by Step 8'],['Generated outputs','JSON evidence/synthesis/QA, preliminary PRISMA, PDF']], [175,340])
section('Executive summary')
add('This project implements a stateful, multi-agent pipeline for research protocol generation, literature search, deduplication, metadata enrichment, exploratory retrieval-augmented generation (RAG), title/abstract screening, preliminary evidence analysis, quality checks and report generation. The demonstration completed all 10 workflow stages and produced a six-record descriptive synthesis. It illustrates orchestration and reproducible intermediate artifacts, not a fully validated systematic review.')
add('The current scope is deliberately limited: five search results per source were requested, only OpenAlex and arXiv were searched in this demonstration, eligibility is based on abstracts, and no independent dual screening or full-text risk-of-bias assessment has been completed.')

section('1. Assignment alignment and deliverables')
add('The supplied M1 assignment requests a modular multi-agent review system, RAG, PRISMA-aligned reporting, traceable decisions, human oversight, source code in GitHub/GitLab, a README, a video demonstration of no more than three minutes, evaluation results and explicit individual contributions.')
table([['Assignment criterion','Current evidence / remaining gap'],['End-to-end autonomous pipeline','Demonstrated: all 10 nodes executed; outputs saved'],['Multi-source retrieval + RAG','OpenAlex and arXiv used; exploratory RAG implemented'],['PRISMA screening + extraction','Preliminary title/abstract screening and six descriptive extractions; full text pending'],['Quality / risk of bias','Automated QA flags exist; formal study-level risk-of-bias tool not yet applied'],['Reproducibility + traceability','JSON outputs and decision reasons saved; full search logs/version pinning need documenting'],['Evaluation vs manual review','No measured baseline, timing or agreement scores supplied; do not claim time savings'],['Submission package','Git repository, README, <=3-minute video and individual contribution statement must be supplied']], [165,350])

section('2. Research question and protocol')
add('Objective: To examine empirical uses of explainable AI in credit risk assessment, including predictive performance, interpretability, fairness and deployment challenges, using publications dated 2022–2026.')
for x in ['RQ1. Which XAI techniques are used for credit risk assessment in the recent literature?', 'RQ2. How do reported predictive results and interpretability methods compare across studies?', 'RQ3. What methodological, fairness and operational limitations are reported?']:add(x)
sub('Documented protocol amendment for this M1 demonstration')
add('Original rule: peer-reviewed English empirical studies only, with preprints excluded. Amended provisional rule: original empirical preprints may be considered as supplementary evidence when relevant; peer-reviewed status must not be inferred from repository records or DOI registration. The amendment was made after initial screening and is therefore transparently documented. It has not received formal researcher approval.')
add('Eligibility at abstract stage: publication year 2022–2026; directly related to XAI or interpretable models for credit risk; reports completed empirical work or concrete quantitative evaluation; English-language content appears available. Exclude secondary reviews and conceptual/legal-only work from the primary synthesis. Papers with missing abstracts or only planned research remain uncertain.')
add('Search coverage: the demonstrated retrieval used OpenAlex and arXiv, up to five records per source. Web of Science, Scopus, IEEE Xplore and ACM Digital Library were recommendations in the generated protocol, NOT databases confirmed as searched.')

section('3. System architecture and execution')
table([['Node','Function / evidence'],['1. Coordinator','Builds the review plan'],['2. Protocol','Generates research questions, eligibility criteria and search keywords'],['3. Search','Retrieves candidate records from OpenAlex and arXiv'],['4. Deduplication','Produces unique-record set and deduplication log'],['5. Retrieval + verification','Enriches metadata; Crossref provides publication metadata, not proof of peer review'],['6. Exploratory RAG','Indexes abstracts and produces grounded exploratory answers'],['7. Screening','Returns include / exclude / uncertain with reasons'],['8. Evidence analysis','Extracts methods, metrics and reported findings for six provisional records'],['9. Reporting + QA','Generates synthesis, quality notes and PRISMA-style counts'],['10. Document generation','Produces diagram and preliminary PDF']], [140,375])
add('Implementation: Python; LangGraph stateful graph; specialized agents; academic APIs (OpenAlex, arXiv, Crossref); local LLM via Ollama; RAG with document retrieval. The pipeline stores intermediate JSON artifacts to permit inspection and targeted reruns. The final demonstration reran Steps 8–10 from saved screening outputs rather than repeating search.')

section('4. Screening and preliminary PRISMA results')
table([['Stage','Count / status'],['Records identified','10'],['Duplicates removed in this run','0 (count not independently audited)'],['Records screened by title/abstract','10'],['Provisionally included for descriptive synthesis','6'],['Excluded at title/abstract screening','2'],['Uncertain, pending verification','2'],['Full texts assessed','Not established'],['Finally included after full-text review','Not established']], [300,215])
add('These are preliminary PRISMA-style counts, not a completed PRISMA 2020 eligibility flow. The 6 + 2 + 2 screening outcomes account for all 10 unique records.')
img=ROOT/'prisma_flow.png'
if not img.exists():img=Path('/mnt/data/prisma_flow(2).png')
if img.exists():
    im=Image(str(img)); im.drawWidth=510; im.drawHeight=510*im.imageHeight/im.imageWidth;body.append(im)
    add('Figure 1. Preliminary PRISMA-style flow. Full-text eligibility and final inclusion counts are intentionally not reported.','SmallX')

section('5. Evidence map: six provisionally included studies')
include=[r for r in records if r['decision']=='include']
for n,r in enumerate(include,1):
    paper=r['paper']; title=paper.get('title','Untitled'); abstract=paper.get('abstract','')
    sub(f'{n}. {title} ({paper.get("year","n.d.")})')
    doi=paper.get('doi') or paper.get('arxiv_id') or 'Not reported'
    add('Source: '+str(paper.get('source','unknown'))+' | Identifier: '+str(doi),'SmallX')
    if 'Balancing Transparency' in title:
        add('Reported approach: gradient boosting, neural networks, logistic regression and decision trees with SHAP/LIME; benchmark credit datasets mentioned but not named. Findings are qualitative in the abstract; numerical accuracy or fidelity estimates are not supplied.')
    elif 'Financial Decision Support' in title:
        add('Reported approach: peer-to-peer credit risk prediction with decision tree, random forest, SHAP and LIME. Abstract reports accuracies 0.89 and 0.93, and 0.90 and 0.93 on a larger dataset. These are author-reported figures, not independently replicated.')
    elif 'Financial and Economic Analysis' in title:
        add('Reported approach: credit-risk dataset, gradient boosting/neural networks, SHAP/LIME; accuracy, precision and recall are mentioned, but no exact metric values are supplied in the abstract. Publication metadata indicates IEEE conference proceedings; review process not independently checked.')
    elif 'Ensemble Learning and SHAP' in title:
        add('Reported approach: Home Credit dataset, logistic regression, random forest, XGBoost and LightGBM; SHAP explains feature contributions. Abstract mentions accuracy, precision and recall but gives no numerical values.')
    elif 'KACDP' in title:
        add('Reported approach: Kolmogorov-Arnold Networks for default prediction; F1 and ROC-AUC are mentioned without numerical values. Treated as supplementary preprint until publication status and methods are verified.')
    elif 'SHAP Stability' in title:
        add('Reported approach: credit-card default case study assessing SHAP explanation consistency. Abstract associates consistency with feature importance; exact stability measures are not given. DOI metadata points to a journal publication, but the screening source was arXiv.')
    else:add('Abstract-based descriptive extraction only; full text not independently checked.')

section('6. Cross-study synthesis and research implications')
add('Across the six provisionally included records, SHAP is the most frequently mentioned explanation technique, while LIME appears in several model-comparison studies. The predictive models include tree ensembles, logistic regression, neural networks and Kolmogorov-Arnold Networks. Reported evaluation measures include accuracy, precision, recall, F1 and ROC-AUC, but comparable numeric results are generally unavailable in the supplied abstracts.')
add('The central methodological gap is that predictive accuracy alone does not establish explanation quality. Future validation should separately assess faithfulness/fidelity, stability, sparsity, fairness, and reproducibility, and distinguish local feature attribution from global model behavior. No pooled effect size or meta-analysis is justified by the present extracted evidence.')

section('7. Quality assurance, evaluation and limitations')
table([['Dimension','Current status'],['Completeness','10 records processed; not a comprehensive literature search'],['Decision traceability','Per-paper screening reasons stored in JSON; amended decisions labeled provisional'],['Citation traceability','DOIs/arXiv identifiers retained; references not fully verified'],['Extraction accuracy','Abstract-derived and AI-generated; full-text cross-check pending'],['Inter-agent consistency','No quantitative agreement test recorded'],['Time savings vs manual review','Not measured; cannot claim a percentage improvement'],['Risk of bias','No validated appraisal instrument applied'],['Human oversight','Human-review worksheet available; review not completed']], [170,345])
add('Important caveats: Crossref registration, an ISSN, or the label “publishedVersion” does not prove peer review. Automated summaries may overstate results, confuse proposed work with completed experiments, or omit negative findings. The small top-five-per-source search is a software demonstration, not a systematic search with high recall.')

section('8. Reproducibility and execution instructions')
add('Environment: activate the Python virtual environment, install dependencies specified by the project, ensure the local Ollama model is available, and configure academic retrieval tools. Run the main 10-node workflow for a fresh search; use the saved provisional screening outputs for the separate final-three-steps demonstration.')
add('Demonstration commands: python test_full_workflow.py; python prepare_provisional_screening.py; python run_final_steps.py; python build_m1_report.py. Outputs are written to data/outputs/. Version numbers, API configuration and full dependency lockfile should be recorded in README.md before submission.')
add('Suggested evaluation for a future validated version: measure precision/recall of screening against a manually labeled sample, extraction exact-match or factual consistency, decision agreement between agents and human reviewers, completeness of required PRISMA fields, execution time and error rate. These measurements have not yet been performed.')

section('9. Submission checklist and individual contributions')
for x in ['Source code: publish the working project to GitHub or GitLab and confirm access.', 'README.md: explain environment, dependencies, API keys, Ollama, setup, commands, outputs and limitations.', 'Video: record a demonstration lasting no longer than three minutes, showing inputs, agent execution, screening, evidence synthesis and outputs.', 'Team statement: add each student’s actual role and contributions. No contribution claims have been invented in this report.', 'Evaluation: report actual measurements if available; otherwise explicitly mark as pending.']:add('• '+x)
sub('Individual contribution declaration — complete before submission')
add('Student / team member: ____________________   Contribution (implemented agents, testing, documentation, video, etc.): ____________________.')

section('10. References and source provenance')
add('The six bibliographic records below were supplied by the automated retrieval outputs. Bibliographic details and claims should be checked against the original publications before academic citation.')
for i,r in enumerate(include,1):
    p=r['paper'];add(f'{i}. {p.get("title","Untitled")} ({p.get("year","n.d.")}). {p.get("doi") or p.get("arxiv_id") or "Identifier unavailable"}.','SmallX')
add('Project specification: “Development of an Agentic AI Pipeline for Conducting Rigorous, Transparent, and Reproducible Systematic Reviews on Any Given Topic” (M1 assignment provided by the user).','SmallX')


def footer(canvas,doc):
    canvas.saveState();w,h=A4
    canvas.setStrokeColor(colors.HexColor('#D4E0E8'));canvas.line(42,40,w-42,40)
    canvas.setFont('Helvetica',8);canvas.setFillColor(GREY)
    canvas.drawString(43,28,'M1 Agentic AI project | Automated provisional report')
    canvas.drawRightString(w-43,28,f'Page {doc.page}')
    canvas.restoreState()

doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=43,leftMargin=43,topMargin=46,bottomMargin=55,title='M1 Agentic AI Project - Technical Report',author='Automated M1 demonstration')
doc.build(body,onFirstPage=footer,onLaterPages=footer)
print('Created:',OUT)
print('Counts:',dict(counts))
