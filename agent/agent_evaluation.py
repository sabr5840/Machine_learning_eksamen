import os
import re
import sys
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from autogen import ConversableAgent
from config import LLM_CONFIG

# Evalueringsagent
critic = ConversableAgent(
    name="Critic",
    llm_config=LLM_CONFIG
)

def evaluate_response(user_prompt: str, agent_response: str) -> dict:
    critic_prompt = f"""
    Du skal evaluere en shopping-assistent AI agent, der hjælper brugeren med at finde og sammenligne produkter, og komme med en anbefaling.

    Evaluer agentens output ud fra følgende kriterier:
    - Relevans (1-5): Matcher produkterne og anbefalingen brugerens ønsker, behov og kriterier?
    - Sammenligning (1-5): Er produkterne tydeligt og retfærdigt sammenlignet på relevante kriterier (fx pris, egenskaber, butik)?
    - Forklaring (1-5): Er agentens begrundelse for anbefalingen tydelig, informativ og forståelig?
    - Detaljegrad (1-5): Indeholder output nok detaljer om produkterne (fx navn, pris, butik, vigtige funktioner) til at brugeren kan træffe et valg?
    - Robusthed (1-5): Håndterer agenten usikre eller ufuldstændige forespørgsler på en god måde?

    Brugerens prompt: {user_prompt}
    Agentens svar: {agent_response}

    Svar KUN med et gyldigt JSON-objekt i følgende format:
    {{
        "relevance": int (1-5),
        "comparison": int (1-5),
        "explanation": int (1-5),
        "detail": int (1-5),
        "robustness": int (1-5),
        "feedback": string
    }}
    """

    try:
        evaluation_response = critic.generate_reply(messages=[{"role": "user", "content": critic_prompt}])
        content = evaluation_response.get("content", "{}")

        json_str = re.search(r"\{.*\}", content, re.DOTALL).group()
        return json.loads(json_str)

    except json.JSONDecodeError:
        return {"error": "Invalid JSON from critic"}
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}
