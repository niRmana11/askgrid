import asyncio
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.routes.datasets import get_session_store
from app.core.config import Settings, get_settings
from app.schemas.analysis import (
    AnalysisResponse,
    AskRequest,
    FeedbackRequest,
    FeedbackResponse,
)
from app.services.ai.base import AIProvider, AIProviderUnavailableError
from app.services.ai.gemini import GeminiAIProvider
from app.services.csv_parser import CSVParseError, parse_csv_bytes
from app.services.engine import execute_intent
from app.services.intent_validator import IntentValidationError
from app.services.session_store import EphemeralSessionStore, SessionNotFoundError

router = APIRouter(tags=["analysis"])

_feedback_counts: dict[str, int] = {"helpful": 0, "unhelpful": 0}
_analysis_semaphore: asyncio.Semaphore | None = None


def _get_semaphore(limit: int) -> asyncio.Semaphore:
    global _analysis_semaphore
    if _analysis_semaphore is None:
        _analysis_semaphore = asyncio.Semaphore(limit)
    return _analysis_semaphore


@lru_cache
def _cached_gemini_provider(
    api_key: str,
    models_csv: str,
    timeout_seconds: float,
    cooldown_seconds: int,
) -> GeminiAIProvider:
    models = [m.strip() for m in models_csv.split(",") if m.strip()]
    return GeminiAIProvider(
        api_key=api_key,
        models=models,
        timeout_seconds=timeout_seconds,
        cooldown_seconds=cooldown_seconds,
    )


def get_ai_provider(settings: Annotated[Settings, Depends(get_settings)]) -> AIProvider:
    """Provide a cached AIProvider so Circuit Breaker state persists across requests."""
    return _cached_gemini_provider(
        settings.gemini_api_key,
        settings.gemini_models,
        settings.ai_timeout_seconds,
        settings.ai_circuit_cooldown_seconds,
    )


@router.post("/datasets/{session_id}/ask", response_model=AnalysisResponse)
async def ask_dataset(
    session_id: str,
    payload: AskRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    store: Annotated[EphemeralSessionStore, Depends(get_session_store)],
    ai_provider: Annotated[AIProvider, Depends(get_ai_provider)],
) -> AnalysisResponse:
    try:
        raw_bytes = store.get_csv_bytes(session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    semaphore = _get_semaphore(settings.max_concurrent_analyses)
    async with semaphore:
        try:
            parsed = parse_csv_bytes(
                raw_bytes,
                max_size_mb=settings.max_upload_size_mb,
                max_rows=settings.max_rows,
                max_columns=settings.max_columns,
            )
        except CSVParseError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        try:
            # Run blocking SDK call in a worker thread so FastAPI's event loop stays responsive
            intent = await asyncio.to_thread(
                ai_provider.extract_intent,
                parsed.column_types,
                payload.question,
            )
        except AIProviderUnavailableError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc

        try:
            return execute_intent(parsed, intent)
        except IntentValidationError as exc:
            return AnalysisResponse(
                status="clarification_needed",
                headline="Could not run that query against your dataset columns.",
                explanation=str(exc),
                suggested_alternative=(
                    "Check the column names in your dataset profile and try rephrasing."
                ),
            )


@router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(payload: FeedbackRequest) -> FeedbackResponse:
    """Record aggregate answer quality ratings without storing PII or raw rows."""
    key = "helpful" if payload.is_helpful else "unhelpful"
    _feedback_counts[key] += 1
    return FeedbackResponse(
        recorded=True,
        total_helpful=_feedback_counts["helpful"],
        total_unhelpful=_feedback_counts["unhelpful"],
    )
