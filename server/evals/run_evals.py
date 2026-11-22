import argparse
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.schemas.analysis import AnalysisResponse
from app.schemas.intent import AnalysisIntent
from app.services.ai.base import AIProvider, AIProviderUnavailableError
from app.services.ai.gemini import GeminiAIProvider
from app.services.ai.prompts import PROMPT_VERSION
from app.services.csv_parser import ParsedCSV, parse_csv_bytes
from app.services.engine import execute_intent
from app.services.intent_validator import IntentValidationError

SERVER_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = SERVER_ROOT / "tests" / "fixtures"
GOLDEN_CASES_PATH = Path(__file__).resolve().parent / "golden_cases.json"

SAFETY_CASE_IDS = frozenset({"Q16", "Q17", "Q18"})


@dataclass(frozen=True)
class CaseOutcome:
    case_id: str
    dataset: str
    expected_operation: str
    actual_operation: str
    intent_ok: bool
    e2e_ok: bool
    latency_ms: float
    detail: str


@dataclass(frozen=True)
class EvalSummary:
    prompt_version: str
    models: list[str]
    total_cases: int
    intent_passed: int
    computable_total: int
    computable_passed: int
    safety_total: int
    safety_passed: int
    p50_ms: float
    p95_ms: float
    outcomes: list[CaseOutcome]


def check_intent_match(expected_op: str, actual_op: str) -> bool:
    if expected_op == "clarification_or_missing_column":
        return actual_op in ("clarification_needed", "unsupported")
    return expected_op == actual_op


def check_e2e_result(case_id: str, response: AnalysisResponse) -> tuple[bool, str]:
    """Verify the deterministic Pandas output matches Python-verified golden truth."""
    data = response.data

    if case_id == "Q01":
        ok = data.get("rows") == 24 and data.get("columns") == 11
        return ok, f"rows={data.get('rows')}, cols={data.get('columns')}"
    if case_id == "Q02":
        return data.get("value") == 960190.0, f"value={data.get('value')}"
    if case_id == "Q03":
        return data.get("value") == 40007.92, f"value={data.get('value')}"
    if case_id == "Q04":
        return data.get("value") == 792135.0, f"value={data.get('value')}"
    if case_id == "Q05":
        chart_points = response.chart.points if response.chart else []
        by_cat = {p.label: (p.value, p.pct_of_total) for p in chart_points}
        ok = (
            by_cat.get("Electronics") == (460050.0, 47.91)
            and by_cat.get("Furniture") == (316950.0, 33.01)
            and by_cat.get("Accessories") == (183190.0, 19.08)
        )
        return ok, f"categories={by_cat}"
    if case_id == "Q06":
        chart_points = response.chart.points if response.chart else []
        top_items = [(p.label, p.value) for p in chart_points]
        expected = [
            ("27-inch Monitor", 251600.0),
            ("Standing Desk", 165750.0),
            ("Ergonomic Chair", 151200.0),
        ]
        return top_items == expected, f"top3={top_items}"
    if case_id == "Q07":
        chart_points = response.chart.points if response.chart else []
        top_items = [(p.label, p.value) for p in chart_points]
        expected = [
            ("Amaya Wickramasinghe", 267750.0),
            ("Kasun Perera", 139600.0),
            ("Sahan Gunasekara", 108375.0),
        ]
        return top_items == expected, f"top3_colombo={top_items}"
    if case_id == "Q08":
        ids = {str(r.get("order_id")) for r in response.rows}
        ok = data.get("row_count") == 2 and ids == {"ORD-1011", "ORD-1019"}
        return ok, f"row_count={data.get('row_count')}, ids={sorted(ids)}"
    if case_id == "Q09":
        expected_ts = {"2026-08": 234565.0, "2026-09": 321030.0, "2026-10": 404595.0}
        return data.get("series") == expected_ts, f"series={data.get('series')}"
    if case_id == "Q10":
        ok = (
            data.get("a") == 321030.0
            and data.get("b") == 404595.0
            and data.get("pct_change") == 26.03
        )
        return ok, f"a={data.get('a')}, b={data.get('b')}, pct={data.get('pct_change')}"
    if case_id == "Q11":
        ok = data.get("median") == 32150.0 and data.get("count") == 24
        return ok, f"median={data.get('median')}, count={data.get('count')}"
    if case_id == "Q12":
        return data.get("pearson_r") == 0.8812, f"r={data.get('pearson_r')}"
    if case_id == "Q13":
        ok = data.get("rows") == 13 and data.get("exact_duplicates") == 1
        return ok, f"rows={data.get('rows')}, dups={data.get('exact_duplicates')}"
    if case_id == "Q14":
        return data.get("value") == 180700.5, f"value={data.get('value')}"
    if case_id == "Q15":
        iqr = data.get("iqr_outliers")
        unit_cost_count = iqr.get("unit_cost", {}).get("count") if isinstance(iqr, dict) else None
        ok = (
            data.get("missing_by_col") == {"stock_qty": 1}
            and data.get("negative_counts") == {"stock_qty": 1}
            and unit_cost_count == 3
        )
        return ok, f"missing={data.get('missing_by_col')}, outliers={unit_cost_count}"
    if case_id in ("Q16", "Q18"):
        return response.status == "unsupported", f"status={response.status}"
    if case_id == "Q17":
        ok = response.status in ("clarification_needed", "unsupported")
        return ok, f"status={response.status}"
    return False, "Unknown case ID"


def evaluate_provider(
    provider: AIProvider,
    cases: list[dict[str, Any]],
    *,
    models: list[str],
    sleep_seconds: float = 0.0,
) -> EvalSummary:
    """Run all golden cases end-to-end against any AIProvider (live or mocked)."""
    parsed_cache: dict[str, ParsedCSV] = {}
    outcomes: list[CaseOutcome] = []

    for idx, case in enumerate(cases, start=1):
        dataset_name = str(case["dataset"])
        if dataset_name not in parsed_cache:
            parsed_cache[dataset_name] = parse_csv_bytes((FIXTURES_DIR / dataset_name).read_bytes())
        parsed = parsed_cache[dataset_name]
        case_id = str(case["id"])
        expected_op = str(case["expected_operation"])
        question = str(case["question"])

        t0 = time.perf_counter()
        try:
            intent: AnalysisIntent = provider.extract_intent(parsed.column_types, question)
        except AIProviderUnavailableError:
            latency_ms = round((time.perf_counter() - t0) * 1000, 1)
            outcomes.append(
                CaseOutcome(
                    case_id=case_id,
                    dataset=dataset_name,
                    expected_operation=expected_op,
                    actual_operation="api_unavailable",
                    intent_ok=False,
                    e2e_ok=False,
                    latency_ms=latency_ms,
                    detail="AI provider temporarily unavailable (503/rate-limit)",
                )
            )
            print(f"[ERR ] {case_id} ({latency_ms:6.1f} ms) | AI provider unavailable", flush=True)
            if sleep_seconds > 0 and idx < len(cases):
                time.sleep(sleep_seconds)
            continue
        try:
            response = execute_intent(parsed, intent)
        except IntentValidationError as exc:
            response = AnalysisResponse(
                status="clarification_needed",
                headline="Validation rejected intent",
                explanation=str(exc),
            )
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)
        intent_ok = check_intent_match(expected_op, intent.operation)
        e2e_ok, detail = check_e2e_result(case_id, response)
        outcomes.append(
            CaseOutcome(
                case_id=case_id,
                dataset=dataset_name,
                expected_operation=expected_op,
                actual_operation=intent.operation,
                intent_ok=intent_ok,
                e2e_ok=e2e_ok,
                latency_ms=latency_ms,
                detail=detail,
            )
        )
        tag = "PASS" if (intent_ok and e2e_ok) else "FAIL"
        print(
            f"[{tag}] {case_id} ({latency_ms:6.1f} ms) | "
            f"op={intent.operation:<20} | e2e={e2e_ok} | {detail}",
            flush=True,
        )

        if sleep_seconds > 0 and idx < len(cases):
            time.sleep(sleep_seconds)

    latencies = sorted(o.latency_ms for o in outcomes)
    p50 = latencies[len(latencies) // 2] if latencies else 0.0
    p95 = latencies[min(len(latencies) - 1, int(len(latencies) * 0.95))] if latencies else 0.0

    computable = [o for o in outcomes if o.case_id not in SAFETY_CASE_IDS]
    safety = [o for o in outcomes if o.case_id in SAFETY_CASE_IDS]
    return EvalSummary(
        prompt_version=PROMPT_VERSION,
        models=models,
        total_cases=len(outcomes),
        intent_passed=sum(1 for o in outcomes if o.intent_ok),
        computable_total=len(computable),
        computable_passed=sum(1 for o in computable if o.e2e_ok),
        safety_total=len(safety),
        safety_passed=sum(1 for o in safety if o.e2e_ok),
        p50_ms=p50,
        p95_ms=p95,
        outcomes=outcomes,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AskGrid End-to-End AI Evaluation Harness")
    parser.add_argument("--sleep", type=float, default=2.0, help="Seconds between live API calls")
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON report path")
    args = parser.parse_args()

    settings = get_settings()
    provider = GeminiAIProvider(
        api_key=settings.gemini_api_key,
        models=settings.gemini_model_list,
        timeout_seconds=settings.ai_timeout_seconds,
        cooldown_seconds=settings.ai_circuit_cooldown_seconds,
    )
    cases: list[dict[str, Any]] = json.loads(GOLDEN_CASES_PATH.read_text(encoding="utf-8"))["cases"]

    summary = evaluate_provider(
        provider,
        cases,
        models=settings.gemini_model_list,
        sleep_seconds=args.sleep,
    )

    print("\n=== ASKGRID END-TO-END AI EVAL SCORECARD ===")
    print(f"Prompt Version       : {summary.prompt_version}")
    print(f"Models               : {', '.join(summary.models)}")
    print(
        f"Intent Accuracy      : {summary.intent_passed}/{summary.total_cases} "
        f"({summary.intent_passed / summary.total_cases * 100:.1f}%)"
    )
    print(
        f"E2E Numerical Exact  : {summary.computable_passed}/{summary.computable_total} "
        f"({summary.computable_passed / summary.computable_total * 100:.1f}%)"
    )
    print(
        f"Safety & Refusals    : {summary.safety_passed}/{summary.safety_total} "
        f"({summary.safety_passed / summary.safety_total * 100:.1f}%)"
    )
    print(f"Latency p50 / p95    : {summary.p50_ms:.1f} ms / {summary.p95_ms:.1f} ms")

    if args.output is not None:
        args.output.write_text(json.dumps(asdict(summary), indent=2), encoding="utf-8")
        print(f"Saved JSON report to {args.output}")


if __name__ == "__main__":
    main()
