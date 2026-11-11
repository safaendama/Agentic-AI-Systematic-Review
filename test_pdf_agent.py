from agents.pdf_report import PDFReportAgent
from pathlib import Path
protocol={"research_topic":"Example Topic","research_objective":"Assess published methods.","research_questions":[{"question":"Which methods are used?"},"What metrics are reported?"],"databases":["OpenAlex","arXiv"]}
synthesis={"research_topic":"Example Topic","screening_summary":{"total":2,"provisionally_included":1,"excluded":1,"uncertain":0},"study_summaries":[{"reference_number":1,"title":"Example Study","year":2025,"authors":["A. Author"],"methods_mentioned_in_abstract":["Method A"],"dataset":"Dataset X","evaluation_metrics":"Accuracy","reported_findings":"Method A achieved 80% accuracy."}],"research_question_discussion":[{"question":"Which methods are used?","evidence_based_observation":"Method A [1]."}],"academic_sections":{"abstract":"Preliminary abstract-level synthesis.","conclusion":"Human verification is needed."}}
qa={"limitations":["Full-text verification pending."]}
prisma={"records_identified":2,"duplicates_removed":0,"records_after_deduplication":2,"records_screened_title_abstract":2,"records_provisionally_included":1,"records_excluded_title_abstract":1,"records_uncertain":0,"studies_finally_included":None}
p=PDFReportAgent(output_dir="data/outputs").generate(protocol,synthesis,qa,prisma)
print('PDF exists:',Path(p).exists(),'Bytes:',Path(p).stat().st_size)
