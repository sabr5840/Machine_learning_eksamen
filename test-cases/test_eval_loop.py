from agent.agent_evaluation import evaluate_response
from agent.research_agent import format_evaluation

MAX_TRIES = 3
min_acceptable_score = 4

# Lav en liste over forskellige mock agent-svar
mock_agent_responses = [
    # Første forsøg: for kort og uden forklaring
    """
1. 📦 La Roche-Posay Hydraphase Intense Riche
   💰 Pris: 159 kr.
   🏪 Butik: Matas

🏆 Anbefaling: La Roche-Posay
""",
    # Andet forsøg: bedre, men stadig ikke detaljeret nok
    """
1. 📦 La Roche-Posay Hydraphase Intense Riche
   💰 Pris: 159 kr.
   🏪 Butik: Matas
   ⭐ Fugtgivende, parfumefri

2. 📦 Vichy Aqualia Thermal Rich
   💰 Pris: 149 kr.
   🏪 Butik: Apopro
   ⭐ Indeholder hyaluronsyre

🏆 Jeg anbefaler La Roche-Posay pga. dens fugtgivende effekt og parfumefri formel.
""",
    # Tredje forsøg: nu meget detaljeret og pædagogisk
    """
1. 📦 La Roche-Posay Hydraphase Intense Riche
   💰 Pris: 159 kr.
   🏪 Butik: Matas
   ⭐ Fugtgivende, parfumefri, til sensitiv hud

2. 📦 Vichy Aqualia Thermal Rich
   💰 Pris: 149 kr.
   🏪 Butik: Apopro
   ⭐ Indeholder hyaluronsyre, styrker hudbarrieren

3. 📦 Avene Hydrance Rich
   💰 Pris: 135 kr.
   🏪 Butik: Apoteket
   ⭐ Til tør hud, beroligende egenskaber

🏆 Jeg anbefaler La Roche-Posay, da den er meget fugtgivende, parfumefri og særligt velegnet til sensitiv og tør hud. De andre er også gode valg, især hvis du ønsker fokus på barriere eller beroligelse af huden.
"""
]

user_prompt = "Jeg vil gerne finde en dagcreme med hyaluronsyre til tør hud."

message_body = "Du skal finde og sammenligne dagcremer til tør hud med hyaluronsyre og anbefale den bedste til brugeren."

for attempt in range(MAX_TRIES):
    print(f"\n🛍️ Agentens svar (mock, forsøg {attempt + 1}):\n")
    agent_response = mock_agent_responses[attempt]
    print(agent_response)

    evaluation = evaluate_response(user_prompt, agent_response)
    print("\n🔍 Evaluering\n")
    print(format_evaluation(evaluation))

    low_scores = [v for k, v in evaluation.items() if k in ['relevance', 'comparison', 'explanation', 'detail', 'robustness', 'usability', 'diversity'] and isinstance(v, int) and v < min_acceptable_score]
    if not low_scores:
        print("\n✅ Evaluering tilfredsstillende! Slut.")
        break

    print("\n⚠️ Output ikke tilfredsstillende. Prøver igen baseret på feedback...\n")
    print("Feedback fra critic:", evaluation['feedback'])
else:
    print("\n🚩 Maks antal forsøg opbrugt – sidste svar blev brugt.")
