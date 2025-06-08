# agent/agent_evaluation.py

import re
import json
from autogen import ConversableAgent
from config import MISTRAL_LLM_CONFIG, OPENAI_LLM_CONFIG
from rate_limiter import RateLimiter

mistral_rate_limiter = RateLimiter(max_calls=20, period_sec=60)
openai_rate_limiter = RateLimiter(max_calls=20, period_sec=60)

def evaluate_response(user_prompt: str, agent_response: str) -> dict:
    """
    Evaluér output fra shopping-agenten ud fra fastsatte kriterier.
    Returnerer JSON/dict med scorer og feedback.
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

def build_search_query(product_type: str, criteria_summary: str) -> str:
    """
    Bygger søgestreng på baggrund af produkt og kriterier.
    Bruges kun til første søgning, derefter optimerer vi med LLM og feedback.
    """
    lines = [
        lin.strip('-* ').strip()
        for lin in criteria_summary.splitlines()
        if lin.strip().startswith(('-', '*'))
    ]
    keywords = [product_type]
    for lin in lines:
        clean = lin.replace('**', '')
        if ':' in clean:
            label, answer = clean.split(':', 1)
            answer = answer.strip()
            words = answer.split()
            keywords.append(' '.join(words[:2]))
        else:
            kws = clean.lower().replace(',', '').split()
            if kws:
                keywords.append(' '.join(kws[:2]))
    seen = set()
    final = []
    for kw in keywords:
        low = kw.lower()
        if low not in seen:
            final.append(kw)
            seen.add(low)
    return ' '.join(final)

def optimize_search_query_llm(product_type: str, criteria_summary: str, last_feedback: str) -> str:
    """
    Bruger LLM til at foreslå bedre søgeord ud fra feedback.
    Først prøver vi Mistral, hvis den fejler, falder vi tilbage til OpenAI.
    """
    prompt = f"""You are an expert product search optimizer for Google Shopping.
A user is searching for: "{product_type}"
Their criteria are (in bullet points):
{criteria_summary}

The previous product search and recommendations were evaluated with this feedback:
{last_feedback}

Based on the criteria and the feedback, generate an improved and concrete Google Shopping search string (max 12 words) that will help find the most relevant products for the user. Use synonyms or relax constraints if needed. Respond ONLY with the improved search string."""
    
    # Først prøv Mistral
    try:
        optimizer = ConversableAgent(
            name="SearchOptimizer",
            llm_config=MISTRAL_LLM_CONFIG
        )
        result = optimizer.generate_reply([{"role": "user", "content": prompt}])
        if isinstance(result, dict):
            search_query = result.get('content', '').strip()
        else:
            search_query = str(result).strip()
        search_query = search_query.split('\n')[0].strip()
        return search_query
    except Exception as e:
        print("Mistral (optimize_search_query_llm) failed, trying OpenAI:", str(e))
        try:
            optimizer = ConversableAgent(
                name="SearchOptimizer",
                llm_config=OPENAI_LLM_CONFIG
            )
            result = optimizer.generate_reply([{"role": "user", "content": prompt}])
            if isinstance(result, dict):
                search_query = result.get('content', '').strip()
            else:
                search_query = str(result).strip()
            search_query = search_query.split('\n')[0].strip()
            return search_query
        except Exception as e2:
            print("OpenAI (optimize_search_query_llm) failed as well:", str(e2))
            return "artificial flower"  # fallback søgeord (eller vælg noget neutralt)
