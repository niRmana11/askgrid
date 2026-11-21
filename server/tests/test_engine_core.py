from pathlib import Path

import pytest

from app.schemas.intent import AnalysisIntent, FilterClause
from app.services.csv_parser import parse_csv_bytes
from app.services.engine import execute_intent
from app.services.intent_validator import IntentValidationError

FIXTURES = Path(__file__).parent / "fixtures"


def test_golden_q01_to_q04_describe_and_aggregates() -> None:
    parsed = parse_csv_bytes((FIXTURES / "orders_sample.csv").read_bytes())

    # Q01: describe_dataset
    r1 = execute_intent(parsed, AnalysisIntent(operation="describe_dataset"))
    assert r1.data["rows"] == 24
    assert r1.data["columns"] == 11

    # Q02: total revenue
    r2 = execute_intent(
        parsed, AnalysisIntent(operation="aggregate", metric_column="revenue", agg="sum")
    )
    assert r2.data["value"] == 960190.0

    # Q03: mean revenue
    r3 = execute_intent(
        parsed, AnalysisIntent(operation="aggregate", metric_column="revenue", agg="mean")
    )
    assert r3.data["value"] == 40007.92

    # Q04: filtered aggregate (Paid orders only)
    r4 = execute_intent(
        parsed,
        AnalysisIntent(
            operation="aggregate",
            metric_column="revenue",
            agg="sum",
            filters=[FilterClause(column="status", op="eq", value="Paid")],
        ),
    )
    assert r4.data["value"] == 792135.0
    assert r4.audit is not None
    assert r4.audit.filters_applied == ["status eq 'Paid'"]


def test_golden_q05_to_q08_group_topn_and_filter_rows() -> None:
    parsed = parse_csv_bytes((FIXTURES / "orders_sample.csv").read_bytes())

    # Q05: group_aggregate + % of total
    r5 = execute_intent(
        parsed,
        AnalysisIntent(
            operation="group_aggregate", group_by="category", metric_column="revenue", agg="sum"
        ),
    )
    assert r5.chart is not None
    by_cat = {p.label: (p.value, p.pct_of_total) for p in r5.chart.points}
    assert by_cat["Electronics"] == (460050.0, 47.91)
    assert by_cat["Furniture"] == (316950.0, 33.01)
    assert by_cat["Accessories"] == (183190.0, 19.08)

    # Q06: top 3 products
    r6 = execute_intent(
        parsed,
        AnalysisIntent(
            operation="top_n",
            group_by="product",
            metric_column="revenue",
            agg="sum",
            n=3,
            direction="desc",
        ),
    )
    assert r6.chart is not None
    assert [(p.label, p.value) for p in r6.chart.points] == [
        ("27-inch Monitor", 251600.0),
        ("Standing Desk", 165750.0),
        ("Ergonomic Chair", 151200.0),
    ]

    # Q07: top 3 customers in Colombo (universal filter!)
    r7 = execute_intent(
        parsed,
        AnalysisIntent(
            operation="top_n",
            group_by="customer",
            metric_column="revenue",
            agg="sum",
            n=3,
            direction="desc",
            filters=[FilterClause(column="city", op="eq", value="Colombo")],
        ),
    )
    assert r7.chart is not None
    assert [(p.label, p.value) for p in r7.chart.points] == [
        ("Amaya Wickramasinghe", 267750.0),
        ("Kasun Perera", 139600.0),
        ("Sahan Gunasekara", 108375.0),
    ]

    # Q08: filter_rows (Unpaid orders)
    r8 = execute_intent(
        parsed,
        AnalysisIntent(
            operation="filter_rows",
            filters=[FilterClause(column="status", op="eq", value="Unpaid")],
        ),
    )
    assert r8.data["row_count"] == 2
    assert [row["order_id"] for row in r8.rows] == ["ORD-1011", "ORD-1019"]


def test_golden_q14_messy_sales_excludes_nulls_transparently() -> None:
    parsed = parse_csv_bytes((FIXTURES / "messy_sales.csv").read_bytes())
    res = execute_intent(
        parsed, AnalysisIntent(operation="aggregate", metric_column="Amount", agg="sum")
    )
    assert res.data["value"] == 180700.50
    assert res.audit is not None
    assert res.audit.nulls_excluded == 1


def test_validator_blocks_missing_columns_bad_types_and_limits() -> None:
    parsed = parse_csv_bytes((FIXTURES / "orders_sample.csv").read_bytes())

    # Missing column (Q17 profit)
    with pytest.raises(IntentValidationError, match="does not exist"):
        execute_intent(
            parsed, AnalysisIntent(operation="aggregate", metric_column="profit", agg="sum")
        )

    # Sum on text column
    with pytest.raises(IntentValidationError, match="requires a numeric column"):
        execute_intent(
            parsed, AnalysisIntent(operation="aggregate", metric_column="customer", agg="sum")
        )

    # Result limit above 50
    with pytest.raises(IntentValidationError, match="between 1 and 50"):
        execute_intent(
            parsed,
            AnalysisIntent(
                operation="top_n", group_by="product", metric_column="revenue", agg="sum", n=500
            ),
        )
