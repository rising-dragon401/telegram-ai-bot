import os
import requests
import json
from dotenv import load_dotenv
load_dotenv()

PPLX_API_KEY = os.getenv('PPLX_API_KEY')

def get_pplx_response(role_prompt: str, question: str):
    url = "https://api.perplexity.ai/chat/completions"

    payload = {
        "model": "pplx-7b-online",
        "messages": [
            {
                "role": "system",
                "content": role_prompt
            },
            {
                "role": "user",
                "content": question
            }
        ]
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {PPLX_API_KEY}"
    }

    response = requests.post(url, json=payload, headers=headers)
    
    json_response = json.loads(response.text)
    message_content = json_response["choices"][0]["message"]["content"]

    return message_content

