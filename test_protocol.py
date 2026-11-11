
from agents.protocol import ProtocolAgent

topic = "Explainable Artificial Intelligence for Credit Risk Assessment"

agent = ProtocolAgent()
protocol = agent.generate_protocol(topic)

print("\nINCLUSION CRITERIA:")
for criterion in protocol["inclusion_criteria"]:
    print("-", criterion)

print("\nEXCLUSION CRITERIA:")
for criterion in protocol["exclusion_criteria"]:
    print("-", criterion)

print("\nSTATUS:", protocol["status"])
