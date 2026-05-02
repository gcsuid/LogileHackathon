import queue
import socket
import threading
import warnings

from langchain_core._api.deprecation import LangChainDeprecationWarning
from langchain_community.llms import Ollama

_OLLAMA_AVAILABLE = None
_OLLAMA_DISABLED = False

warnings.filterwarnings(
    "ignore",
    category=LangChainDeprecationWarning,
)


def _is_ollama_available() -> bool:
    global _OLLAMA_AVAILABLE

    if _OLLAMA_AVAILABLE is not None:
        return _OLLAMA_AVAILABLE

    try:
        with socket.create_connection(("127.0.0.1", 11434), timeout=0.5):
            _OLLAMA_AVAILABLE = True
    except OSError:
        _OLLAMA_AVAILABLE = False

    return _OLLAMA_AVAILABLE


def run_llm(prompt: str) -> str:
    """Run a prompt against a local Ollama model."""
    global _OLLAMA_DISABLED

    if _OLLAMA_DISABLED:
        return "LLM unavailable. Using local fallback reasoning. Details: previous Ollama call failed."

    if not _is_ollama_available():
        return "LLM unavailable. Using local fallback reasoning. Details: Ollama server not running."

    try:
        llm = Ollama(model="llama3")
        result_queue: queue.Queue = queue.Queue()

        def _invoke() -> None:
            try:
                result_queue.put(("ok", llm.invoke(prompt).strip()))
            except Exception as exc:  # pragma: no cover
                result_queue.put(("error", str(exc)))

        worker = threading.Thread(target=_invoke, daemon=True)
        worker.start()

        try:
            status, payload = result_queue.get(timeout=1.5)
        except queue.Empty:
            _OLLAMA_DISABLED = True
            return "LLM unavailable. Using local fallback reasoning. Details: request timed out."

        if status == "ok":
            return payload
        _OLLAMA_DISABLED = True
        return f"LLM unavailable. Using local fallback reasoning. Details: {payload}"
    except Exception as exc:
        _OLLAMA_DISABLED = True
        return (
            "LLM unavailable. "
            f"Using local fallback reasoning. Details: {exc}"
        )
