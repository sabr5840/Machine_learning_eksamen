import os
import re
import sys
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from autogen import ConversableAgent
from config import MISTRAL_LLM_CONFIG, OPENAI_LLM_CONFIG

def evaluate_response(user_prompt: str, agent_response: str) -> dict:
    """
    Evaluerer shoppingagentens output ud fra faste kriterier:
    - Relevans
    - Sammenligning
    - Forklaring
    - Detaljegrad
    - Robusthed
    - Brugervenlighed
    - Diversitet
    - Pris (DKK/budget/danske shops)
    """

    critic_prompt = f"""
Du skal evaluere en dansk shopping-assistent AI agent, der hjælper brugeren med at finde og sammenligne produkter, og komme med en anbefaling.

Evaluer agentens output ud fra følgende kriterier:
- Relevans (1-5): Matcher produkterne og anbefalingen brugerens ønsker, behov og kriterier?
- Sammenligning (1-5): Er produkterne tydeligt og retfærdigt sammenlignet på relevante kriterier (fx pris, egenskaber, butik)?
- Forklaring (1-5): Er agentens begrundelse for anbefalingen tydelig, informativ og forståelig?
- Detaljegrad (1-5): Indeholder output nok detaljer om produkterne (fx navn, pris, butik, vigtige funktioner) til at brugeren kan træffe et valg?
- Robusthed (1-5): Håndterer agenten usikre eller ufuldstændige forespørgsler på en god måde?
- Brugervenlighed (1-5): Er output let at læse og forstå? (fx brug af punktform, emojis, tydelig anbefaling)
- Diversitet (1-5): Giver agenten flere forskellige valgmuligheder, eller kun én løsning?
- Pris (1-5): Matcher priserne brugerspecifikke krav (fx pris i DKK, inden for budget, danske shops)?

Brugerens prompt og kriterier:
{user_prompt}

Agentens svar:
{agent_response}

Svar KUN med et gyldigt JSON-objekt i følgende format:
{{
    "relevance": int,
    "comparison": int,
    "explanation": int,
    "detail": int,
    "robustness": int,
    "usability": int,
    "diversity": int,
    "price": int,
    "feedback": string
}}
"""

    # Først: prøv Mistral
    critic = ConversableAgent(
        name="Critic",
        llm_config=MISTRAL_LLM_CONFIG
    )
    try:
        evaluation_response = critic.generate_reply(messages=[{"role": "user", "content": critic_prompt}])
        content = evaluation_response.get("content", "{}")
        json_str = re.search(r"\{.*\}", content, re.DOTALL).group()
        return json.loads(json_str)
    except Exception as e:
        print("Mistral fejlede, prøver OpenAI:", str(e))
        try:
            critic = ConversableAgent(
                name="Critic",
                llm_config=OPENAI_LLM_CONFIG
            )
            evaluation_response = critic.generate_reply(messages=[{"role": "user", "content": critic_prompt}])
            content = evaluation_response.get("content", "{}")
            json_str = re.search(r"\{.*\}", content, re.DOTALL).group()
            return json.loads(json_str)
        except Exception as e2:
            print("OpenAI fejlede også:", str(e2))
            return {"error": "Alle LLM-kald fejlede"}

