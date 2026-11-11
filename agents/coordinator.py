
class CoordinatorAgent:
    def __init__(self, research_topic):
        self.research_topic = research_topic

    def create_plan(self):
        stages = [
            "Define review protocol",
            "Develop search strategy",
            "Retrieve scientific papers",
            "Remove duplicates",
            "Screen titles and abstracts",
            "Screen full-text articles",
            "Extract and assess evidence",
            "Synthesize findings",
            "Perform quality assurance",
            "Generate final report"
        ]

        return {
            "research_topic": self.research_topic,
            "review_stages": stages,
            "total_stages": len(stages)
        }
