import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


def check_openai():
    if not OPENAI_API_KEY:
        print("[OpenAI] No API key found in environment.")
        return
    url = "https://api.openai.com/v1/moderations"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    data = {"input": "ping"}
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=10)
        print(f"[OpenAI] Status: {resp.status_code}")
        print(f"[OpenAI] Response: {resp.json()}")
    except Exception as e:
        print(f"[OpenAI] Error: {e}")


def check_anthropic():
    if not ANTHROPIC_API_KEY:
        print("[Anthropic] No API key found in environment.")
        return
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    data = {
        "model": "claude-3-opus-20240229",
        "max_tokens": 1,
        "messages": [{"role": "user", "content": "ping"}],
    }
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=10)
        print(f"[Anthropic] Status: {resp.status_code}")
        print(f"[Anthropic] Response: {resp.json()}")
    except Exception as e:
        print(f"[Anthropic] Error: {e}")


if __name__ == "__main__":
    print("--- LLM Provider Health Check ---")
    check_openai()
    print()
    check_anthropic()
