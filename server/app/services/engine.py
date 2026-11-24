import math
import time
from typing import Any

import numpy as np
import pandas as pd

from app.schemas.analysis import AnalysisResponse, CalculationAudit, ChartPoint, ChartSpec
from app.schemas.dataset import ColumnType, JsonScalar
from app.schemas.intent import AggFunc, AnalysisIntent, FilterClause
from app.services.csv_parser import ParsedCSV
from app.services.engine_advanced import (
    run_compare,
    run_correlation,
    run_distribution,
    run_quality_report,
    run_time_series,
)
from app.services.formatting import human_agg, human_col
from app.services.intent_validator import IntentValidationError, validate_intent


def _to_json_scalar(value: object) -> JsonScalar:
    """Convert Pandas/NumPy scalars into strictly JSON-serializable values."""
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        float_val = float(value)
        if math.isnan(float_val) or math.isinf(float_val):
            return None
        return round(float_val, 4)
    return str(value)


def _apply_filters(
    df: pd.DataFrame,
    column_types: dict[str, ColumnType],
    filters: list[FilterClause],
) -> tuple[pd.DataFrame, list[str]]:
    """Apply universal filter clauses deterministically and record readable descriptions."""
    filtered = df
    applied: list[str] = []

    for clause in filters:
        col = clause.column
        col_type = column_types.get(col, "string")
        series = filtered[col]

        if col_type in ("integer", "float"):
            try:
                target_num = float(clause.value)
            except ValueError as exc:
                raise IntentValidationError(
                    f"Filter value '{clause.value}' is not a valid number for column '{col}'."
                ) from exc
            if clause.op == "eq":
                mask = series == target_num
            elif clause.op == "neq":
                mask = series != target_num
            elif clause.op == "gt":
                mask = series > target_num
            elif clause.op == "gte":
                mask = series >= target_num
            elif clause.op == "lt":
                mask = series < target_num
            elif clause.op == "lte":
                mask = series <= target_num
            else:
                raise IntentValidationError(f"Unsupported numeric filter operator '{clause.op}'.")
        elif col_type == "date":
            try:
                target_dt = pd.to_datetime(clause.value)
            except ValueError as exc:
                raise IntentValidationError(
                    f"Filter value '{clause.value}' is not a valid date for column '{col}'."
                ) from exc
            if clause.op == "eq":
                mask = series == target_dt
            elif clause.op == "neq":
                mask = series != target_dt
            elif clause.op == "gt":
                mask = series > target_dt
            elif clause.op == "gte":
                mask = series >= target_dt
            elif clause.op == "lt":
                mask = series < target_dt
            elif clause.op == "lte":
                mask = series <= target_dt
            else:
                raise IntentValidationError(f"Unsupported date filter operator '{clause.op}'.")
        else:
            normalized = series.astype("string").str.strip().str.lower()
            target_str = clause.value.strip().lower()
            if clause.op == "eq":
                mask = normalized == target_str
            elif clause.op == "neq":
                mask = normalized != target_str
            elif clause.op == "contains":
                # regex=False prevents ReDoS attacks from untrusted filter text
                mask = normalized.str.contains(target_str, regex=False, na=False)
            else:
                raise IntentValidationError(f"Unsupported text filter operator '{clause.op}'.")

        filtered = filtered[mask.fillna(False)]
        applied.append(f"{col} {clause.op} '{clause.value}'")

    return filtered, applied


def _compute_agg(df: pd.DataFrame, col: str | None, agg: AggFunc) -> tuple[float, int]:
    """Compute a single deterministic aggregate and count excluded nulls."""
    if agg == "count" and col is None:
        return float(len(df)), 0
    assert col is not None
    series = df[col]
    nulls_excluded = int(series.isna().sum())
    clean = series.dropna()
    if clean.empty:
        return 0.0, nulls_excluded

    if agg == "sum":
        result = float(clean.sum())
    elif agg == "mean":
        result = float(clean.mean())
    elif agg == "median":
        result = float(clean.median())
    elif agg == "min":
        result = float(clean.min())
    elif agg == "max":
        result = float(clean.max())
    elif agg == "count":
        result = float(clean.count())
    elif agg == "count_distinct":
        result = float(clean.nunique())
    elif agg == "std":
        std_val = float(clean.std())
        result = 0.0 if math.isnan(std_val) else std_val
    else:
        raise IntentValidationError(f"Unsupported aggregation '{agg}'.")

    return round(result, 2), nulls_excluded


def _compute_grouped_agg(
    df: pd.DataFrame,
    group_col: str,
    metric_col: str | None,
    agg: AggFunc,
) -> list[tuple[str, float]]:
    """Run deterministic groupby aggregation and return (group_label, rounded_value) pairs."""
    grouped: pd.Series[Any]
    if agg == "count" and metric_col is None:
        grouped = df.groupby(group_col).size()
    else:
        assert metric_col is not None
        gb = df.groupby(group_col)[metric_col]
        if agg == "sum":
            grouped = gb.sum()
        elif agg == "mean":
            grouped = gb.mean()
        elif agg == "median":
            grouped = gb.median()
        elif agg == "min":
            grouped = gb.min()
        elif agg == "max":
            grouped = gb.max()
        elif agg == "count":
            grouped = gb.count()
        elif agg == "count_distinct":
            grouped = gb.nunique()
        elif agg == "std":
            grouped = gb.std().fillna(0.0)
        else:
            raise IntentValidationError(f"Unsupported grouped aggregation '{agg}'.")

    results: list[tuple[str, float]] = []
    for key, val in grouped.items():
        fval = float(val)
        if not math.isnan(fval):
            results.append((str(key), round(fval, 2)))
    return results


def execute_intent(parsed: ParsedCSV, raw_intent: AnalysisIntent) -> AnalysisResponse:
    """Validate and deterministically execute an AnalysisIntent on a ParsedCSV."""
    t0 = time.perf_counter()
    intent = validate_intent(raw_intent, parsed.column_types)
    op = intent.operation

    if op in ("unsupported", "clarification_needed"):
        return AnalysisResponse(
            status=op,
            headline=intent.reason or "This question cannot be answered directly from the dataset.",
            explanation=intent.reason
            or "Try rephrasing with exact column names or one of the 10 supported operations.",
            suggested_alternative=intent.suggested_alternative,
        )

    df = parsed.df
    rows_scanned = len(df)
    filtered, filters_applied = _apply_filters(df, parsed.column_types, intent.filters)
    rows_matched = len(filtered)

    if op == "describe_dataset":
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        cols = list(parsed.column_types.keys())
        return AnalysisResponse(
            status="ok",
            headline=f"Dataset has {rows_scanned:,} rows and {len(cols)} columns.",
            explanation=f"Columns: {', '.join(cols)}",
            data={
                "rows": rows_scanned,
                "columns": len(cols),
                "column_types": dict(parsed.column_types),
            },
            audit=CalculationAudit(
                operation=op,
                columns_used=cols,
                rows_scanned=rows_scanned,
                rows_matched=rows_scanned,
                date_format_used=parsed.date_format_note,
                execution_ms=elapsed_ms,
            ),
        )

    if op == "aggregate":
        agg: AggFunc = intent.agg or "count"
        value, nulls_excluded = _compute_agg(filtered, intent.metric_column, agg)
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        col_label = intent.metric_column or "rows"
        readable_col = human_col(intent.metric_column)
        readable_agg = human_agg(agg)
        return AnalysisResponse(
            status="ok",
            headline=f"{readable_agg.capitalize()} {readable_col}: {value:,.2f}",
            explanation=(
                f"Calculated {readable_agg} {readable_col} "
                f"across {rows_matched:,} matching rows"
                + (f" ({nulls_excluded} missing values skipped)." if nulls_excluded else ".")
            ),
            data={"value": value, "agg": agg, "column": col_label},
            chart=ChartSpec(
                chart_type="kpi",
                title=f"{readable_agg.capitalize()} {readable_col}",
                points=[ChartPoint(label=col_label, value=value)],
            ),
            audit=CalculationAudit(
                operation=op,
                columns_used=[c for c in [intent.metric_column] if c],
                filters_applied=filters_applied,
                rows_scanned=rows_scanned,
                rows_matched=rows_matched,
                nulls_excluded=nulls_excluded,
                date_format_used=parsed.date_format_note,
                execution_ms=elapsed_ms,
            ),
        )

    if op in ("group_aggregate", "top_n"):
        assert intent.group_by is not None
        agg = intent.agg or "sum"
        pairs = _compute_grouped_agg(filtered, intent.group_by, intent.metric_column, agg)
        reverse = (intent.direction or "desc") == "desc"
        pairs.sort(key=lambda item: item[1], reverse=reverse)

        grand_total = sum(v for _, v in pairs) if agg in ("sum", "count") else 0.0
        if op == "top_n":
            limit = intent.n or 5
            pairs = pairs[:limit]

        points = [
            ChartPoint(
                label=label,
                value=val,
                pct_of_total=round(val / grand_total * 100, 2) if grand_total > 0 else None,
            )
            for label, val in pairs
        ]
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        metric_label = intent.metric_column or "rows"
        readable_metric = human_col(intent.metric_column)
        readable_group = human_col(intent.group_by)
        readable_agg = human_agg(agg)
        rank_word = "Lowest" if intent.direction == "asc" else "Highest"
        top_preview = (
            f"{points[0].label} ({points[0].value:,.2f})" if points else "No matching rows"
        )
        return AnalysisResponse(
            status="ok",
            headline=f"{rank_word} by {readable_agg} {readable_metric}: {top_preview}",
            explanation=f"Grouped {rows_matched:,} matching rows by {readable_group}.",
            data={
                "group_by": intent.group_by,
                "metric": metric_label,
                "agg": agg,
                "groups": [
                    {"label": p.label, "value": p.value, "pct_of_total": p.pct_of_total}
                    for p in points
                ],
            },
            chart=ChartSpec(
                chart_type="horizontal_bar" if op == "top_n" else "bar",
                title=f"{readable_agg.capitalize()} {readable_metric} by {readable_group}",
                x_label=intent.group_by,
                y_label=metric_label,
                points=points,
            ),
            audit=CalculationAudit(
                operation=op,
                columns_used=[c for c in [intent.group_by, intent.metric_column] if c],
                filters_applied=filters_applied,
                rows_scanned=rows_scanned,
                rows_matched=rows_matched,
                date_format_used=parsed.date_format_note,
                execution_ms=elapsed_ms,
            ),
        )

    if op == "filter_rows":
        result_df = filtered
        if intent.sort_by:
            ascending = (intent.direction or "desc") == "asc"
            result_df = result_df.sort_values(by=intent.sort_by, ascending=ascending)
        limit = intent.n or 25
        capped = result_df.head(limit)
        rows: list[dict[str, JsonScalar]] = [
            {str(col): _to_json_scalar(row[col]) for col in capped.columns}
            for _, row in capped.iterrows()
        ]
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        return AnalysisResponse(
            status="ok",
            headline=f"Found {rows_matched:,} matching rows (showing {len(rows)}).",
            explanation=f"Filtered dataset using {', '.join(filters_applied) or 'no filters'}.",
            data={"row_count": rows_matched, "returned_count": len(rows)},
            rows=rows,
            chart=ChartSpec(chart_type="table", title="Matching Rows"),
            audit=CalculationAudit(
                operation=op,
                columns_used=list(parsed.column_types.keys()),
                filters_applied=filters_applied,
                rows_scanned=rows_scanned,
                rows_matched=rows_matched,
                date_format_used=parsed.date_format_note,
                execution_ms=elapsed_ms,
            ),
        )

    if op == "time_series":
        return run_time_series(
            parsed,
            filtered,
            intent,
            filters_applied=filters_applied,
            rows_scanned=rows_scanned,
            t0=t0,
            grouped_agg_fn=_compute_grouped_agg,
        )

    if op == "compare":
        return run_compare(
            parsed,
            filtered,
            intent,
            filters_applied=filters_applied,
            rows_scanned=rows_scanned,
            t0=t0,
            agg_fn=_compute_agg,
        )

    if op == "distribution":
        return run_distribution(
            parsed,
            filtered,
            intent,
            filters_applied=filters_applied,
            rows_scanned=rows_scanned,
            t0=t0,
        )

    if op == "correlation":
        return run_correlation(
            parsed,
            filtered,
            intent,
            filters_applied=filters_applied,
            rows_scanned=rows_scanned,
            t0=t0,
        )

    if op == "quality_report":
        return run_quality_report(parsed, t0=t0)

    raise IntentValidationError(f"Unsupported operation '{op}'.")
