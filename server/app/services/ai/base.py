from typing import Protocol

from app.schemas.dataset import ColumnType
from app.schemas.intent import AnalysisIntent


class AIProviderUnavailableError(RuntimeError):
    """Raised when all configured AI models fail, time out, or lack credentials."""


class AIProvider(Protocol):
    """Provider-agnostic interface for schema-only intent extraction."""

    def extract_intent(
        self,
        column_types: dict[str, ColumnType],
        question: str,
    ) -> AnalysisIntent:
        """Translate a question + dataset schema (NEVER raw rows) into an AnalysisIntent."""
        ...
