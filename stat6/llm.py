import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STAT6_ROOT = Path(__file__).resolve().parent

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(STAT6_ROOT / ".env", override=False)

HF_TOKEN = os.getenv("HF_TOKEN", "").strip()
HF_MODEL = os.getenv("HF_MODEL", "mistralai/Mistral-7B-Instruct-v0.3").strip()
HF_TIMEOUT_SECONDS = float(os.getenv("HF_TIMEOUT_SECONDS", "20"))


def _sanitize_prompt(prompt: str) -> str:
    prompt = str(prompt).strip() or "No prompt content was provided."
    redacted = prompt.replace(HF_TOKEN, "[REDACTED]") if HF_TOKEN else prompt
    return redacted[:6000]


def _sanitize_response(response: str) -> str:
    replacements = {
        "\u20b9": "INR ",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2022": "-",
    }
    for source, target in replacements.items():
        response = response.replace(source, target)

    return response.encode("ascii", errors="ignore").decode("ascii").strip()


def call_hf_inference(prompt: str, max_new_tokens: int = 220) -> str:
    """Call the Hugging Face hosted inference endpoint. No local model is used."""
    if not HF_TOKEN or not HF_MODEL:
        return ""

    endpoint = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
    payload = {
        "inputs": _sanitize_prompt(prompt),
        "parameters": {
            "max_new_tokens": max_new_tokens,
            "temperature": 0.1,
            "return_full_text": False,
        },
        "options": {
            "wait_for_model": True,
        },
    }

    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=HF_TIMEOUT_SECONDS) as response:
            data: Any = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        return ""

    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict):
            return _sanitize_response(first.get("generated_text", ""))
    if isinstance(data, dict):
        return _sanitize_response(data.get("generated_text", ""))
    return ""
