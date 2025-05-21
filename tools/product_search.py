import os
import requests
from typing import List, Dict
from dotenv import load_dotenv
load_dotenv()


SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")



def search_products(query: str, max_results: int = 5) -> List[Dict]:
    """
    Søg efter produkter via SerpAPI's Google Shopping-engine.
    Returnerer en liste af produkter med navn, pris, butik, billede og link.
    """
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_shopping",
        "q": query,
        "api_key": SERPAPI_API_KEY,
        "num": max_results
    }
    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        print("API-fejl:", resp.status_code, resp.text)
        return []
    data = resp.json()
    results = []
    for p in data.get("shopping_results", [])[:max_results]:
        results.append({
            "title": p.get("title"),
            "price": p.get("price"),
            "store": p.get("source"),
            "link": p.get("link"),
            "thumbnail": p.get("thumbnail"),
            "delivery": p.get("delivery_options", None),  # Ikke altid tilgængeligt
        })
    return results




# --------- Test-kode herunder ---------
if __name__ == "__main__":
    products = search_products("Macbook Pro", max_results=3)
    for p in products:
        print(p)