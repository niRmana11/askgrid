from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.dataset import JsonScalar

ChartType = Literal[
    "kpi",
    "bar",
    "horizontal_bar",
    "line",
    "histogram",
    "scatter",
    "delta",
    "table",
]


class CalculationAudit(BaseModel):
    """Transparency record showing exactly how Python computed the answer."""

    operation: str
    columns_used: list[str]
    filters_applied: list[str] = Field(default_factory=list)
    rows_scanned: int
    rows_matched: int
    nulls_excluded: int = 0
    date_format_used: str | None = None
    execution_ms: float


class ChartPoint(BaseModel):
    """Single labeled point or category bar for chart rendering."""

    label: str
    value: float
    pct_of_total: float | None = None
    x_value: float | None = None


class ChartSpec(BaseModel):
    """Structured chart description rendered by the React frontend."""

    chart_type: ChartType
    title: str
    x_label: str | None = None
    y_label: str | None = None
    points: list[ChartPoint] = Field(default_factory=list)


class AnalysisResponse(BaseModel):
    """Final verified response returned by the deterministic Pandas engine."""

    status: Literal["ok", "unsupported", "clarification_needed"]
    headline: str
    explanation: str
    data: dict[str, object] = Field(default_factory=dict)
    rows: list[dict[str, JsonScalar]] = Field(default_factory=list)
    chart: ChartSpec | None = None
    audit: CalculationAudit | None = None
    suggested_alternative: str | None = None
