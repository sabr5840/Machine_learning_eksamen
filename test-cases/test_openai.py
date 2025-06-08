import os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "Sig hej! Dette er en test af OpenAI API-nøglen."}
        ]
    )
    print("✅ OpenAI-svar:", response.choices[0].message.content)
except Exception as e:
    print("❌ Fejl ved kald til OpenAI:", e)
