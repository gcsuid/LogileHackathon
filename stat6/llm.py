import os
import socket
import warnings

from langchain_core._api.deprecation import LangChainDeprecationWarning
from langchain_community.llms import Ollama

warnings.filterwarnings(
    "ignore",
    category=LangChainDeprecationWarning,
)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b").strip()
_LLM = Ollama(
    model=OLLAMA_MODEL,
    base_url=OLLAMA_HOST,
    timeout=20,
    temperature=0,
    num_predict=80,
)


def _is_ollama_available() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", 11434), timeout=1):
            return True
    except OSError:
        return False


def run_llm(prompt: str) -> str:
    """Run a prompt against the local Ollama model with a simple fallback."""
    if not _is_ollama_available():
        return "LLM unavailable. Using local fallback reasoning. Details: Ollama server not running."

    try:
        response = _LLM.invoke(prompt)
        return response.strip() if isinstance(response, str) else str(response)
    except Exception as exc:
        return f"LLM unavailable. Using local fallback reasoning. Details: {exc}"
