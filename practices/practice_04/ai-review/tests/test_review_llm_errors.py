import httpx
import pytest

from app.api import app, get_llm
from app.llm import LLMTimeout, LLMUnavailable, OllamaLLM


class FailingLLM:
    def __init__(self, error: Exception) -> None:
        self.error = error

    def review(self, diff: str) -> str:
        raise self.error


@pytest.fixture
def failing_llm():
    def use(error: Exception) -> None:
        app.dependency_overrides[get_llm] = lambda: FailingLLM(error)

    yield use
    app.dependency_overrides.clear()


def test_llm_timeout_returns_504(client, failing_llm):
    failing_llm(LLMTimeout("read timed out after 30s at 127.0.0.1"))

    response = client.post("/review", json={"diff": "+x"})

    assert response.status_code == 504
    assert response.json() == {"detail": "LLM timeout"}


def test_llm_unavailable_returns_502(client, failing_llm):
    failing_llm(LLMUnavailable("connection refused 127.0.0.1:11434"))

    response = client.post("/review", json={"diff": "+x"})

    assert response.status_code == 502
    assert response.json() == {"detail": "LLM unavailable"}


def test_validation_still_runs_before_llm(client, failing_llm):
    failing_llm(LLMTimeout("must not be reached"))

    response = client.post("/review", json={"diff": "x" * 20_001})

    assert response.status_code == 413


def ollama_with(handler) -> OllamaLLM:
    return OllamaLLM(transport=httpx.MockTransport(handler))


def test_ollama_returns_model_answer():
    llm = ollama_with(lambda request: httpx.Response(200, json={"response": "ok"}))

    assert llm.review("+x") == "ok"


def test_ollama_timeout_becomes_llm_timeout():
    def handler(request):
        raise httpx.ReadTimeout("slow", request=request)

    with pytest.raises(LLMTimeout):
        ollama_with(handler).review("+x")


def test_ollama_connection_error_becomes_llm_unavailable():
    def handler(request):
        raise httpx.ConnectError("refused", request=request)

    with pytest.raises(LLMUnavailable):
        ollama_with(handler).review("+x")


def test_ollama_error_status_becomes_llm_unavailable():
    llm = ollama_with(lambda request: httpx.Response(404, json={"error": "model not found"}))

    with pytest.raises(LLMUnavailable):
        llm.review("+x")


def test_ollama_timeout_comes_from_env(monkeypatch):
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "2.5")
    seen = {}

    def handler(request):
        seen.update(request.extensions["timeout"])
        return httpx.Response(200, json={"response": "ok"})

    ollama_with(handler).review("+x")

    assert seen["read"] == 2.5


def test_ollama_timeout_defaults_to_30s(monkeypatch):
    monkeypatch.delenv("LLM_TIMEOUT_SECONDS", raising=False)
    seen = {}

    def handler(request):
        seen.update(request.extensions["timeout"])
        return httpx.Response(200, json={"response": "ok"})

    ollama_with(handler).review("+x")

    assert seen["read"] == 30.0
