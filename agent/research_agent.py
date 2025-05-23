import os
import sys
from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from autogen import AssistantAgent, UserProxyAgent, register_function
from agent.agent_evaluation import evaluate_response
from config import MISTRAL_LLM_CONFIG, OPENAI_LLM_CONFIG
from tools.product_search import search_products

# Valutakonvertering – kan udvides til EUR m.m.
def usd_to_dkk(usd):
    try:
        return round(float(usd) * 7.0)  # Ret evt. kursen til aktuel (fx 7,0 for USD→DKK)
    except Exception:
        return None

def format_products(products: list) -> str:
    if not products:
        return "Ingen produkter fundet."
    formatted = []
    for i, p in enumerate(products, 1):
        pris = p.get('price', '-')
        dkk_info = ""
        if pris and isinstance(pris, str) and pris.strip().startswith('$'):
            usd = pris.strip().replace('$','').replace(',','')
            dkk = usd_to_dkk(usd)
            if dkk:
                dkk_info = f" (ca. {dkk} kr)"
        # Tilføj evt. flere valutatyper her (EUR, GBP etc.)
        formatted.append(
            f"{i}. 📦 {p.get('title', 'Ukendt')}\n"
            f"   💰 Pris: {pris}{dkk_info}\n"
            f"   🏪 Butik: {p.get('store', '-')}\n"
            f"   🔗 Link: {p.get('link', '-')}\n"
        )
    return "\n".join(formatted)

def format_evaluation(evaluation: dict) -> str:
    if "error" in evaluation:
        return f"Fejl i evaluering: {evaluation['error']}"
    return (
        f"* Relevans: {evaluation.get('relevance', '-')}\n"
        f"* Sammenligning: {evaluation.get('comparison', '-')}\n"
        f"* Forklaring: {evaluation.get('explanation', '-')}\n"
        f"* Detaljegrad: {evaluation.get('detail', '-')}\n"
        f"* Robusthed: {evaluation.get('robustness', '-')}\n"
        f"* Brugervenlighed: {evaluation.get('usability', '-')}\n"
        f"* Diversitet: {evaluation.get('diversity', '-')}\n"
        f"* Pris: {evaluation.get('price', '-')}\n\n"
        f"Feedback:\n{evaluation.get('feedback', '-')}"
    )

def get_product_type():
    query = input("Hvilket produkt leder du efter? (fx 'TV', 'natcreme', 'laptop'):\n> ").strip()
    return query

def collect_user_criteria(product_type):
    # Prompter agenten til at indsamle ALLE nødvendige svar fra brugeren (uden at søge produkter endnu).
    # Når agenten har nok, skal den udskrive alle ønsker i punktform og afslutte med teksten: KLAR TIL SØGNING
    system_prompt = (
        f"Du er en venlig, grundig og kyndig dansk shopping-assistent, der hjælper brugeren med at finde det bedst egnede produkt, "
        f"uanset om brugeren ved meget eller lidt om produktkategorien. \n"
        f"Når brugeren nævner et produkt (fx '{product_type}'), skal du først indlede en dialog med brugeren, hvor du:\n"
        f"- Stiller uddybende spørgsmål for at forstå brugerens behov, erfaring og præferencer – typisk om hudtype, finish, allergier, prisniveau, foretrukne mærker, eller andre relevante ønsker/krav for produktkategorien.\n"
        f"- Hvis brugeren ikke selv nævner specifikke ønsker, skal du give konkrete eksempler på spørgsmål, og forklare kort, hvorfor de kan være vigtige at overveje (fx 'For makeup: foretrækker du en mat eller glansfuld finish? Hvilken hudtype har du? Prisniveau?').\n"
        f"- Gør dialogen let og tryg for brugeren – forklar kort men pædagogisk hvorfor dine spørgsmål er relevante.\n"
        f"**VIGTIGT:** Når du har fået alle nødvendige svar fra brugeren, skal du skrive et punktvist sammendrag over alle ønsker og krav fra brugeren, så det er klart hvad der skal søges efter. "
        f"Afslut derefter dit svar med teksten: KLAR TIL SØGNING (i egen linje, gerne med store bogstaver). Du må ikke stille flere spørgsmål eller afvente mere brugerinput efter dette.\n"
        f"Du skal **ikke** gå videre til at foreslå produkter endnu. Kun dialog og opklaring i denne fase."
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
    register_function(
        search_products,
        caller=assistant,
        executor=user_proxy,
        name="search_products",
        description="Søg efter produkter baseret på søgeord, og returner titel, pris, butik, link og evt. andre detaljer."
    )

    # Chat indtil agenten svarer med "KLAR TIL SØGNING"
    criteria_summary = ""
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
        if "KLAR TIL SØGNING" in last_reply.upper():
            break
    else:
        print("Kunne ikke samle brugerens ønsker korrekt.")
    return criteria_summary

def run_shopping_search(criteria_summary, assistant_config):
    user_proxy = UserProxyAgent(
        name="User",
        human_input_mode="TERMINATE",   # INGEN brugerinput i search/output-fasen!
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
        description="Søg efter produkter baseret på søgeord, og returner titel, pris, butik, link og evt. andre detaljer."
    )
    shopping_prompt = (
        f"Her er brugerens ønsker og kriterier (sammendrag):\n"
        f"{criteria_summary}\n\n"
        f"Nu skal du:\n"
        f"- Søge efter og sammenligne relevante produkter, der matcher brugerens kriterier. "
        f"- Vis produkter fra både danske og internationale webshops. "
        f"- Hvis prisen er i USD ($) eller anden valuta, skal du omregne den til DKK og vise begge priser. "
        f"- Sammenlign altid ud fra DKK-prisen, især hvis brugeren har angivet et budget i kr. "
        f"- Vis mindst 3-5 produkter. For hvert produkt: 📦 Navn, 💰 Pris, 🏪 Butik, 🔗 Link. Brug punktliste og emojis. "
        f"- Marker tydeligt din anbefaling (fx med 🏆 eller ✨) og forklar kort, hvorfor du vælger netop det produkt ud fra brugerens kriterier. "
        f"- Afslut samtalen med anbefalingen, uden at vente på mere brugerinput."
    )
    chat_result = user_proxy.initiate_chat(
        assistant,
        message=shopping_prompt,
        summary_method="last_msg",
        max_turns=8
    )
    return chat_result.summary

def main():
    product_type = get_product_type()

    # FASE 1: Indsaml brugerens krav (ALWAYS-mode)
    try:
        criteria_summary = collect_user_criteria(product_type)
    except Exception as e:
        print("\nMistral fejlede under dialog – prøver OpenAI i stedet.\n", str(e))
        # Fallback til OpenAI
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
            description="Søg efter produkter baseret på søgeord, og returner titel, pris, butik, link og evt. andre detaljer."
        )
        criteria_summary = collect_user_criteria(product_type)

    # FASE 2: Automatisk søgning og evaluering uden brugerinput
    MAX_TRIES = 3
    min_acceptable_score = 4
    shopping_prompt_used = criteria_summary

    for attempt in range(MAX_TRIES):
        print(f"\n=== Produktsøgning og vurdering, forsøg {attempt + 1} ===\n")
        try:
            agent_response = run_shopping_search(shopping_prompt_used, MISTRAL_LLM_CONFIG)
        except Exception as e:
            print("\nMistral fejlede – forsøger med OpenAI i stedet!\n", str(e))
            agent_response = run_shopping_search(shopping_prompt_used, OPENAI_LLM_CONFIG)

        print(f"\n🛍️ Agentens produktforslag:\n{agent_response}")

        evaluation = evaluate_response(shopping_prompt_used, agent_response)
        print("\n🔍 Evaluering\n")
        print(format_evaluation(evaluation))

        low_scores = [v for k, v in evaluation.items()
                      if k in ['relevance', 'comparison', 'explanation', 'detail', 'robustness', 'usability', 'diversity', 'price']
                      and isinstance(v, int) and v < min_acceptable_score]
        if not low_scores:
            print("\n✅ Evaluering tilfredsstillende! Slut med anbefaling.")
            break

        print("\n⚠️ Output ikke tilfredsstillende. Prøver igen baseret på feedback...\n")
        # Forbedr prompten ud fra evalueringens feedback
        shopping_prompt_used = (
            f"{shopping_prompt_used}\n\nForrige kritik fra evaluering: {evaluation['feedback']}\nForbedr dine produktsøgninger og anbefalinger baseret på denne feedback."
        )
    else:
        print("\n🚩 Maks antal forsøg opbrugt – sidste svar blev brugt.")

if __name__ == "__main__":
    main()
