import json

with open("OAI_CONFIG.json", "r") as f:
    config = json.load(f)

my_api_key = config["api_key"]

import openai
from openai import OpenAI

client = OpenAI(api_key=my_api_key)

def conjecture_insight_betting(conj: str, model: str = "gpt-4"):
    prompt = (
        f"Consider the following inequality derived from NBA data. What insight does it give from a sports betting perspective?:\n\n"
        f"{conj}"
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=300
    )

    return response.choices[0].message.content.strip()

def conjecture_insight_coaching(conj: str, model: str = "gpt-4"):
    prompt = (
        f"Consider the following inequality derived from NBA data. What insight does it give from a basketball coaching perspective?:\n\n"
        f"{conj}"
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=300
    )

    return response.choices[0].message.content.strip()
