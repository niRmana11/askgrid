from pathlib import Path

from app.schemas.intent import AnalysisIntent
from app.services.csv_parser import parse_csv_bytes
from app.services.engine import execute_intent

FIXTURES = Path(__file__).parent / "fixtures"


def test_golden_q09_time_series_monthly() -> None:
    parsed = parse_csv_bytes((FIXTURES / "orders_sample.csv").read_bytes())
    res = execute_intent(
        parsed,
        AnalysisIntent(
            operation="time_series",
            date_column="order_date",
            metric_column="revenue",
            agg="sum",
            freq="month",
        ),
    )
    assert res.data["series"] == {
        "2026-08": 234565.0,
        "2026-09": 321030.0,
        "2026-10": 404595.0,
    }
    assert res.chart is not None and res.chart.chart_type == "line"


def test_golden_q10_compare_periods_and_groups() -> None:
    parsed = parse_csv_bytes((FIXTURES / "orders_sample.csv").read_bytes())

    # Q10: September 2026 vs October 2026 revenue
    period_res = execute_intent(
        parsed,
        AnalysisIntent(
            operation="compare",
            compare_column="order_date",
            compare_a="2026-09",
            compare_b="2026-10",
            metric_column="revenue",
            agg="sum",
        ),
    )
    assert period_res.data["a"] == 321030.0
    assert period_res.data["b"] == 404595.0
    assert period_res.data["diff"] == 83565.0
    assert period_res.data["pct_change"] == 26.03

    # Category comparison: Colombo vs Kandy
    city_res = execute_intent(
        parsed,
        AnalysisIntent(
            operation="compare",
            compare_column="city",
            compare_a="Colombo",
            compare_b="Kandy",
            metric_column="revenue",
            agg="sum",
        ),
    )
    assert city_res.status == "ok"
    assert city_res.chart is not None and city_res.chart.chart_type == "delta"


def test_golden_q11_and_q12_distribution_and_correlation() -> None:
    parsed = parse_csv_bytes((FIXTURES / "orders_sample.csv").read_bytes())

    # Q11: distribution of revenue
    dist_res = execute_intent(
        parsed, AnalysisIntent(operation="distribution", metric_column="revenue")
    )
    assert dist_res.data["median"] == 32150.0
    assert dist_res.data["count"] == 24
    assert dist_res.chart is not None and dist_res.chart.chart_type == "histogram"

    # Q12: correlation between discount_pct and quantity
    corr_res = execute_intent(
        parsed,
        AnalysisIntent(operation="correlation", column_x="discount_pct", column_y="quantity"),
    )
    assert corr_res.data["pearson_r"] == 0.8812
    assert corr_res.data["strength"] == "strong"
    assert corr_res.chart is not None and corr_res.chart.chart_type == "scatter"


def test_golden_q13_and_q15_quality_reports() -> None:
    # Q13: messy_sales.csv missing values + duplicate row
    messy = parse_csv_bytes((FIXTURES / "messy_sales.csv").read_bytes())
    q13 = execute_intent(messy, AnalysisIntent(operation="quality_report"))
    assert q13.data["rows"] == 13
    assert q13.data["exact_duplicates"] == 1
    assert q13.data["missing_by_col"] == {"Amount": 1, "Payment_Method": 1}

    # Q15: inventory_sample.csv missing stock, negative stock, and 3 IQR unit_cost outliers
    inv = parse_csv_bytes((FIXTURES / "inventory_sample.csv").read_bytes())
    q15 = execute_intent(inv, AnalysisIntent(operation="quality_report"))
    assert q15.data["missing_by_col"] == {"stock_qty": 1}
    assert q15.data["negative_counts"] == {"stock_qty": 1}
    iqr_outliers = q15.data["iqr_outliers"]
    assert isinstance(iqr_outliers, dict)
    assert iqr_outliers["unit_cost"]["count"] == 3
