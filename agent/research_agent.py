# agent/research_agent.py

import os
import sys
import math
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.product_search import search_products
from agent.agent_evaluation import evaluate_response
from config import MISTRAL_LLM_CONFIG, OPENAI_LLM_CONFIG
from autogen import AssistantAgent, UserProxyAgent, register_function

# FAST valutakurs: USD → DKK
USD_TO_DKK_RATE = 7.0

def usd_to_dkk(usd: float) -> int:
    """
    Helper: Konverter USD (float) → DKK (afrundet int).
    """
    try:
        return round(usd * USD_TO_DKK_RATE)
    except Exception:
        return None

def format_products(products: list) -> str:
    """
    Konverterer en liste af produkt-dicts til en pæn tekst, hvor hver linje
    viser navn, pris i USD + DKK, butik og link. Sorteret fra billigst til dyrest.
    """
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
    """
    Spørger brugeren i terminalen: “Hvilket produkt leder du efter?”
    """
    query = input("Hvad søger du efter? (f.eks. 'night cream', 'laptop', 'TV'):\n> ").strip()
    return query

def collect_user_criteria(product_type: str) -> str:
    """
    Fase 1: Kører en dialog via LLM for at indsamle krav. 
    Returnerer en opsummeringstekst, der slutter med 'READY FOR SEARCH'.
    """
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

    # Sætter AssistantAgent (ShoppingAssistant) og UserProxyAgent (User) op
    user_proxy = UserProxyAgent(
        name="User",
        human_input_mode="ALWAYS",
        code_execution_config={"use_docker": False}
    )
    assistant = AssistantAgent(
        name="ShoppingAssistant",
        llm_config=MISTRAL_LLM_CONFIG
    )
    # Registrer search_products hos LLM’en, men vi kommer faktisk ikke til at bruge den direkte i denne fase
    register_function(
        search_products,
        caller=assistant,
        executor=user_proxy,
        name="search_products",
        description="Search for products based on keywords, returning title, price, store, link and other details."
    )

    criteria_summary = ""
    # Giv modellen op til 12 samtaleturns til at stille opklarende spørgsmål
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
        # Hvis modellen aldrig siger READY FOR SEARCH, giv fejlbesked
        print("Kunne ikke indsamle brugerens krav korrekt. Stopper.")
        sys.exit(1)

    return criteria_summary

def build_search_query(criteria_summary: str) -> str:
    """
    Simpel heuristic til at danne en søgestreng ud fra krav-summeriet.
    F.eks. udtræk kernesætninger som 'night cream', 'dry skin', 'dewy finish', 'SPF', 'no fragrance', 'redness hyperpigmentation'.
    Her laver vi bare en “naiv” sammensætning: find nøgleord i teksten og join dem.
    """
    # NOTE: Man kan lave mere avanceret NLP, men lad os holde det simpelt:
    #   - Splits alle bullet-punkter fra criteria_summary
    #   - Tag nøgleord (korte ord) ud fra hver linje
    lines = [lin.strip("-* ").lower() for lin in criteria_summary.splitlines() if lin.strip().startswith("-")]
    # Tag f.eks. de vigtigste ord ud til søgning
    keywords = []
    for lin in lines:
        # Lad os splitte på mellemrum og tag de 2-3 vigtigste ord per linje
        words = lin.replace(",", "").split()
        if len(words) > 0:
            # Vælg 1-2 centrale ord: de første ord, evt. “night cream” oversættes ikke, men vi gætter
            if len(words) >= 2:
                keywords.append(words[0] + " " + words[1])
            else:
                keywords.append(words[0])
    # Sørg for "night cream" står med
    if "night cream" not in " ".join(keywords):
        keywords.insert(0, "night cream")
    # Tilføj budget-nøgleord hvis den findes
    for lin in lines:
        if "budget" in lin:
            # Eksempel: "budget: omkring 200-400 dkk"
            keywords.append("under budget")
    # Sammensæt alt til en enkelt streng
    query = " ".join(keywords)
    return query

def run_product_loop(criteria_summary: str, budget_usd: int, max_tries: int = 3, min_score: int = 4):
    """
    Fase 2: Kald direkte search_products, formater output, kør evaluation, og loop feedback tilbage.
    Returnerer en liste af 5 “endelige” produkter (som dicts), samt deres formaterede tekst.
    """
    final_products = []
    last_feedback = ""
    for attempt in range(1, max_tries + 1):
        print(f"\n=== Forsøg {attempt} på produkt-search og evaluering ===\n")

        # 1) Byg søge-streng
        search_query = build_search_query(criteria_summary)
        print(f"🔎 Søger efter: “{search_query}” (max USD {budget_usd})\n")

        # 2) Kald search_products med max_results=5
        raw_products = search_products(search_query, max_results=5)

        # 3) Filtrér evt. dem, der er over budget_usd (---- MEN: search_products giver allerede kun top 5).
        #    Hvis der er priser i USD, skal vi parse dem, konvertere til float og droppe dem, der > budget_usd
        def parse_usd_price(pdict):
            pris = pdict.get("price", "")
            if isinstance(pris, str) and pris.startswith('$'):
                try:
                    return float(pris.replace('$', '').replace(',', ''))
                except:
                    return None
            return None

        filtered = []
        for p in raw_products:
            usd_val = parse_usd_price(p)
            if usd_val is None:
                # Hvis vi ikke kan parse price, behold produktet (for så evaluerer vi manuelt senere)
                filtered.append(p)
            else:
                if usd_val <= budget_usd:
                    filtered.append(p)
        # Hvis der er færre end 5 inden for budget, beholder vi dem alligevel – men advaret LLM’en?
        if not filtered:
            print("⚠️ Ingen produkter fundet inden for budgettet. Stopper.\n")
            sys.exit(0)

        # 4) Formater dem til output i terminalen
        formatted_text = format_products(filtered)
        print("🛍️ Fundne produkter (sorteret fra billigst til dyrest):\n")
        print(formatted_text)

        # 5) Kør evaluator på “kriterier + produkterne som tekst”
        evaluation = evaluate_response(criteria_summary, formatted_text)

        # 6) Udskriv evaluering (pænt)
        if "error" in evaluation:
            print("\n🔍 Evaluator-agenten fejlede med besked:", evaluation["error"])
            print("👉 Bruger sidste fund som endelige produkter.\n")
            final_products = filtered
            break

        # Udskriv scores + feedback
        print("\n🔍 Evaluering af fundne produkter:\n")
        print(
            f"  * Relevance : {evaluation.get('relevance')}\n"
            f"  * Comparison: {evaluation.get('comparison')}\n"
            f"  * Explanation: {evaluation.get('explanation')}\n"
            f"  * Detail    : {evaluation.get('detail')}\n"
            f"  * Robustness: {evaluation.get('robustness')}\n"
            f"  * Usability : {evaluation.get('usability')}\n"
            f"  * Diversity : {evaluation.get('diversity')}\n"
            f"  * Price     : {evaluation.get('price')}\n"
            f"\n  Feedback:\n{evaluation.get('feedback')}\n"
        )

        # 7) Tjek om alle scores ≥ min_score
        low_scores = [
            score for key, score in evaluation.items()
            if key in ['relevance', 'comparison', 'explanation', 'detail', 'robustness', 'usability', 'diversity', 'price']
            and isinstance(score, int) and score < min_score
        ]
        if not low_scores:
            print("✅ Evaluering tilfredsstillende – går videre til endelig anbefaling.\n")
            final_products = filtered
            break
        else:
            # 8) Hent feedback og tilføj til criteria_summary
            last_feedback = evaluation.get('feedback', '')
            print("⚠️ Evaluering under standard – prøver igen baseret på feedback:\n", last_feedback, "\n")
            criteria_summary = (
                f"{criteria_summary}\n\n"
                f"Previous evaluation feedback: {last_feedback}\n"
                f"Improve your product search and recommendations based on this feedback. "
                f"Do NOT change the user's original criteria."
            )
            # Loop til næste forsøg

    else:
        # Hvis vi kommer hertil, er MAX_TRIES overskredet
        print("🚩 Maximum antal forsøg nået – bruger sidste fundne produkter.\n")
        final_products = filtered

    return final_products

def final_comparison_and_recommendation(products: list, criteria_summary: str):
    """
    Fase 3: Bed LLM’en om at sammenligne de 5 produkter og give en endelig anbefaling.
    Vi kan sende en prompt til GPT-3.5 eller Mistral via AssistantAgent.
    """
    # Byg prompt
    # Vi nævner hvert produkt som en kort bullet (navn, pris, butik, link) plus kriterierne.
    product_lines = []
    for i, p in enumerate(products, 1):
        price_str = p.get('price', '-')
        dkk_info = ""
        usd_val = None
        if isinstance(price_str, str) and price_str.startswith('$'):
            try:
                usd_val = float(price_str.replace('$', '').replace(',', ''))
                dkk_info = f" ({usd_to_dkk(usd_val)} DKK)"
            except:
                pass
        product_lines.append(f"{i}. {p.get('title')} – Price: {price_str}{dkk_info} – Store: {p.get('store')} – Link: {p.get('link')}")

    products_text = "\n".join(product_lines)

    comparison_prompt = (
        "Du er en venlig shopping-assistent. Sammenlign nu de fem produkter herunder, "
        "tag udgangspunkt i brugerens krav og vælg ét som din endelige anbefaling. "
        "Forklar kort hvorfor netop det produkt opfylder kravene bedst.\n\n"
        f"Brugerens krav:\n{criteria_summary}\n\n"
        f"Produkter:\n{products_text}\n\n"
        "Skriv dit svar på engelsk, i kortfattet regelsæt stil, og marker anbefalingen med 🏆 eller ✨.\n"
    )

    # Sæt AssistantAgent op med enten Mistral eller OpenAI
    assistant = AssistantAgent(
        name="FinalRecommender",
        llm_config=OPENAI_LLM_CONFIG  # eller MISTRAL_LLM_CONFIG, alt efter hvad du foretrækker
    )
    user_proxy = UserProxyAgent(
        name="User",
        human_input_mode="TERMINATE",
        code_execution_config={"use_docker": False}
    )

    # Ingen tools skal registreres her – LLM’en skal bare skrive tekst
    chat_result = user_proxy.initiate_chat(
        assistant,
        message=comparison_prompt,
        summary_method=None,
        max_turns=4
    )
    recommendation = chat_result.summary
    print("\n🏁 **Endelig sammenligning og anbefaling**:\n")
    print(recommendation)

def main():
    # 0) Hvilket produkt skal vi kigge efter?
    product_type = get_product_type()

    # 1) Fase 1: Indsaml bruger-krav gennem LLM
    criteria_summary = collect_user_criteria(product_type)

    # 2) Sørg for at budget nævnes som DKK i requirements, hvis ikke allerede:
    if "DKK" not in criteria_summary.upper():
        # Antager default budget 400 DKK, men du kan alternativt lade brugeren vælge via dialog
        user_budget_dkk = 400
        criteria_summary = criteria_summary.strip() + f"\n- Budget: omkring {user_budget_dkk} DKK\n"
    else:
        # Hvis budgettet blev opsamlet i dialog, skal vi parse det fra criteria_summary
        # For simpelt eksempel: find ”200-400 DKK” og tag maksimum. Her antager vi maks 400 DKK:
        user_budget_dkk = 400

    # Beregn max USD (rund op, så vi ikke overskrider budget DKK)
    budget_usd = math.ceil(user_budget_dkk / USD_TO_DKK_RATE)

    # 3) Fase 2: Looper product search + evaluering
    final_products = run_product_loop(criteria_summary, budget_usd, max_tries=3, min_score=4)

    # 4) Fase 3: Endelig sammenligning og anbefaling
    final_comparison_and_recommendation(final_products, criteria_summary)


if __name__ == "__main__":
    main()
