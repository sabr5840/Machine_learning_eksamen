# tools/product_search.py

import os
import time
import requests
from typing import List, Dict
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load .env og hent API‐nøglen
load_dotenv()
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
if not SERPAPI_API_KEY:
    raise EnvironmentError("SERPAPI_API_KEY not set in environment. Check your .env file!")

# Konfigurer en session med retry‐strategi
session = requests.Session()
retry_strategy = Retry(
    total=3,                # maks 3 forsøg
    backoff_factor=1,       # 1s, 2s, 4s mellem forsøg
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)

def search_products(query: str, max_results: int = 5, timeout: int = 15) -> List[Dict]:
    """
    Søger produkter via SerpAPI's Google Shopping engine.
    - Retrier ved 429/5xx op til 3 gange med eksponentiel backoff.
    - Timeout sat til 15s for at undgå for hurtige read timeouts.
    """
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_shopping",
        "q": query,
        "api_key": SERPAPI_API_KEY,
        "num": max_results
    }

    try:
        resp = session.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()

        # Håndtér eventuelle API‐level fejlbeskeder
        if data.get("error"):
            print(f"API error: {data['error']}")
            return []

        results = []
        for p in data.get("shopping_results", [])[:max_results]:
            results.append({
                "title": p.get("title"),
                "price": p.get("price"),
                "store": p.get("source"),
                "link": p.get("link") or p.get("product_link") or None,
                "thumbnail": p.get("thumbnail"),
                "delivery": p.get("delivery_options", None),
            })
        return results

    except requests.exceptions.RequestException as e:
        print("Exception during product search:", str(e))
        return []
