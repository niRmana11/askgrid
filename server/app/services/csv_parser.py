import csv
import io
import re
from dataclasses import dataclass

import pandas as pd

from app.schemas.dataset import ColumnType

# Matches currency symbol ("$45.50"), known currency code + space ("LKR 125,000.00"),
# or comma-formatted number ("12,500.00") — never hyphenated IDs like "ORD-1011".
_CURRENCY_RE = re.compile(
    r"^(?:(?:\$|€|£|¥|₹)\s*|(?:LKR|USD|EUR|GBP|INR|AUD|CAD|SGD|Rs\.?)\s+)"
    r"-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?$"
    r"|^-?\d{1,3}(?:,\d{3})+(?:\.\d+)?$"
)
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(?::\d{2})?)?$")
_SLASH_DATE_RE = re.compile(r"^\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}$")


class CSVParseError(ValueError):
    """Raised when an uploaded CSV fails security validation or parsing."""


@dataclass(frozen=True)
class ParsedCSV:
    """Container for a validated, normalized DataFrame and parsing metadata."""

    df: pd.DataFrame
    encoding: str
    delimiter: str
    date_format_note: str | None
    column_types: dict[str, ColumnType]


def _detect_encoding(raw_bytes: bytes) -> str:
    """Decode using utf-8-sig first (strips BOM cleanly), falling back to Windows-1252."""
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            raw_bytes.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue
    raise CSVParseError("Could not decode file text. Please upload a UTF-8 or CSV text file.")


def _detect_delimiter(sample_text: str) -> str:
    """Detect comma, semicolon, or tab delimiter safely with a comma fallback."""
    try:
        dialect = csv.Sniffer().sniff(sample_text, delimiters=",;\t")
        return dialect.delimiter
    except csv.Error:
        return ","


def _normalize_columns(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, ColumnType], str | None]:
    """Infer and normalize currency strings and date strings into proper Pandas dtypes."""
    column_types: dict[str, ColumnType] = {}
    date_format_note: str | None = None

    for col in df.columns:
        col_name = str(col)
        series = df[col]

        if pd.api.types.is_bool_dtype(series.dtype):
            column_types[col_name] = "boolean"
            continue
        if pd.api.types.is_integer_dtype(series.dtype):
            column_types[col_name] = "integer"
            continue
        if pd.api.types.is_float_dtype(series.dtype):
            column_types[col_name] = "float"
            continue
        if pd.api.types.is_datetime64_any_dtype(series.dtype):
            column_types[col_name] = "date"
            continue

        # Sample up to 500 non-null string values for fast (<1 ms) type detection
        sample = [str(v).strip() for v in series.dropna().head(500).tolist() if str(v).strip()]
        if not sample:
            column_types[col_name] = "string"
            continue

        iso_ratio = sum(1 for v in sample if _ISO_DATE_RE.match(v)) / len(sample)
        slash_ratio = sum(1 for v in sample if _SLASH_DATE_RE.match(v)) / len(sample)
        currency_ratio = sum(1 for v in sample if _CURRENCY_RE.match(v)) / len(sample)

        if iso_ratio >= 0.8:
            df[col] = pd.to_datetime(series, format="mixed", dayfirst=False, errors="coerce")
            column_types[col_name] = "date"
            date_format_note = date_format_note or "ISO (YYYY-MM-DD)"
        elif slash_ratio >= 0.8:
            df[col] = pd.to_datetime(series, format="mixed", dayfirst=True, errors="coerce")
            column_types[col_name] = "date"
            date_format_note = "Day-first (DD/MM/YYYY)"
        elif currency_ratio >= 0.8:
            cleaned = series.astype("string").str.replace(r"[^\d.\-]", "", regex=True)
            df[col] = pd.to_numeric(cleaned, errors="coerce")
            column_types[col_name] = "float"
        else:
            column_types[col_name] = "string"

    return df, column_types, date_format_note


def parse_csv_bytes(
    raw_bytes: bytes,
    *,
    max_size_mb: int = 10,
    max_rows: int = 100_000,
    max_columns: int = 50,
) -> ParsedCSV:
    """Validate raw uploaded bytes and parse them into a normalized ParsedCSV."""
    max_bytes = max_size_mb * 1024 * 1024
    if not raw_bytes or not raw_bytes.strip():
        raise CSVParseError("Uploaded CSV file is empty.")
    if len(raw_bytes) > max_bytes:
        raise CSVParseError(f"File exceeds maximum allowed size of {max_size_mb} MB.")
    if b"\x00" in raw_bytes:
        raise CSVParseError("Binary file detected. Please upload a valid text CSV file.")

    encoding = _detect_encoding(raw_bytes)
    text = raw_bytes.decode(encoding)
    delimiter = _detect_delimiter(text[:4096])

    try:
        df = pd.read_csv(io.StringIO(text), sep=delimiter)
    except Exception as exc:
        raise CSVParseError(f"Could not parse CSV structure: {exc}") from exc

    if df.empty or len(df.columns) == 0:
        raise CSVParseError("CSV contains no data rows.")
    if len(df.columns) > max_columns:
        raise CSVParseError(f"CSV exceeds maximum allowed {max_columns} columns.")
    if len(df) > max_rows:
        raise CSVParseError(f"CSV exceeds maximum allowed {max_rows:,} rows.")

    # Clean leading/trailing spaces in headers
    df.columns = pd.Index([str(c).strip() for c in df.columns])

    df, column_types, date_format_note = _normalize_columns(df)
    return ParsedCSV(
        df=df,
        encoding=encoding,
        delimiter=delimiter,
        date_format_note=date_format_note,
        column_types=column_types,
    )
