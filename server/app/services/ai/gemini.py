import time
from collections.abc import Callable

from google import genai
from google.genai import types

from app.schemas.dataset import ColumnType
from app.schemas.intent import AnalysisIntent
from app.services.ai.base import AIProviderUnavailableError
from app.services.ai.prompts import SYSTEM_PROMPT, build_schema_prompt


class ModelCircuitBreaker:
    """Skips recently failing models for a cooldown window to keep latency low."""

    def __init__(
        self,
        cooldown_seconds: int = 120,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._cooldown_seconds = cooldown_seconds
        self._clock = clock
        self._open_until: dict[str, float] = {}

    def is_open(self, model: str) -> bool:
        until = self._open_until.get(model)
        if until is None:
            return False
        if self._clock() >= until:
            del self._open_until[model]
            return False
        return True

    def trip(self, model: str) -> None:
        self._open_until[model] = self._clock() + self._cooldown_seconds

    def reset(self, model: str) -> None:
        self._open_until.pop(model, None)


class GeminiAIProvider:
    """Google Gemini adapter using native Pydantic v2 Structured Outputs."""

    def __init__(
        self,
        *,
        api_key: str,
        models: list[str],
        timeout_seconds: float = 15.0,
        cooldown_seconds: int = 120,
    ) -> None:
        self._api_key = api_key.strip()
        self._models = models
        self._timeout_ms = int(timeout_seconds * 1000)
        self._breaker = ModelCircuitBreaker(cooldown_seconds=cooldown_seconds)
        self._client: genai.Client | None = None

    def _get_client(self) -> genai.Client:
        if not self._api_key:
            raise AIProviderUnavailableError(
                "GEMINI_API_KEY is not configured. Non-AI profiling remains available."
            )
        if self._client is None:
            self._client = genai.Client(
                api_key=self._api_key,
                http_options=types.HttpOptions(timeout=self._timeout_ms),
            )
        return self._client

    def extract_intent(
        self,
        column_types: dict[str, ColumnType],
        question: str,
    ) -> AnalysisIntent:
        client = self._get_client()
        user_prompt = build_schema_prompt(column_types, question)
        last_error: Exception | None = None

        for model in self._models:
            if self._breaker.is_open(model):
                continue
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        response_schema=AnalysisIntent,
                        temperature=0.0,
                    ),
                )
                self._breaker.reset(model)
                return AnalysisIntent.model_validate_json(response.text or "{}")
            except Exception as exc:
                self._breaker.trip(model)
                last_error = exc

        raise AIProviderUnavailableError(
            "AI service is temporarily unavailable. Dataset preview and profiling still work."
        ) from last_error
