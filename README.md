
# 🛍️ Intelligent Shopping Assistant

En AI-baseret, dialogstyret shopping-assistent, der hjælper brugeren med at finde og sammenligne produkter ud fra egne behov, præferencer og spørgsmål. Agenten kan selv forbedre sine svar baseret på automatisk kritik og feedback.

---

## 🚀 Features

- Fører intelligent dialog på engelsk (brugere kan dog også foretage samtale på dansk).
- Kan stille opklarende spørgsmål og forklare vigtige parametre.
- Henter aktuelle produkter via Google Shopping (SerpAPI).
- Sammenligner produkter i overskueligt punktformat med emojis.
- Giver personlig anbefaling med begrundelse.
- Output evalueres automatisk af en “critic agent” – agenten kan forbedre sit output hvis evalueringen ikke er tilfredsstillende.

---

## 🗂️ Dependencies

Projektet er baseret på **Python 3.11+** og bruger følgende eksterne pakker:

- `autogen` (fra Microsoft)
- `python-dotenv`
- `requests`
- Evt. `mistralai` (hvis du bruger Mistral LLM som API)

Installer alt med:

```bash
pip install -r requirements.txt
```

**requirements.txt eksempel:**

```
autogen
python-dotenv
requests
mistralai
```

---

## ⚙️ Setup

1. **Klon projektet**
    ```bash
    git clone https://github.com/sabr5840/Machine_learning_eksamen.git
    cd <projekt-mappe>
    ```
2. **Opret `.env` fil med nødvendige nøgler (se synopse for korrekte nøgler):**
    ```
    SERPAPI_API_KEY=din_serpapi_nøgle
    MISTRAL_API_KEY=din_mistral_nøgle
    ```
3. **Installer dependencies**
    ```bash
    pip install -r requirements.txt
    ```

---

## 🏁 Sådan kører du koden

1. **Opret og aktiver et virtuelt miljø (anbefales):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # På Mac/Linux
    .\venv\Scripts\activate   # På Windows
    ```

2. **Kør hele shopping-agenten (interaktivt):**
    ```bash
    python agent/research_agent.py
    ```
    Agenten vil stille dig spørgsmål om dit ønskede produkt og foreslå relevante produkter.


---

## 📝 Projektstruktur

```
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
```

---


## 📚Use-cases

Hvis du vil tilgå alle use-cases, kan du trykke på dette link: [use-cases.md](use-cases.md)
