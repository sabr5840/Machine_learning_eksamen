from agent.agent_evaluation import evaluate_response
from agent.research_agent import format_evaluation

user_prompt = "Jeg vil gerne finde en dagcreme med hyaluronsyre til tør hud."
agent_response = """
1. 📦 La Roche-Posay Hydraphase Intense Riche
   💰 Pris: 159 kr.
   🏪 Butik: Matas
   ⭐ Fugtgivende, til tør hud, parfumefri

2. 📦 Vichy Aqualia Thermal Rich
   💰 Pris: 149 kr.
   🏪 Butik: Apopro
   ⭐ Hyaluronsyre, styrker hudbarrieren

🏆 Jeg anbefaler La Roche-Posay, da den både er meget fugtgivende, parfumefri og velegnet til sensitiv hud.
"""

eval_result = evaluate_response(user_prompt, agent_response)
print("🔍 Evaluering af agentens output:\n")
print(format_evaluation(eval_result))
