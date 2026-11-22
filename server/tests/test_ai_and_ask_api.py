from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.routes.analysis import get_ai_provider
from app.api.routes.datasets import get_session_store
from app.main import app
from app.schemas.dataset import ColumnType
from app.schemas.intent import AnalysisIntent
from app.services.ai.base import AIProviderUnavailableError
from app.services.ai.gemini import ModelCircuitBreaker
from app.services.ai.prompts import build_schema_prompt
from app.services.session_store import EphemeralSessionStore


class FakeAIProvider:
    """Deterministic offline fake AI provider that captures what metadata it received."""

    def __init__(
        self,
        intent: AnalysisIntent | None = None,
        error: Exception | None = None,
    ) -> None:
        self._intent = intent
        self._error = error
        self.received_schemas: list[dict[str, ColumnType]] = []
        self.received_questions: list[str] = []

    def extract_intent(
        self,
        column_types: dict[str, ColumnType],
        question: str,
    ) -> AnalysisIntent:
        self.received_schemas.append(dict(column_types))
        self.received_questions.append(question)
        if self._error is not None:
            raise self._error
        assert self._intent is not None
        return self._intent


@pytest.fixture
def tmp_store(tmp_path: Path) -> Iterator[EphemeralSessionStore]:
    store = EphemeralSessionStore(base_dir=tmp_path, ttl_minutes=60)
    app.dependency_overrides[get_session_store] = lambda: store
    try:
        yield store
    finally:
        app.dependency_overrides.clear()


def test_ask_sends_schema_only_and_computes_golden_revenue(
    tmp_store: EphemeralSessionStore,
) -> None:
    fake_ai = FakeAIProvider(
        intent=AnalysisIntent(operation="aggregate", metric_column="revenue", agg="sum")
    )
    app.dependency_overrides[get_ai_provider] = lambda: fake_ai
    client = TestClient(app)

    session_id = client.post("/api/v1/datasets/sample").json()["session_id"]
    res = client.post(
        f"/api/v1/datasets/{session_id}/ask",
        json={"question": "What is total revenue?"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["data"]["value"] == 960190.0
    assert body["audit"]["operation"] == "aggregate"

    # Verify ZERO raw dataset row values were ever sent to the AI provider
    assert len(fake_ai.received_schemas) == 1
    prompt_text = build_schema_prompt(fake_ai.received_schemas[0], "What is total revenue?")
    assert "revenue" in prompt_text
    assert "Amaya Wickramasinghe" not in prompt_text
    assert "ORD-1001" not in prompt_text


def test_ask_converts_hallucinated_column_into_clarification(
    tmp_store: EphemeralSessionStore,
) -> None:
    fake_ai = FakeAIProvider(
        intent=AnalysisIntent(operation="aggregate", metric_column="profit", agg="sum")
    )
    app.dependency_overrides[get_ai_provider] = lambda: fake_ai
    client = TestClient(app)

    session_id = client.post("/api/v1/datasets/sample").json()["session_id"]
    res = client.post(
        f"/api/v1/datasets/{session_id}/ask",
        json={"question": "What is total profit?"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "clarification_needed"
    assert "does not exist" in body["explanation"]


def test_ask_returns_503_on_ai_outage_while_profile_still_works(
    tmp_store: EphemeralSessionStore,
) -> None:
    fake_ai = FakeAIProvider(error=AIProviderUnavailableError("All models busy"))
    app.dependency_overrides[get_ai_provider] = lambda: fake_ai
    client = TestClient(app)

    session_id = client.post("/api/v1/datasets/sample").json()["session_id"]
    ask_res = client.post(
        f"/api/v1/datasets/{session_id}/ask",
        json={"question": "Total revenue?"},
    )
    assert ask_res.status_code == 503

    # FR-016: Non-AI dataset endpoints keep working cleanly during AI outage
    profile_res = client.get(f"/api/v1/datasets/{session_id}")
    assert profile_res.status_code == 200
    assert profile_res.json()["profile"]["row_count"] == 24


def test_circuit_breaker_skips_tripped_model_until_cooldown() -> None:
    now = 1000.0
    breaker = ModelCircuitBreaker(cooldown_seconds=60, clock=lambda: now)

    assert breaker.is_open("gemini-3.8-flash") is False
    breaker.trip("gemini-3.8-flash")
    assert breaker.is_open("gemini-3.8-flash") is True

    now = 1059.0
    assert breaker.is_open("gemini-3.8-flash") is True

    now = 1061.0
    assert breaker.is_open("gemini-3.8-flash") is False


def test_feedback_endpoint_records_counts(tmp_store: EphemeralSessionStore) -> None:
    client = TestClient(app)
    res = client.post(
        "/api/v1/feedback",
        json={"session_id": "sample", "operation": "aggregate", "is_helpful": True},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["recorded"] is True
    assert body["total_helpful"] >= 1
