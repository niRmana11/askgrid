import math
import time
from collections.abc import Callable

import numpy as np
import pandas as pd

from app.schemas.analysis import AnalysisResponse, CalculationAudit, ChartPoint, ChartSpec
from app.schemas.intent import AggFunc, AnalysisIntent
from app.services.csv_parser import ParsedCSV
from app.services.formatting import human_agg, human_col

AggFn = Callable[[pd.DataFrame, str | None, AggFunc], tuple[float, int]]
GroupedAggFn = Callable[[pd.DataFrame, str, str | None, AggFunc], list[tuple[str, float]]]


def run_time_series(
    parsed: ParsedCSV,
    filtered: pd.DataFrame,
    intent: AnalysisIntent,
    *,
    filters_applied: list[str],
    rows_scanned: int,
    t0: float,
    grouped_agg_fn: GroupedAggFn,
) -> AnalysisResponse:
    """Op 6: Aggregate a metric over day/week/month/year periods chronologically."""
    assert intent.date_column is not None
    date_col = intent.date_column
    freq = intent.freq or "month"
    agg: AggFunc = intent.agg or "sum"

    valid_mask = filtered[date_col].notna()
    nulls_excluded = int((~valid_mask).sum())
    ts_df = filtered[valid_mask].copy()

    dt_series = ts_df[date_col]
    if freq == "day":
        ts_df["__period__"] = dt_series.dt.strftime("%Y-%m-%d")
    elif freq == "week":
        ts_df["__period__"] = dt_series.dt.to_period("W").astype(str)
    elif freq == "year":
        ts_df["__period__"] = dt_series.dt.strftime("%Y")
    else:
        ts_df["__period__"] = dt_series.dt.strftime("%Y-%m")

    pairs = grouped_agg_fn(ts_df, "__period__", intent.metric_column, agg)
    pairs.sort(key=lambda item: item[0])
    points = [ChartPoint(label=label, value=val) for label, val in pairs]

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
    metric_label = intent.metric_column or "rows"
    readable_metric = human_col(intent.metric_column)
    readable_agg = human_agg(agg)
    return AnalysisResponse(
        status="ok",
        headline=(
            f"{freq.capitalize()} {readable_agg} {readable_metric} across {len(points)} periods."
        ),
        explanation=f"Grouped {len(ts_df):,} dated rows by {freq} using {human_col(date_col)}.",
        data={"freq": freq, "series": {p.label: p.value for p in points}},
        chart=ChartSpec(
            chart_type="line",
            title=f"{freq.capitalize()} {readable_agg} {readable_metric}",
            x_label=date_col,
            y_label=metric_label,
            points=points,
        ),
        audit=CalculationAudit(
            operation="time_series",
            columns_used=[c for c in [date_col, intent.metric_column] if c],
            filters_applied=filters_applied,
            rows_scanned=rows_scanned,
            rows_matched=len(ts_df),
            nulls_excluded=nulls_excluded,
            date_format_used=parsed.date_format_note,
            execution_ms=elapsed_ms,
        ),
    )


def run_compare(
    parsed: ParsedCSV,
    filtered: pd.DataFrame,
    intent: AnalysisIntent,
    *,
    filters_applied: list[str],
    rows_scanned: int,
    t0: float,
    agg_fn: AggFn,
) -> AnalysisResponse:
    """Op 7: Compare Period A vs Period B or Group A vs Group B with diff & % change."""
    assert intent.compare_column is not None
    assert intent.compare_a is not None
    assert intent.compare_b is not None

    col = intent.compare_column
    val_a = intent.compare_a.strip()
    val_b = intent.compare_b.strip()
    agg: AggFunc = intent.agg or "sum"

    if parsed.column_types.get(col) == "date":
        date_str = filtered[col].dt.strftime("%Y-%m-%d").fillna("")
        df_a = filtered[date_str.str.startswith(val_a)]
        df_b = filtered[date_str.str.startswith(val_b)]
    else:
        norm = filtered[col].astype("string").str.strip().str.lower()
        df_a = filtered[norm == val_a.lower()]
        df_b = filtered[norm == val_b.lower()]

    res_a, nulls_a = agg_fn(df_a, intent.metric_column, agg)
    res_b, nulls_b = agg_fn(df_b, intent.metric_column, agg)
    diff = round(res_b - res_a, 2)
    pct_change = round((diff / res_a) * 100, 2) if res_a != 0 else None

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
    metric_label = intent.metric_column or "rows"
    pct_text = f" ({pct_change:+.2f}%)" if pct_change is not None else ""
    return AnalysisResponse(
        status="ok",
        headline=f"{val_a} vs {val_b}: {res_a:,.2f} -> {res_b:,.2f} ({diff:+,.2f}{pct_text})",
        explanation=(
            f"Compared {agg}({metric_label}) on '{col}' between '{val_a}' "
            f"({len(df_a)} rows) and '{val_b}' ({len(df_b)} rows)."
        ),
        data={
            "label_a": val_a,
            "label_b": val_b,
            "a": res_a,
            "b": res_b,
            "diff": diff,
            "pct_change": pct_change,
        },
        chart=ChartSpec(
            chart_type="delta",
            title=f"{agg.upper()}({metric_label}): {val_a} vs {val_b}",
            x_label=col,
            y_label=metric_label,
            points=[
                ChartPoint(label=val_a, value=res_a),
                ChartPoint(label=val_b, value=res_b),
            ],
        ),
        audit=CalculationAudit(
            operation="compare",
            columns_used=[c for c in [col, intent.metric_column] if c],
            filters_applied=filters_applied,
            rows_scanned=rows_scanned,
            rows_matched=len(df_a) + len(df_b),
            nulls_excluded=nulls_a + nulls_b,
            date_format_used=parsed.date_format_note,
            execution_ms=elapsed_ms,
        ),
    )


def run_distribution(
    parsed: ParsedCSV,
    filtered: pd.DataFrame,
    intent: AnalysisIntent,
    *,
    filters_applied: list[str],
    rows_scanned: int,
    t0: float,
) -> AnalysisResponse:
    """Op 8: Compute quartiles, spread stats, and histogram bins for a numeric column."""
    assert intent.metric_column is not None
    col = intent.metric_column
    series = filtered[col]
    nulls_excluded = int(series.isna().sum())
    clean = series.dropna()

    if clean.empty:
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        return AnalysisResponse(
            status="ok",
            headline=f"No non-null values found in '{col}'.",
            explanation="All matching rows were missing values.",
            data={"count": 0},
            audit=CalculationAudit(
                operation="distribution",
                columns_used=[col],
                filters_applied=filters_applied,
                rows_scanned=rows_scanned,
                rows_matched=0,
                nulls_excluded=nulls_excluded,
                execution_ms=elapsed_ms,
            ),
        )

    values = clean.to_numpy(dtype=float)
    q1 = round(float(clean.quantile(0.25)), 2)
    median = round(float(clean.median()), 2)
    q3 = round(float(clean.quantile(0.75)), 2)
    mean = round(float(clean.mean()), 2)
    min_val = round(float(clean.min()), 2)
    max_val = round(float(clean.max()), 2)

    num_bins = min(10, max(1, int(clean.nunique())))
    counts, edges = np.histogram(values, bins=num_bins)
    points = [
        ChartPoint(label=f"{edges[i]:,.1f}-{edges[i + 1]:,.1f}", value=float(counts[i]))
        for i in range(len(counts))
    ]

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
    return AnalysisResponse(
        status="ok",
        headline=(
            f"Distribution of '{col}': median {median:,.2f}, range {min_val:,.2f}..{max_val:,.2f}"
        ),
        explanation=(
            f"Computed quartiles and {num_bins}-bin histogram across {len(clean):,} values."
        ),
        data={
            "count": len(clean),
            "min": min_val,
            "q1": q1,
            "median": median,
            "mean": mean,
            "q3": q3,
            "max": max_val,
        },
        chart=ChartSpec(
            chart_type="histogram",
            title=f"Distribution of {col}",
            x_label=col,
            y_label="Count",
            points=points,
        ),
        audit=CalculationAudit(
            operation="distribution",
            columns_used=[col],
            filters_applied=filters_applied,
            rows_scanned=rows_scanned,
            rows_matched=len(clean),
            nulls_excluded=nulls_excluded,
            date_format_used=parsed.date_format_note,
            execution_ms=elapsed_ms,
        ),
    )


def run_correlation(
    parsed: ParsedCSV,
    filtered: pd.DataFrame,
    intent: AnalysisIntent,
    *,
    filters_applied: list[str],
    rows_scanned: int,
    t0: float,
) -> AnalysisResponse:
    """Op 9: Compute deterministic Pearson correlation r and scatter plot points."""
    assert intent.column_x is not None
    assert intent.column_y is not None
    col_x, col_y = intent.column_x, intent.column_y

    pair_df = filtered[[col_x, col_y]].dropna()
    nulls_excluded = len(filtered) - len(pair_df)

    xs = pair_df[col_x].to_numpy(dtype=float)
    ys = pair_df[col_y].to_numpy(dtype=float)

    if len(pair_df) < 2 or float(np.std(xs)) == 0.0 or float(np.std(ys)) == 0.0:
        pearson_r = 0.0
    else:
        raw_r = float(np.corrcoef(xs, ys)[0, 1])
        pearson_r = 0.0 if math.isnan(raw_r) else round(raw_r, 4)

    abs_r = abs(pearson_r)
    strength = "strong" if abs_r >= 0.7 else "moderate" if abs_r >= 0.4 else "weak"
    direction = "positive" if pearson_r > 0 else "negative" if pearson_r < 0 else "no"

    points = [
        ChartPoint(label=str(idx + 1), x_value=round(float(x), 4), value=round(float(y), 4))
        for idx, (x, y) in enumerate(zip(xs[:200], ys[:200], strict=False))
    ]

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
    readable_x = human_col(col_x)
    readable_y = human_col(col_y)
    return AnalysisResponse(
        status="ok",
        headline=(
            f"{strength.capitalize()} {direction} relationship between "
            f"{readable_x} and {readable_y} (r = {pearson_r:.4f})"
        ),
        explanation=(
            f"Measured linear relationship between {readable_x} and {readable_y} "
            f"across {len(pair_df):,} paired rows."
        ),
        data={
            "column_x": col_x,
            "column_y": col_y,
            "pearson_r": pearson_r,
            "strength": strength,
            "direction": direction,
        },
        chart=ChartSpec(
            chart_type="scatter",
            title=f"{readable_x} vs {readable_y} (r = {pearson_r:.4f})",
            x_label=col_x,
            y_label=col_y,
            points=points,
        ),
        audit=CalculationAudit(
            operation="correlation",
            columns_used=[col_x, col_y],
            filters_applied=filters_applied,
            rows_scanned=rows_scanned,
            rows_matched=len(pair_df),
            nulls_excluded=nulls_excluded,
            date_format_used=parsed.date_format_note,
            execution_ms=elapsed_ms,
        ),
    )


def run_quality_report(
    parsed: ParsedCSV,
    *,
    t0: float,
) -> AnalysisResponse:
    """Op 10: Detect missing values, exact duplicates, negatives, and IQR numeric outliers."""
    df = parsed.df
    rows_scanned = len(df)
    exact_duplicates = int(df.duplicated().sum())

    missing_by_col: dict[str, int] = {}
    negative_counts: dict[str, int] = {}
    iqr_outliers: dict[str, dict[str, object]] = {}

    for col in df.columns:
        col_name = str(col)
        series = df[col]
        miss = int(series.isna().sum())
        if miss > 0:
            missing_by_col[col_name] = miss

        if parsed.column_types.get(col_name) in ("integer", "float"):
            clean = series.dropna()
            neg_count = int((clean < 0).sum())
            if neg_count > 0:
                negative_counts[col_name] = neg_count

            if len(clean) >= 4:
                q1 = float(clean.quantile(0.25))
                q3 = float(clean.quantile(0.75))
                iqr = q3 - q1
                if iqr > 0:
                    lower = q1 - 1.5 * iqr
                    upper = q3 + 1.5 * iqr
                    outlier_vals = clean[(clean < lower) | (clean > upper)]
                    if not outlier_vals.empty:
                        iqr_outliers[col_name] = {
                            "count": len(outlier_vals),
                            "lower_fence": round(lower, 2),
                            "upper_fence": round(upper, 2),
                            "sample_values": [
                                round(float(v), 2) for v in outlier_vals.head(5).tolist()
                            ],
                        }

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
    total_missing = sum(missing_by_col.values())
    return AnalysisResponse(
        status="ok",
        headline=(
            f"Quality check: {total_missing} missing cell(s), "
            f"{exact_duplicates} duplicate row(s), "
            f"{len(iqr_outliers)} column(s) with IQR outliers."
        ),
        explanation=f"Scanned {rows_scanned:,} rows across {len(df.columns)} columns.",
        data={
            "rows": rows_scanned,
            "columns": len(df.columns),
            "exact_duplicates": exact_duplicates,
            "missing_by_col": missing_by_col,
            "negative_counts": negative_counts,
            "iqr_outliers": iqr_outliers,
        },
        chart=ChartSpec(chart_type="table", title="Data Quality Summary"),
        audit=CalculationAudit(
            operation="quality_report",
            columns_used=list(parsed.column_types.keys()),
            rows_scanned=rows_scanned,
            rows_matched=rows_scanned,
            date_format_used=parsed.date_format_note,
            execution_ms=elapsed_ms,
        ),
    )
