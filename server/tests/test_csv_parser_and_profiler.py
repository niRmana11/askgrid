from pathlib import Path

import pytest

from app.services.csv_parser import CSVParseError, parse_csv_bytes
from app.services.profiler import build_dataset_profile

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_and_profile_clean_orders_golden() -> None:
    parsed = parse_csv_bytes((FIXTURES / "orders_sample.csv").read_bytes())
    profile = build_dataset_profile(parsed, preview_limit=5)

    assert profile.row_count == 24
    assert profile.column_count == 11
    assert profile.duplicate_row_count == 0
    assert profile.delimiter == ","
    assert len(profile.preview_rows) == 5

    col_map = {c.name: c for c in profile.columns}
    assert col_map["order_date"].inferred_type == "date"
    assert col_map["order_id"].inferred_type == "string"
    assert col_map["revenue"].inferred_type in ("integer", "float")
    assert round(float(parsed.df["revenue"].sum()), 2) == 960190.0


def test_parse_and_profile_messy_sales_golden() -> None:
    parsed = parse_csv_bytes((FIXTURES / "messy_sales.csv").read_bytes())
    profile = build_dataset_profile(parsed)

    assert profile.row_count == 13
    assert profile.delimiter == ";"
    assert profile.duplicate_row_count == 1
    assert profile.date_format_note == "Day-first (DD/MM/YYYY)"

    col_map = {c.name: c for c in profile.columns}
    assert col_map["Sale_Date"].inferred_type == "date"
    assert col_map["Amount"].inferred_type == "float"
    assert col_map["Amount"].missing_count == 1
    assert col_map["Payment_Method"].missing_count == 1
    assert round(float(parsed.df["Amount"].sum()), 2) == 180700.50


def test_parse_and_profile_inventory_golden() -> None:
    parsed = parse_csv_bytes((FIXTURES / "inventory_sample.csv").read_bytes())
    profile = build_dataset_profile(parsed)

    col_map = {c.name: c for c in profile.columns}
    assert profile.row_count == 16
    assert col_map["stock_qty"].missing_count == 1
    assert col_map["stock_qty"].min_value == -4.0


def test_rejects_empty_binary_and_limit_violations() -> None:
    with pytest.raises(CSVParseError, match="empty"):
        parse_csv_bytes(b"   \n")

    with pytest.raises(CSVParseError, match="Binary"):
        parse_csv_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00IHDR")

    with pytest.raises(CSVParseError, match="maximum allowed size"):
        parse_csv_bytes(b"a,b\n1,2\n" * 500, max_size_mb=0)

    with pytest.raises(CSVParseError, match="maximum allowed 2 rows"):
        parse_csv_bytes(b"a,b\n1,2\n3,4\n5,6\n", max_rows=2)

    with pytest.raises(CSVParseError, match="maximum allowed 2 columns"):
        parse_csv_bytes(b"a,b,c\n1,2,3\n", max_columns=2)
