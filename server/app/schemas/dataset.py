from typing import Literal

from pydantic import BaseModel, Field

ColumnType = Literal["integer", "float", "date", "boolean", "string"]
JsonScalar = str | int | float | bool | None


class ColumnProfile(BaseModel):
    """Summary profile for a single dataset column."""

    name: str
    inferred_type: ColumnType
    missing_count: int
    unique_count: int
    min_value: float | str | None = None
    max_value: float | str | None = None
    mean_value: float | None = None
    median_value: float | None = None
    top_values: list[str] = Field(default_factory=list)


class DatasetProfile(BaseModel):
    """Complete metadata profile and preview rows for an uploaded CSV."""

    row_count: int
    column_count: int
    duplicate_row_count: int
    encoding: str
    delimiter: str
    date_format_note: str | None = None
    columns: list[ColumnProfile]
    preview_rows: list[dict[str, JsonScalar]]
