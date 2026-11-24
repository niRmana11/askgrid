_AGG_LABELS: dict[str, str] = {
    "sum": "total",
    "mean": "average",
    "median": "median",
    "min": "lowest",
    "max": "highest",
    "count": "count of",
    "count_distinct": "unique count of",
    "std": "standard deviation of",
}


def human_col(col: str | None) -> str:
    """Format snake_case column names like 'unit_cost' as 'unit cost' for display."""
    return col.replace("_", " ") if col else "rows"


def human_agg(agg: str) -> str:
    """Convert internal agg names like 'mean' into readable English like 'average'."""
    return _AGG_LABELS.get(agg, agg)
