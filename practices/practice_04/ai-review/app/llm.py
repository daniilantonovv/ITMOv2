"""LLM clients. The API depends only on the ReviewLLM protocol."""

import os
from typing import Protocol

import httpx

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "itmo-agent"
DEFAULT_TIMEOUT_SECONDS = 30.0


def llm_timeout_seconds() -> float:
    return float(os.environ.get("LLM_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS))


class LLMError(Exception):
    """Base error of an LLM client."""


class LLMTimeout(LLMError):
    """The LLM did not answer in time."""


class LLMUnavailable(LLMError):
    """The LLM could not be reached or returned an error."""


class ReviewLLM(Protocol):
    def review(self, diff: str) -> str: ...


class OllamaLLM:
    """Real client for the local Ollama model."""

    def __init__(
        self,
        url: str = OLLAMA_URL,
        model: str = OLLAMA_MODEL,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.url = url
        self.model = model
        self.transport = transport

    def review(self, diff: str) -> str:
        prompt = f"Review this diff. List concrete problems, one per line.\n\n{diff}"
        try:
            with httpx.Client(transport=self.transport, timeout=llm_timeout_seconds()) as client:
                response = client.post(
                    self.url,
                    json={"model": self.model, "prompt": prompt, "stream": False},
                )
                response.raise_for_status()
        except httpx.TimeoutException as error:
            raise LLMTimeout(str(error)) from error
        except httpx.HTTPError as error:
            raise LLMUnavailable(str(error)) from error
        return response.json()["response"]
