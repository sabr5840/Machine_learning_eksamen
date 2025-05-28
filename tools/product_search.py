import os
import requests
from typing import List, Dict
from dotenv import load_dotenv
load_dotenv()

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

def search_products(query: str, max_results: int = 5) -> List[Dict]:
    """
    Search for products via SerpAPI's Google Shopping engine (US/international market).
    Returns a list of products with title, price, store, image, and link.
    """
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_shopping",
        "q": query,                    # Expect English product queries (e.g. "night cream for dry skin")
        "api_key": SERPAPI_API_KEY,
        "num": max_results
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            print("API error:", resp.status_code, resp.text)
            return []
        data = resp.json()
        results = []
        for p in data.get("shopping_results", [])[:max_results]:
            results.append({
                "title": p.get("title"),
                "price": p.get("price"),
                "store": p.get("source"),
                "link": p.get("link") or p.get("product_link") or None,
                "thumbnail": p.get("thumbnail"),
                "delivery": p.get("delivery_options", None),  # Not always available
            })
        return results
    except Exception as e:
        print("Exception during product search:", str(e))
        return []

# --------- Test code below ---------
if __name__ == "__main__":
    products = search_products("night cream for dry skin", max_results=5)
    for p in products:
        print(p)
