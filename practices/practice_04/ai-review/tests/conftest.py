import pytest
from fastapi.testclient import TestClient

from app.api import app, get_llm


class FakeLLM:
    """Records calls instead of talking to a real model."""

    def __init__(self, answer: str = "looks good") -> None:
        self.answer = answer
        self.calls: list[str] = []

    def review(self, diff: str) -> str:
        self.calls.append(diff)
        return self.answer


@pytest.fixture
def fake_llm():
    llm = FakeLLM()
    app.dependency_overrides[get_llm] = lambda: llm
    yield llm
    app.dependency_overrides.clear()


@pytest.fixture
def client(fake_llm):
    return TestClient(app)
