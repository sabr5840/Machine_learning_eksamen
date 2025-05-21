import os
import sys

from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from autogen import AssistantAgent, UserProxyAgent, register_function
from agent.agent_evaluation import evaluate_response
from config import LLM_CONFIG
from tools.product_search import search_products

def get_user_input():
    query = input("Hvilket produkt leder du efter? (fx 'TV', 'natcreme', 'laptop'):\n> ")
    return query

def format_products(products: list) -> str:
    # Fallback: Brug denne hvis du på et tidspunkt vil vise "rå" produktdata fra search_products
    if not products:
        return "Ingen produkter fundet."
    formatted = []
    for i, p in enumerate(products, 1):
        formatted.append(
            f"{i}. 📦 {p.get('title', 'Ukendt')}\n"
            f"   💰 Pris: {p.get('price', '-')}\n"
            f"   🏪 Butik: {p.get('store', '-')}\n"
            f"   🔗 Link: {p.get('link', '-')}\n"
        )
    return "\n".join(formatted)

def format_evaluation(evaluation: dict) -> str:
    if "error" in evaluation:
        return f"Fejl i evaluering: {evaluation['error']}"
    return (
        f"* Relevans: {evaluation['relevance']}\n"
        f"* Sammenligning: {evaluation.get('comparison', '-')}\n"
        f"* Forklaring: {evaluation.get('explanation', '-')}\n"
        f"* Detaljegrad: {evaluation['detail']}\n"
        f"* Robusthed: {evaluation['robustness']}\n\n"
        f"Feedback:\n{evaluation['feedback']}"
    )

def main():
    query = get_user_input()
    message_body = (
        f"Du er en venlig og kyndig shopping-assistent, der hjælper brugeren med at finde det bedste produkt – uanset hvor meget eller lidt brugeren selv ved om produktet."
        f"\nNår brugeren nævner et produkt (fx '{query}'), skal du først indlede en dialog med brugeren, hvor du:"
        "\n- Stiller uddybende spørgsmål for at forstå brugerens behov, erfaring og præferencer."
        "\n- Hvis brugeren virker usikker eller ikke selv nævner specifikke ønsker, skal du komme med eksempler på relevante spørgsmål og forklare kort, hvorfor de kan være vigtige at overveje."
        "\nEksempel (for TV): 'Skal det bruges mest til film, gaming eller sport? Hvor stort skal det være? Hvilket budget har du? Hvilke funktioner er vigtige for dig, fx smart-TV eller særlige apps? Størrelsen påvirker oplevelsen, og dit budget afgør hvilke funktioner du får.'"
        "\nEksempel (for natcreme): 'Er der ingredienser, du foretrækker, fx hyaluronsyre for fugt eller E-vitamin for hudbeskyttelse? Har du allergier, eller foretrækker du parfumefri? Ingredienser som hyaluronsyre binder fugt til huden, mens E-vitamin beskytter mod frie radikaler.'"
        "\nHvis brugeren mangler viden om produktkategorien, så forklar de vigtigste ting, man typisk bør overveje, på en letforståelig måde – også hvorfor det er vigtigt."
        "\nNår du har nok information, brug 'search_products'-værktøjet til at hente de mest relevante produkter, sammenlign dem ud fra brugerens kriterier, og giv en personlig anbefaling med en kort begrundelse."
        "\nNår du sammenligner produkterne, lav altid en punktliste – brug gerne emojis til at vise egenskaber og gøre listen let at læse."
        "\nFor hvert produkt skal du vise fx: 📦 Navn, 💰 Pris, 🏪 Butik, ⭐ Vigtige egenskaber. Marker din anbefaling tydeligt – fx med 🏆 eller ✨ og forklar dit valg i 2-3 korte linjer."
        "\nBrug korte, tydelige sætninger, og gør det nemt at sammenligne produkterne."
        "\nAfslut først, når brugeren er tilfreds. Stil gerne opklarende spørgsmål undervejs."
    )

    user_proxy = UserProxyAgent(
        name="User",
        human_input_mode="NEVER",  # Sæt evt. til "ALWAYS" for interaktiv test
        code_execution_config=False
    )

    assistant = AssistantAgent(
        name="ShoppingAssistant",
        llm_config=LLM_CONFIG
    )

    register_function(
        search_products,
        caller=assistant,
        executor=user_proxy,
        name="search_products",
        description="Søg efter produkter baseret på søgeord, og returner titel, pris, butik, link og evt. andre detaljer."
    )

    chat_result = user_proxy.initiate_chat(
        assistant,
        message=message_body,
        summary_method="last_msg",
        max_turns=8  # Giver agenten god tid til dialog!
    )

    agent_response = chat_result.summary

    print("\n🛍️ Agentens svar:\n")
    print(agent_response)

    # -- Evaluering --
    evaluation = evaluate_response(message_body, agent_response)
    print("\n🔍 Evaluering\n")
    print(format_evaluation(evaluation))

    # Hvis du en dag vil vise produkter i punktform direkte fra API'et:
    # products = search_products(query)
    # print(format_products(products))

if __name__ == "__main__":
    main()
