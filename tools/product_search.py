# tools/product_search.py

import os # Finder .env filen
import time
import requests # Håndterer HTTP‐anmodninger (internet søgninger)
from typing import List, Dict # Hvilen type af data vi returnerer
from dotenv import load_dotenv # Håndterer miljøvariabler
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry # Håndterer retry‐strategi for HTTP‐anmodninger

# Load .env og hent API‐nøglen
load_dotenv()

# Hent SerpAPI nøglen fra miljøvariabler eller retuner fejl hvis ikke sat
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
if not SERPAPI_API_KEY:
    raise EnvironmentError("SERPAPI_API_KEY not set in environment. Check your .env file!")

# Konfigurer en session med retry‐strategi
session = requests.Session()

# Hvis der opstår en 429 (Too Many Requests) eller 5xx fejl, prøv igen med eksponentiel backoff
retry_strategy = Retry(
    total=3,                # maks 3 forsøg
    backoff_factor=1,       # 1s, 2s, 4s mellem forsøg
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"] # Kun GET‐anmodninger
)

# Tilføj retry‐strategi til sessionen
adapter = HTTPAdapter(max_retries=retry_strategy)

# Mount adapteren til både http og https for at håndtere alle slags anmodninger
session.mount("https://", adapter)
session.mount("http://", adapter)

# Funktion til at søge produkter via SerpAPI's Google Shopping engine 
# Timeout sat til 15s for at undgå for hurtige read timeouts.
def search_products(query: str, max_results: int = 5, timeout: int = 15) -> List[Dict]:
    
    # Url til SerpAPI Google Shopping søgning
    url = "https://serpapi.com/search"

    # Ekstra instillinger til forespørgslen
    params = {
        "engine": "google_shopping", # Vælg Google Shopping som søgemaskine
        "q": query, # Søgeord
        "api_key": SERPAPI_API_KEY, # Din SerpAPI nøgle
        "num": max_results # Maksimalt antal resultater at returnere (5 sat som standard)
    }

    try:
        resp = session.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()

        # Håndtér eventuelle API‐level fejlbeskeder
        if data.get("error"):
            print(f"API error: {data['error']}")
            return []

        # Hvis der ikke er resultater, returner en tom liste
        results = []

        # Hvis der er shopping_resultater, gennemgå dem og saml relevante data
        for p in data.get("shopping_results", [])[:max_results]:
               
                results.append({
                    "title": p.get("title"), # titlen på produktet
                    "price": p.get("price"), # prisen på produktet
                    "store": p.get("source"), 
                    "link": p.get("link") or p.get("product_link") or None,
                    "thumbnail": p.get("thumbnail"), # miniaturebillede af produktet 
                    "description": p.get("description", ""),  # Ofte kort produkttekst
                    "rating": p.get("rating", None), # Produktets rating, hvis tilgængelig
                    "reviews": p.get("reviews", None),
                    "attributes": p.get("attributes", None),  # Kan være liste af specs
                    "delivery": p.get("delivery_options", None),
                })
        return results

    # Håndter HTTP‐fejl som 404, 500 osv.
    except requests.exceptions.RequestException as e:
        print("Exception during product search:", str(e))
        return []
