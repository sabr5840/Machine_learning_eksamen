import os
import sys
import math
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.product_search import search_products
from agent.agent_evaluation import (
    evaluate_response,
    build_search_query,
    optimize_search_query_llm
)
from config import MISTRAL_LLM_CONFIG, OPENAI_LLM_CONFIG
from autogen import AssistantAgent, UserProxyAgent

USD_TO_DKK_RATE = 7.0

def usd_to_dkk(usd: float) -> int:
    try:
        return round(usd * USD_TO_DKK_RATE)
    except Exception:
        return None

def format_products(products: list) -> str:
    if not products:
        return "Ingen produkter fundet."
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
            try:
                usd_val = float(price_str.strip().replace('$', '').replace(',', ''))
                dkk_val = usd_to_dkk(usd_val)
                if dkk_val is not None:
                    dkk_info = f" ({dkk_val} DKK)"
            except:
                pass
        formatted.append(
            f"{i}. 📦 {p.get('title', 'Unknown')}\n"
            f"   💰 Price: {price_str}{dkk_info}\n"
            f"   🏪 Store: {p.get('store', '-')}\n"
            f"   🔗 Link: {p.get('link', '-') or 'Ikke tilgængelig'}\n"
        )
    return "\n".join(formatted)

def get_product_type() -> str:
    query = input("Hvad søger du efter? (f.eks. 'day cream', 'laptop', 'TV'):\n> ").strip()
    return query

def collect_user_criteria(product_type: str) -> str:
    system_prompt = (
        f"You are a friendly, thorough, and knowledgeable English-speaking shopping assistant who helps the user find the best product, "
        f"even if the user responds in Danish. If the user replies in Danish, answer in English but take their answers into account.\n"
        f"When the user mentions a product (e.g. '{product_type}'), you must first start a dialog with the user where you:\n"
        f"- Ask clarifying questions to understand their needs, experience, and preferences – such as skin type, finish, allergies, budget, favorite brands, or other relevant wishes/requirements for the product category.\n"
        f"- If the user does not mention specific wishes, give concrete example questions and briefly explain why they matter (e.g. 'For skincare: do you prefer fragrance free? What is your skin type? Budget?').\n"
        f"- Make the dialog easy and comfortable for the user – explain pedagogically why your questions matter.\n"
        f"**IMPORTANT:** When you have all needed answers, summarize all wishes and requirements as bullet points, so it's clear what to search for. "
        f"Then end your reply with: READY FOR SEARCH (on its own line, all caps). Do NOT ask more questions or await more user input after this.\n"
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
    from autogen import register_function
    register_function(
        search_products,
        caller=assistant,
        executor=user_proxy,
        name="search_products",
        description="Search for products based on keywords, returning title, price, store, link and other details."
    )

    criteria_summary = ""
    for _ in range(12):
        chat_result = user_proxy.initiate_chat(
            assistant,
            message=system_prompt if not criteria_summary else "",
            summary_method="last_msg",
            max_turns=2
        )
        last_reply = chat_result.summary
        print("\n" + "-"*80)
        print(last_reply)
        print("\n" + "-"*80 + "\n")
        criteria_summary += last_reply + "\n"
        if "READY FOR SEARCH" in last_reply.upper():
            break
    else:
        print("Kunne ikke indsamle brugerens krav korrekt. Stopper.")
        sys.exit(1)
    return criteria_summary

def run_product_loop(product_type: str, criteria_summary: str, budget_usd: int, max_tries: int = 8, min_avg_score: float = 4.0):
    final_products = []
    best_avg_score = 0.0
    best_filtered = []
    best_evaluation = None
    last_feedback = ""
    for attempt in range(1, max_tries + 1):
        print(f"\n=== Forsøg {attempt} på produkt-search og evaluering ===\n")
        # Første iteration = klassisk build_search_query, herefter bruger vi feedback-optimeret søgestreng
        if attempt == 1 or not last_feedback:
            search_query = build_search_query(product_type, criteria_summary)
        else:
            print(f"\n🔁 Forbedrer søgestrengen med LLM baseret på feedback...\n")
            search_query = optimize_search_query_llm(product_type, criteria_summary, last_feedback)
        print(f"🔎 Søger efter: “{search_query}” (max USD {budget_usd})\n")
        raw_products = search_products(search_query, max_results=5)
        def parse_usd_price(p):
            price = p.get("price", "")
            if isinstance(price, str) and price.startswith('$'):
                try:
                    return float(price.replace('$', '').replace(',', ''))
                except:
                    return None
            return None
        filtered = []
        for p in raw_products:
            usd_val = parse_usd_price(p)
            if usd_val is None or usd_val <= budget_usd:
                filtered.append(p)
        if not filtered:
            print("⚠️ Ingen produkter fundet inden for budgettet. Stopper.\n")
            sys.exit(0)
        formatted_text = format_products(filtered)
        print("🛍️ Fundne produkter (sorteret fra billigst til dyrest):\n")
        print(formatted_text)
        evaluation = evaluate_response(criteria_summary, formatted_text)
        if "error" in evaluation:
            print("\n🔍 Evaluator-agenten fejlede:", evaluation["error"])
            final_products = filtered
            break
        # Udregn gennemsnitsscoren
        score_keys = ['relevance','comparison','explanation','detail','robustness','usability','diversity','price']
        scores = [evaluation.get(k, 0) for k in score_keys if isinstance(evaluation.get(k, 0), int)]
        avg_score = sum(scores) / len(scores) if scores else 0
        print("\n🔍 Evaluering af fundne produkter:")
        for key in score_keys:
            print(f"  * {key.capitalize():<10}: {evaluation.get(key)}")
        print(f"\n  Feedback:\n{evaluation.get('feedback')}\n")
        print(f"  ** Gennemsnitsscore: {avg_score:.2f} **\n")
        # Gem bedste forsøg hvis det er bedre end før
        if avg_score > best_avg_score:
            best_avg_score = avg_score
            best_filtered = filtered
            best_evaluation = evaluation
        if avg_score >= min_avg_score:
            print("✅ Evaluering tilfredsstillende – går videre til endelig anbefaling.\n")
            final_products = filtered
            break
        else:
            print("⚠️ For lav gennemsnitsscore, prøver igen med feedback.\n")
            last_feedback = evaluation.get('feedback') or ""
            criteria_summary += f"\n\nPrevious feedback: {last_feedback}"
    else:
        print(f"🚩 Maks. forsøg nået – bruger bedste fund med gennemsnitsscore {best_avg_score:.2f}.\n")
        final_products = best_filtered
    return final_products

def final_comparison_and_recommendation(products: list, criteria_summary: str):
    lines = []
    for i, p in enumerate(products, 1):
        price = p.get("price", "-")
        dkk = ""
        if isinstance(price, str) and price.startswith('$'):
            try:
                dkk = f" ({usd_to_dkk(float(price.replace('$','').replace(',',''))) } DKK)"
            except:
                pass
        lines.append(f"{i}. {p.get('title')} – Price: {price}{dkk} – Store: {p.get('store')} – Link: {p.get('link')}")
    products_text = "\n".join(lines)
    prompt = (
        "Du er en venlig shopping-assistent. Sammenlign nu de fem produkter herunder, "
        "tag udgangspunkt i brugerens krav og vælg ét som din endelige anbefaling. "
        "Forklar kort hvorfor netop det produkt opfylder kravene bedst.\n\n"
        f"Brugerens krav:\n{criteria_summary}\n\n"
        f"Produkter:\n{products_text}\n\n"
        "Skriv dit svar på engelsk i punktform, marker anbefalingen med 🏆.\n"
        "Reply ONLY with bullet points and your final recommendation in plain text. "
        "Do NOT include any Python code, code blocks or attempt to print or execute code."
    )
    assistant = AssistantAgent(name="FinalRecommender", llm_config=OPENAI_LLM_CONFIG)
    user_proxy = UserProxyAgent(name="User", human_input_mode="TERMINATE", code_execution_config={"use_docker": False})
    chat = user_proxy.initiate_chat(assistant, message=prompt, summary_method=None, max_turns=4)
    print("\n" + "-"*80)
    print(chat.summary)
    print("\n" + "-"*80)

def main():
    product_type = get_product_type()
    criteria_summary = collect_user_criteria(product_type)
    print("\n" + "-"*80)
    print("Your criteria summary:")
    print(criteria_summary.strip())
    print("-"*80 + "\n")
    confirm = input("Approve and start search? (yes to continue):\n> ").strip().lower()
    if confirm != 'yes':
        print("Search cancelled. Please restart and adjust your criteria if needed.")
        sys.exit(0)
    if "DKK" not in criteria_summary.upper():
        user_budget_dkk = 400
        criteria_summary += f"\n- Budget: omkring {user_budget_dkk} DKK\n"
    else:
        user_budget_dkk = 400
    budget_usd = math.ceil(user_budget_dkk / USD_TO_DKK_RATE)
    final_products = run_product_loop(product_type, criteria_summary, budget_usd, max_tries=8, min_avg_score=4.0)
    final_comparison_and_recommendation(final_products, criteria_summary)

if __name__ == "__main__":
    main()
