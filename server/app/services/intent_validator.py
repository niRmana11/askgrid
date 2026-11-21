from app.schemas.dataset import ColumnType
from app.schemas.intent import AnalysisIntent

NUMERIC_AGGS = frozenset({"sum", "mean", "median", "std"})
MAX_RESULT_LIMIT = 50


class IntentValidationError(ValueError):
    """Raised when an AnalysisIntent references invalid columns, types, or bounds."""


def _require_column(
    column: str | None,
    column_types: dict[str, ColumnType],
    field_name: str,
) -> str:
    if not column:
        raise IntentValidationError(f"Missing required field '{field_name}' for this operation.")
    if column not in column_types:
        available = ", ".join(column_types.keys())
        raise IntentValidationError(
            f"Column '{column}' does not exist in this dataset. Available columns: {available}"
        )
    return column


def _require_numeric(
    column: str,
    column_types: dict[str, ColumnType],
) -> None:
    if column_types.get(column) not in ("integer", "float"):
        raise IntentValidationError(
            f"Column '{column}' is '{column_types.get(column)}', "
            "but this calculation requires a numeric column."
        )


def validate_intent(intent: AnalysisIntent, column_types: dict[str, ColumnType]) -> AnalysisIntent:
    """Validate an AnalysisIntent strictly against actual dataset columns and dtypes."""
    op = intent.operation
    if op in ("unsupported", "clarification_needed", "describe_dataset", "quality_report"):
        return intent

    # Validate every universal filter clause first
    for clause in intent.filters:
        col = _require_column(clause.column, column_types, "filter.column")
        col_type = column_types[col]
        if col_type in ("integer", "float") and clause.op == "contains":
            raise IntentValidationError(
                f"Filter operator 'contains' cannot be used on numeric column '{col}'."
            )
        if col_type in ("string", "boolean") and clause.op in ("gt", "gte", "lt", "lte"):
            raise IntentValidationError(
                f"Numeric comparison '{clause.op}' cannot be used on text column '{col}'."
            )

    # Validate operation-specific fields and types
    if op == "aggregate":
        agg = intent.agg or "count"
        if agg != "count" or intent.metric_column is not None:
            col = _require_column(intent.metric_column, column_types, "metric_column")
            if agg in NUMERIC_AGGS:
                _require_numeric(col, column_types)

    elif op in ("group_aggregate", "top_n"):
        _require_column(intent.group_by, column_types, "group_by")
        agg = intent.agg or "sum"
        if agg != "count" or intent.metric_column is not None:
            col = _require_column(intent.metric_column, column_types, "metric_column")
            if agg in NUMERIC_AGGS:
                _require_numeric(col, column_types)
        if intent.n is not None and not (1 <= intent.n <= MAX_RESULT_LIMIT):
            raise IntentValidationError(
                f"Result limit 'n' must be between 1 and {MAX_RESULT_LIMIT}."
            )

    elif op == "filter_rows":
        if intent.sort_by is not None:
            _require_column(intent.sort_by, column_types, "sort_by")
        if intent.n is not None and not (1 <= intent.n <= MAX_RESULT_LIMIT):
            raise IntentValidationError(f"Row limit 'n' must be between 1 and {MAX_RESULT_LIMIT}.")

    elif op == "time_series":
        date_col = _require_column(intent.date_column, column_types, "date_column")
        if column_types[date_col] != "date":
            raise IntentValidationError(f"Column '{date_col}' is not a date column.")
        agg = intent.agg or "sum"
        if agg != "count" or intent.metric_column is not None:
            col = _require_column(intent.metric_column, column_types, "metric_column")
            if agg in NUMERIC_AGGS:
                _require_numeric(col, column_types)

    elif op == "compare":
        _require_column(intent.compare_column, column_types, "compare_column")
        if not intent.compare_a or not intent.compare_b:
            raise IntentValidationError(
                "Compare operation requires both 'compare_a' and 'compare_b'."
            )
        agg = intent.agg or "sum"
        if agg != "count" or intent.metric_column is not None:
            col = _require_column(intent.metric_column, column_types, "metric_column")
            if agg in NUMERIC_AGGS:
                _require_numeric(col, column_types)

    elif op == "distribution":
        col = _require_column(intent.metric_column, column_types, "metric_column")
        _require_numeric(col, column_types)

    elif op == "correlation":
        col_x = _require_column(intent.column_x, column_types, "column_x")
        col_y = _require_column(intent.column_y, column_types, "column_y")
        _require_numeric(col_x, column_types)
        _require_numeric(col_y, column_types)

    return intent
