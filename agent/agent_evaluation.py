# agent/agent_evaluation.py

import re
import json

from autogen import ConversableAgent
from config import MISTRAL_LLM_CONFIG, OPENAI_LLM_CONFIG
from rate_limiter import RateLimiter

# Initialiser rate limiters
mistral_rate_limiter = RateLimiter(max_calls=20, period_sec=60)
openai_rate_limiter = RateLimiter(max_calls=20, period_sec=60)

def evaluate_response(user_prompt: str, agent_response: str) -> dict:
    """
    Evaluate the shopping assistant agent's output according to fixed criteria:
    - Relevance
    - Comparison
    - Explanation
    - Detail
    - Robustness
    - Usability
    - Diversity
    - Price (DKK/budget/shops)
    """

    critic_prompt = f"""
You are an evaluation agent. Evaluate an English-language shopping assistant AI agent that helps the user find and compare products and gives a recommendation.

Evaluate the agent's output according to the following criteria (rate each 1-5):
- Relevance: Do the products and recommendations match the user's needs and criteria?
- Comparison: Are the products clearly and fairly compared on relevant criteria (e.g., price, features, store)?
- Explanation: Is the agent's justification for the recommendation clear, informative, and understandable?
- Detail: Does the output contain enough details (e.g., name, price, store, important features) for the user to make a choice?
- Robustness: Does the agent handle ambiguous or incomplete queries well?
- Usability: Is the output easy to read and understand? (e.g., bullet points, emojis, clear recommendation)
- Diversity: Are there several options, or only one solution?
- Price: Do the prices match user-specified requirements (e.g., in DKK, within budget, relevant shops)?

User's prompt and criteria:
{user_prompt}

Agent's response:
{agent_response}

Respond ONLY with a valid JSON object in the following format:
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

    mistral_rate_limiter.wait_if_needed()
    critic = ConversableAgent(
        name="Critic",
        llm_config=MISTRAL_LLM_CONFIG
    )
    try:
        evaluation_response = critic.generate_reply(messages=[{"role": "user", "content": critic_prompt}])

        if not isinstance(evaluation_response, dict):
            print("Warning: evaluation_response is not a dict. Skipping Mistral evaluation.")
            raise ValueError("Invalid response type")

        content = evaluation_response.get("content", "{}")
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if not json_match:
            print("Warning: No JSON found in Mistral response content. Skipping.")
            raise ValueError("No JSON found")

        json_str = json_match.group()
        return json.loads(json_str)

    except Exception as e:
        print("Mistral evaluation failed, trying OpenAI:", str(e))
        try:
            openai_rate_limiter.wait_if_needed()
            critic = ConversableAgent(
                name="Critic",
                llm_config=OPENAI_LLM_CONFIG
            )
            evaluation_response = critic.generate_reply(messages=[{"role": "user", "content": critic_prompt}])

            if not isinstance(evaluation_response, dict):
                print("Warning: evaluation_response is not a dict from OpenAI. Skipping evaluation.")
                raise ValueError("Invalid response type")

            content = evaluation_response.get("content", "{}")
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if not json_match:
                print("Warning: No JSON found in OpenAI response content. Skipping.")
                raise ValueError("No JSON found")

            json_str = json_match.group()
            return json.loads(json_str)

        except Exception as e2:
            print("OpenAI evaluation failed as well:", str(e2))
            return {"error": "All LLM evaluation calls failed"}
