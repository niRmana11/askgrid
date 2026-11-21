from typing import Literal

from pydantic import BaseModel, Field

Operation = Literal[
    "describe_dataset",
    "aggregate",
    "group_aggregate",
    "top_n",
    "filter_rows",
    "time_series",
    "compare",
    "distribution",
    "correlation",
    "quality_report",
    "unsupported",
    "clarification_needed",
]

AggFunc = Literal["sum", "mean", "median", "min", "max", "count", "count_distinct", "std"]
FilterOp = Literal["eq", "neq", "gt", "gte", "lt", "lte", "contains"]
TimeFreq = Literal["day", "week", "month", "year"]
SortDirection = Literal["asc", "desc"]


class FilterClause(BaseModel):
    """A single filter condition applied universally before any data operation."""

    column: str
    op: FilterOp
    value: str


class AnalysisIntent(BaseModel):
    """Strict structured intent produced by the AI router and verified by the backend."""

    operation: Operation
    metric_column: str | None = None
    agg: AggFunc | None = None
    group_by: str | None = None
    n: int | None = None
    sort_by: str | None = None
    direction: SortDirection | None = None
    date_column: str | None = None
    freq: TimeFreq | None = None
    compare_column: str | None = None
    compare_a: str | None = None
    compare_b: str | None = None
    column_x: str | None = None
    column_y: str | None = None
    filters: list[FilterClause] = Field(default_factory=list)
    reason: str | None = None
    suggested_alternative: str | None = None
