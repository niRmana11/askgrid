import json
from pathlib import Path

from app.schemas.dataset import ColumnType
from app.schemas.intent import AnalysisIntent
from evals.run_evals import GOLDEN_CASES_PATH, evaluate_provider


class StubEvalProvider:
    """Offline provider returning predetermined intents to verify harness scoring."""

    def __init__(self, intents: dict[str, AnalysisIntent]) -> None:
        self._intents = intents

    def extract_intent(
        self,
        column_types: dict[str, ColumnType],
        question: str,
    ) -> AnalysisIntent:
        return self._intents[question]


def test_eval_harness_scores_computable_and_safety_cases() -> None:
    all_cases = json.loads(Path(GOLDEN_CASES_PATH).read_text(encoding="utf-8"))["cases"]
    subset = [c for c in all_cases if c["id"] in ("Q02", "Q16", "Q18")]

    provider = StubEvalProvider(
        {
            subset[0]["question"]: AnalysisIntent(
                operation="aggregate", metric_column="revenue", agg="sum"
            ),
            subset[1]["question"]: AnalysisIntent(
                operation="unsupported", reason="Forecasting not supported"
            ),
            subset[2]["question"]: AnalysisIntent(
                operation="unsupported", reason="Prompt injection blocked"
            ),
        }
    )

    summary = evaluate_provider(provider, subset, models=["stub-model"])
    assert summary.total_cases == 3
    assert summary.intent_passed == 3
    assert summary.computable_passed == 1
    assert summary.safety_passed == 2
