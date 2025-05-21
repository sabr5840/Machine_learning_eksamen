
# 🛍️ Intelligent Shopping Assistant

En AI-baseret, dialogstyret shopping-assistent, der hjælper brugeren med at finde og sammenligne produkter ud fra egne behov, præferencer og spørgsmål. Agenten kan selv forbedre sine svar baseret på automatisk kritik og feedback.

---

## 🚀 **Features**
- Fører intelligent dialog på dansk (eller engelsk).
- Kan stille opklarende spørgsmål og forklare vigtige parametre.
- Henter aktuelle produkter via Google Shopping (SerpAPI).
- Sammenligner produkter i overskueligt punktformat med emojis.
- Giver personlig anbefaling med begrundelse.
- Output evalueres automatisk af en “critic agent” – agenten kan forbedre sit output hvis evalueringen ikke er tilfredsstillende.

🗂️ Dependencies

Projektet er baseret på Python 3.11+ og bruger følgende eksterne pakker:

autogen (fra Microsoft)
python-dotenv
requests
Evt. mistralai (hvis du bruger Mistral LLM som API)
Du installerer alt med:

pip install -r requirements.txt
requirements.txt eksempel:

autogen
python-dotenv
requests
mistralai

⚙️ Setup

Klon projektet
git clone <repo-url>
cd <projekt-mappe>
Opret .env fil med dine nøgler (læg denne i projektroden):
SERPAPI_API_KEY=din_serpapi_nøgle
MISTRAL_API_KEY=din_mistral_nøgle
Installer dependencies
pip install -r requirements.txt

🏁 Sådan kører du koden

Kør hele shopping-agenten (interaktivt):
python agent/research_agent.py
Agenten vil stille dig spørgsmål om dit ønskede produkt og foreslå relevante produkter.

Test produkt-søgning isoleret:
python tools/product_search.py
Denne fil tester kun API-opslag af produkter (kan bruges til fejlsøgning af API-nøgle).

Test evaluering og auto-feedback (med mock-data):
python test_eval.py
python test_eval_loop.py
Disse filer viser hvordan evaluering og forbedrings-loop fungerer – uden at bruge eksterne API-kald.

📝 Projektstruktur

agent/
    research_agent.py         # Hovedagenten (dialog og workflow)
    agent_evaluation.py       # Evaluering/"critic agent"
tools/
    product_search.py         # Produkt-søgning via SerpAPI
test_eval.py                 # Simpel evalueringstest (mock)
test_eval_loop.py            # Evaluering + feedback-loop (mock)
.env                         # Dine API-nøgler (IKKE til Git)
requirements.txt             # Dependencies
README.md                    # (denne fil)
use_cases.md                 # Brugsscenarier (eksempler)
💡 Tips og fejlfinding

API Rate Limits: Hvis du rammer grænser på Mistral eller SerpAPI, kan du teste med mock-data i test_eval.py og test_eval_loop.py.
Fejl i nøgler: Hvis produkt-søgning fejler, tjek at .env filen er korrekt sat op.
Ændr sproget: Du kan tilpasse alle prompts til dansk eller engelsk, som du ønsker.
Udvidelse: Koden kan let udvides med flere datakilder, flere evalueringskriterier, eller tilføjes et web-UI.










