import math

import numpy as np
import pandas as pd

from app.schemas.dataset import ColumnProfile, DatasetProfile, JsonScalar
from app.services.csv_parser import ParsedCSV


def _to_json_scalar(value: object) -> JsonScalar:
    """Convert Pandas/NumPy scalars into strictly JSON-serializable Python values."""
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


def build_dataset_profile(parsed: ParsedCSV, preview_limit: int = 10) -> DatasetProfile:
    """Generate a complete DatasetProfile from a ParsedCSV."""
    df = parsed.df
    columns: list[ColumnProfile] = []

    for col in df.columns:
        col_name = str(col)
        series = df[col]
        col_type = parsed.column_types.get(col_name, "string")
        missing_count = int(series.isna().sum())
        non_null = series.dropna()
        unique_count = int(non_null.nunique())

        min_val: float | str | None = None
        max_val: float | str | None = None
        mean_val: float | None = None
        median_val: float | None = None
        top_values: list[str] = []

        if col_type in ("integer", "float") and not non_null.empty:
            min_val = round(float(non_null.min()), 4)
            max_val = round(float(non_null.max()), 4)
            mean_val = round(float(non_null.mean()), 4)
            median_val = round(float(non_null.median()), 4)
        elif col_type == "date" and not non_null.empty:
            min_dt = non_null.min()
            max_dt = non_null.max()
            if isinstance(min_dt, pd.Timestamp):
                min_val = min_dt.strftime("%Y-%m-%d")
            if isinstance(max_dt, pd.Timestamp):
                max_val = max_dt.strftime("%Y-%m-%d")
        elif not non_null.empty:
            top_values = [str(v) for v in non_null.astype("string").value_counts().head(5).index]

        columns.append(
            ColumnProfile(
                name=col_name,
                inferred_type=col_type,
                missing_count=missing_count,
                unique_count=unique_count,
                min_value=min_val,
                max_value=max_val,
                mean_value=mean_val,
                median_value=median_val,
                top_values=top_values,
            )
        )

    preview_rows: list[dict[str, JsonScalar]] = []
    for _, row in df.head(preview_limit).iterrows():
        preview_rows.append({str(col): _to_json_scalar(row[col]) for col in df.columns})

    return DatasetProfile(
        row_count=len(df),
        column_count=len(df.columns),
        duplicate_row_count=int(df.duplicated().sum()),
        encoding=parsed.encoding,
        delimiter=parsed.delimiter,
        date_format_note=parsed.date_format_note,
        columns=columns,
        preview_rows=preview_rows,
    )
