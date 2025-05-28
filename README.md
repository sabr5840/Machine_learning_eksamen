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
- `mistralai`

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

---

## 🧪 Testfiler – Oversigt og Formål

Projektet indeholder en række testfiler, som gør det nemt at verificere, at de vigtigste funktioner og integrationer virker som forventet. Herunder kan du læse, hvad de enkelte testfiler bruges til:

### `test_rate_limiter.py`

Tester at vores rate limiter fungerer korrekt og overholder grænser for hvor mange kald, der må ske til eksterne API’er indenfor et bestemt tidsinterval.  
**Eksempel:** Ved 3 kald per 5 sekunder vil filen vise, at de første tre kald sker med det samme, mens det fjerde kald venter, indtil vinduet er gået.

### `test_openai.py`

Sikrer, at forbindelsen til OpenAI API’et virker, og at vores API-nøgle er indlæst korrekt.  
Sender en simpel testbesked til GPT-3.5 og viser svaret i terminalen. Giver en fejlbesked, hvis der er problemer med nøglen eller netværket.

### `test_mock_output.py`

Tester formateringen af produktdata.  
Vi bruger en liste af fiktive (“mock”) produkter, som bliver sendt igennem funktionen `format_products`, så vi kan se, hvordan produkterne ville blive præsenteret for brugeren – helt uden at hente rigtige data udefra.

### `test_eval.py`

Tester evalueringen af et eksempel på et agentsvar.  
Funktionen `evaluate_response` vurderer, hvor godt et svar matcher brugerens prompt, og resultatet vises i en letlæselig form. Bruges til at sikre, at vores evalueringslogik fungerer som forventet.

### `test_eval_loop.py`

Simulerer et feedback-loop, hvor agenten får flere forsøg til at forbedre sine svar.  
Indeholder tre forskellige agentsvar af varierende kvalitet og evaluerer dem ét ad gangen. Hvis et svar ikke er godt nok, vises feedback, og der prøves igen.  
Dette efterligner en iterativ proces, hvor agenten lærer af feedback og forbedrer sine resultater.

#### Generelt

Disse testfiler gør det hurtigt at afprøve og validere enkelte dele af projektet, både ift. API-integration, databehandling og evaluering af agent-svar.  
Du kan køre dem direkte fra terminalen, f.eks.:
