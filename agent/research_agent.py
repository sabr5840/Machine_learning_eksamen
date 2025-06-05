import os
import sys
from dotenv import load_dotenv
import math

# FAST valutakurs: USD → DKK
USD_TO_DKK_RATE = 7.0

load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from autogen import AssistantAgent, UserProxyAgent, register_function
from agent.agent_evaluation import evaluate_response
from config import MISTRAL_LLM_CONFIG, OPENAI_LLM_CONFIG
from tools.product_search import search_products

def usd_to_dkk(usd):
    try:
        return round(float(usd) * USD_TO_DKK_RATE)
    except Exception:
        return None

def format_products(products: list) -> str:
    """
    Konverterer en liste af produkt-dicts til en pæn tekst, hvor hver linje
    viser navn, pris i USD + DKK, butik og link. Sorterer fra billigst til dyrest.
    """
    if not products:
        return "No products found."
    def price_to_float(pris):
        if isinstance(pris, str) and pris.strip().startswith('$'):
            try:
                return float(pris.strip().replace('$', '').replace(',', ''))
            except Exception:
                return float('inf')
        return float('inf')
    sorted_products = sorted(products, key=lambda x: price_to_float(x.get('price')))
    formatted = []
    for i, p in enumerate(sorted_products, 1):
        price_str = p.get('price', '-')
        dkk_info = ""
        if price_str and isinstance(price_str, str) and price_str.strip().startswith('$'):
            usd = price_str.strip().replace('$', '').replace(',', '')
            dkk = usd_to_dkk(usd)
            if dkk is not None:
                dkk_info = f" ({dkk} DKK)"
        formatted.append(
            f"{i}. 📦 {p.get('title', 'Unknown')}\n"
            f"   💰 Price: {price_str}{dkk_info}\n"
            f"   🏪 Store: {p.get('store', '-')}\n"
            f"   🔗 Link: {p.get('link', '-') or 'Not available'}\n"
        )
    return "\n".join(formatted)

def format_evaluation(evaluation: dict) -> str:
    """
    Konverterer evaluerings-dictionary til en pæn tekst.
    """
    if "error" in evaluation:
        return f"Evaluation error: {evaluation['error']}"
    return (
        f"* Relevance: {evaluation.get('relevance', '-')}\n"
        f"* Comparison: {evaluation.get('comparison', '-')}\n"
        f"* Explanation: {evaluation.get('explanation', '-')}\n"
        f"* Detail: {evaluation.get('detail', '-')}\n"
        f"* Robustness: {evaluation.get('robustness', '-')}\n"
        f"* Usability: {evaluation.get('usability', '-')}\n"
        f"* Diversity: {evaluation.get('diversity', '-')}\n"
        f"* Price: {evaluation.get('price', '-')}\n\n"
        f"Feedback:\n{evaluation.get('feedback', '-')}"
    )

def get_product_type():
    """
    Spørger brugeren om hvilket produkt, de leder efter (f.eks. 'day cream').
    """
    query = input("What product are you looking for? (e.g. 'night cream', 'laptop', 'TV'):\n> ").strip()
    return query

def collect_user_criteria(product_type):
    """
    Fase 1: Kører en dialog med brugeren for at indsamle krav (hudtype, budget, SPF osv.).
    Returnerer en opsummering (string), der slutter med 'READY FOR SEARCH'.
    """
    system_prompt = (
        f"You are a friendly, thorough, and knowledgeable English-speaking shopping assistant who helps the user find the best product, "
        f"even if the user responds in Danish. If the user replies in Danish, answer in English but take their answers into account.\n"
        f"When the user mentions a product (e.g. '{product_type}'), you must first start a dialog with the user where you:\n"
        f"- Ask clarifying questions to understand their needs, experience, and preferences – such as skin type, finish, allergies, budget, favorite brands, or other relevant wishes/requirements for the product category.\n"
        f"- If the user does not mention specific wishes, give concrete example questions and briefly explain why they matter (e.g. 'For skincare: do you prefer fragrance free? What is your skin type? Budget?').\n"
        f"- Make the dialog easy and comfortable for the user – explain pedagogically hvorfor your questions matter.\n"
        f"**IMPORTANT:** When you have all needed answers, summarize all wishes and requirements as bullet points, so it's clear what to search for. "
        f"Then end your reply med: READY FOR SEARCH (in its own line, all caps). Do NOT ask more questions or await more user input after this.\n"
        f"You must NOT proceed to suggest products yet. Only dialog and clarification in this phase."
    )

    user_proxy = UserProxyAgent(
        name="User",
        human_input_mode="ALWAYS",
        code_execution_config={"use_docker": False}
    )
    assistant = AssistantAgent(
        name="ShoppingAssistant",
        llm_config=MISTRAL_LLM_CONFIG
    )
    # Registrer search_products som et tilgængeligt “tool”
    register_function(
        search_products,
        caller=assistant,
        executor=user_proxy,
        name="search_products",
        description="Search for products based on keywords, returning title, price, store, link and other details."
    )

    criteria_summary = ""
    # Giv modellen op til 12 samtaleturns til at besvare opklaringsspørgsmål
    for _ in range(12):
        chat_result = user_proxy.initiate_chat(
            assistant,
            message=system_prompt if not criteria_summary else "",
            summary_method="last_msg",
            max_turns=2
        )
        last_reply = chat_result.summary
        print("\n---\n", last_reply, "\n---\n")
        criteria_summary += last_reply + "\n"
        if "READY FOR SEARCH" in last_reply.upper():
            break
    else:
        # Hvis modellen aldrig siger READY FOR SEARCH
        print("Could not collect user's requirements correctly.")
    return criteria_summary

def run_shopping_search(criteria_summary: str, budget_usd: int, assistant_config):
    """
    Fase 2: Bygger prompt’en, beder modellen om at søge produkter under `budget_usd`.
    Modellen må ikke bruge kodeblokke eller JSON/array-kald efter 'TERMINATE'.
    Returnerer kun det, der står op til og med 'TERMINATE'.
    """
    user_proxy = UserProxyAgent(
        name="User",
        human_input_mode="TERMINATE",
        code_execution_config={"use_docker": False}
    )
    assistant = AssistantAgent(
        name="ShoppingAssistant",
        llm_config=assistant_config
    )
    register_function(
        search_products,
        caller=assistant,
        executor=user_proxy,
        name="search_products",
        description="Search for products based on keywords, returning title, price, store, link and other details."
    )

    def build_shopping_prompt(criteria_summary: str, budget_usd: int) -> str:
        approx_dkk = budget_usd * USD_TO_DKK_RATE
        return (
            # Gør det helt tydeligt, at vi kun vil have ren tekst
            f"Respond only in plain text; do not include any python code blocks or markdown fences.\n"
            f"Here are the user's wishes and requirements (summary):\n"
            f"{criteria_summary}\n\n"
            f"Now you must:\n"
            f"- Search for and compare relevant products matching the user's criteria. "
            f"- Show products from US/international webshops only (no Danish shops). "
            f"- Only include products under USD {budget_usd} (≈ {approx_dkk:.0f} DKK). "
            f"- If the price is in USD ($), convert it to DKK og show both. "
            f"- Always sammenlign ved hjælp af DKK-pris. "
            f"- Vis mindst 3–5 produkter. For hver: 📦 Navn, 💰 Pris, 🏪 Butik, 🔗 Link (list format + emojis).\n"
            f"- Sorter produkterne fra laveste til højeste pris i DKK. "
            f"- Marker din anbefaling med 🏆 eller ✨ og forklar kort, hvorfor netop det produkt passer til brugerens kriterier.\n"
            f"- Hvis ingen produkter findes inden for budgettet, skal du skrive 'No products found within budget' og derefter skrive TERMINATE på sin egen linje.\n"
            f"- Afslut med anbefalingen; vent ikke på yderligere input.\n"
            f"When you give your final recommendation, write TERMINATE on its own line and stop; do not make any further tool calls or code outputs."
        )

    shopping_prompt = build_shopping_prompt(criteria_summary, budget_usd)

    # Brug summary_method=None for at få hele output råt
    chat_result = user_proxy.initiate_chat(
        assistant,
        message=shopping_prompt,
        summary_method=None,
        max_turns=8
    )

    # Udtræk det samlede svar (en enkelt string, som indeholder alle modellens beskeder)
    full_response = chat_result.summary

    # Split i linjer og find 'TERMINATE'
    lines = full_response.splitlines()
    truncated_lines = []
    for line in lines:
        truncated_lines.append(line)
        if line.strip() == "TERMINATE":
            break

    # Returnér alt op til og med 'TERMINATE'
    return "\n".join(truncated_lines)

def main():
    product_type = get_product_type()

    # Brugervalgt budget i DKK (kan også hentes fra dialog, men her antaget 400)
    user_budget_dkk = 400
    # Beregn maksimal USD, rund opad, så vi aldrig overskrider 400 DKK
    budget_usd = math.ceil(user_budget_dkk / USD_TO_DKK_RATE)

    # PHASE 1: Collect user requirements (ALWAYS-mode)
    try:
        criteria_summary = collect_user_criteria(product_type)
    except Exception as e:
        print("\nMistral failed during dialog – trying OpenAI instead.\n", str(e))
        # Fallback til OpenAI hvis Mistral fejler
        user_proxy = UserProxyAgent(
            name="User",
            human_input_mode="ALWAYS",
            code_execution_config={"use_docker": False}
        )
        assistant = AssistantAgent(
            name="ShoppingAssistant",
            llm_config=OPENAI_LLM_CONFIG
        )
        register_function(
            search_products,
            caller=assistant,
            executor=user_proxy,
            name="search_products",
            description="Search for products based on keywords, returning title, price, store, link and other details."
        )
        criteria_summary = collect_user_criteria(product_type)

    # —– Indsæt budgetlinje, hvis “DKK” ikke allerede er nævnt
    if "DKK" not in criteria_summary:
        criteria_summary = criteria_summary.strip() + f"\n- Budget: omkring {user_budget_dkk} DKK\n"

    # PHASE 2: Automatic search and evaluation uden yderligere brugerinput
    MAX_TRIES = 3
    min_acceptable_score = 4

    for attempt in range(MAX_TRIES):
        print(f"\n=== Product search and evaluation, attempt {attempt + 1} ===\n")
        try:
            agent_response = run_shopping_search(criteria_summary, budget_usd, MISTRAL_LLM_CONFIG)
        except Exception as e:
            print("\nMistral failed – trying OpenAI instead!\n", str(e))
            agent_response = run_shopping_search(criteria_summary, budget_usd, OPENAI_LLM_CONFIG)

        # Udskriv, hvad modellen svarede (op til og med TERMINATE)
        print(f"\n🛍️ Agent's product suggestions:\n{agent_response}\n")

        evaluation = evaluate_response(criteria_summary, agent_response)

        # Hvis der opstod en evalueringsfejl, gør vi ikke flere forsøg
        if "error" in evaluation:
            print("\n🔍 Evaluation error:", evaluation["error"])
            print("Using last answer despite evaluation failure.\n")
            break

        print("\n🔍 Evaluation\n")
        print(format_evaluation(evaluation))

        # Tjek om der er lave scores (< min_acceptable_score)
        low_scores = [
            v for k, v in evaluation.items()
            if k in ['relevance', 'comparison', 'explanation', 'detail', 'robustness', 'usability', 'diversity', 'price']
            and isinstance(v, int) and v < min_acceptable_score
        ]
        if not low_scores:
            print("\n✅ Evaluation satisfactory! Ending with recommendation.\n")
            break

        print("\n⚠️ Output ikke tilfredsstillende. Forsøger igen baseret på feedback...\n")
        feedback = evaluation.get('feedback', '')
        criteria_summary = (
            f"{criteria_summary}\n\nPrevious evaluation feedback: {feedback}\n"
            f"Improve your product search and recommendations based on this feedback. Do NOT change the user's original criteria."
        )
    else:
        print("\n🚩 Maximum number of attempts reached – using last answer.\n")

if __name__ == "__main__":
    main()
