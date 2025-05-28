import os
import sys
from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from autogen import AssistantAgent, UserProxyAgent, register_function
from agent.agent_evaluation import evaluate_response
from config import MISTRAL_LLM_CONFIG, OPENAI_LLM_CONFIG
from tools.product_search import search_products

def usd_to_dkk(usd):
    try:
        return round(float(usd) * 7.0)  # Adjust as needed for live rates
    except Exception:
        return None

def format_products(products: list) -> str:
    if not products:
        return "No products found."
    # Sort products by USD price (lowest first)
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
            if dkk:
                dkk_info = f" ({dkk} DKK)"
        formatted.append(
            f"{i}. 📦 {p.get('title', 'Unknown')}\n"
            f"   💰 Price: {price_str}{dkk_info}\n"
            f"   🏪 Store: {p.get('store', '-')}\n"
            f"   🔗 Link: {p.get('link', '-') or 'Not available'}\n"
        )
    return "\n".join(formatted)

def format_evaluation(evaluation: dict) -> str:
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
    query = input("What product are you looking for? (e.g. 'night cream', 'laptop', 'TV'):\n> ").strip()
    return query

def collect_user_criteria(product_type):
    # Agent prompt, always in English
    system_prompt = (
        f"You are a friendly, thorough, and knowledgeable English-speaking shopping assistant who helps the user find the best product, "
        f"even if the user responds in Danish. If the user replies in Danish, answer in English but take their answers into account.\n"
        f"When the user mentions a product (e.g. '{product_type}'), you must first start a dialog with the user where you:\n"
        f"- Ask clarifying questions to understand their needs, experience, and preferences – such as skin type, finish, allergies, budget, favorite brands, or other relevant wishes/requirements for the product category.\n"
        f"- If the user does not mention specific wishes, give concrete example questions and briefly explain why they matter (e.g. 'For skincare: do you prefer fragrance free? What is your skin type? Budget?').\n"
        f"- Make the dialog easy and comfortable for the user – explain pedagogically why your questions matter.\n"
        f"**IMPORTANT:** When you have all needed answers, summarize all wishes and requirements as bullet points, so it's clear what to search for. "
        f"Then end your reply with: READY FOR SEARCH (in its own line, all caps). Do NOT ask more questions or await more user input after this.\n"
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
        print("\n---\n", last_reply, "\n---\n")
        criteria_summary += last_reply + "\n"
        if "READY FOR SEARCH" in last_reply.upper():
            break
    else:
        print("Could not collect user's requirements correctly.")
    return criteria_summary

def run_shopping_search(criteria_summary, assistant_config):
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
    shopping_prompt = (
        f"Here are the user's wishes and requirements (summary):\n"
        f"{criteria_summary}\n\n"
        f"Now you must:\n"
        f"- Search for and compare relevant products matching the user's criteria. "
        f"- Show products from US/international webshops only (no Danish shops). "
        f"- If the price is in USD ($), convert it to DKK and show both. "
        f"- Always compare using the DKK price, especially if the user stated a budget in DKK. "
        f"- Show at least 3-5 products. For each product: 📦 Name, 💰 Price, 🏪 Store, 🔗 Link. List format and emojis.\n"
        f"- Sort products from lowest to highest price. Do not remove duplicates.\n"
        f"- Clearly mark your recommendation (e.g. with 🏆 or ✨) and explain briefly why you chose it based on the user's criteria.\n"
        f"- End the conversation with your recommendation, without waiting for more user input."
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

    # PHASE 1: Collect user requirements (ALWAYS-mode)
    try:
        criteria_summary = collect_user_criteria(product_type)
    except Exception as e:
        print("\nMistral failed during dialog – trying OpenAI instead.\n", str(e))
        # Fallback to OpenAI
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

    # PHASE 2: Automatic search and evaluation without user input
    MAX_TRIES = 3
    min_acceptable_score = 4
    shopping_prompt_used = criteria_summary

    for attempt in range(MAX_TRIES):
        print(f"\n=== Product search and evaluation, attempt {attempt + 1} ===\n")
        try:
            agent_response = run_shopping_search(shopping_prompt_used, MISTRAL_LLM_CONFIG)
        except Exception as e:
            print("\nMistral failed – trying OpenAI instead!\n", str(e))
            agent_response = run_shopping_search(shopping_prompt_used, OPENAI_LLM_CONFIG)

        print(f"\n🛍️ Agent's product suggestions:\n{agent_response}")

        evaluation = evaluate_response(shopping_prompt_used, agent_response)
        print("\n🔍 Evaluation\n")
        print(format_evaluation(evaluation))

        low_scores = [v for k, v in evaluation.items()
                      if k in ['relevance', 'comparison', 'explanation', 'detail', 'robustness', 'usability', 'diversity', 'price']
                      and isinstance(v, int) and v < min_acceptable_score]
        if not low_scores:
            print("\n✅ Evaluation satisfactory! Ending with recommendation.")
            break

        print("\n⚠️ Output not satisfactory. Trying again based on evaluation feedback...\n")
        # Update prompt using evaluation feedback but keep user criteria
        shopping_prompt_used = (
            f"{criteria_summary}\n\nPrevious evaluation feedback: {evaluation['feedback']}\n"
            f"Improve your product search and recommendations based on this feedback. Do NOT change the user's original criteria."
        )
    else:
        print("\n🚩 Maximum number of attempts reached – using last answer.")

if __name__ == "__main__":
    main()
