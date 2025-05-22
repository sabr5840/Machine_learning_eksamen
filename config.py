import os
from dotenv import load_dotenv

load_dotenv()

MISTRAL_LLM_CONFIG = {
    "config_list": [
        {
            "model": "mistral-large-latest",  #open-mistral-nemo
            "api_key": os.getenv("MISTRAL_API_KEY"),
            "api_type": "mistral",
            "temperature": 0.0,
            "stream": False,
            "tool_choice": "auto",
        }
    ]
}

OPENAI_LLM_CONFIG = {
    "config_list": [
        {
            "model": "gpt-3.5-turbo",
            "api_key": os.getenv("OPENAI_API_KEY"),
            # evt. flere openai-parametre
        }
    ]
}