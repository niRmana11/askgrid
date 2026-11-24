from pathlib import Path

from fastapi.testclient import TestClient

from app.core.rate_limit import SlidingWindowRateLimiter
from app.main import app
from app.schemas.intent import AnalysisIntent
from app.services.csv_parser import parse_csv_bytes
from app.services.engine import execute_intent

FIXTURES = Path(__file__).parent / "fixtures"


def test_security_headers_attached_to_responses() -> None:
    client = TestClient(app)
    res = client.get("/api/v1/health")

    assert res.status_code == 200
    assert res.headers["x-content-type-options"] == "nosniff"
    assert res.headers["x-frame-options"] == "DENY"
    assert res.headers["referrer-policy"] == "no-referrer"
    assert "x-request-id" in res.headers


def test_sliding_window_rate_limiter_enforces_limit_and_recovers() -> None:
    now = 100.0
    limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=60.0, clock=lambda: now)

    assert limiter.check("1.2.3.4")[0] is True
    assert limiter.check("1.2.3.4")[0] is True

    allowed, retry_after = limiter.check("1.2.3.4")
    assert allowed is False
    assert retry_after >= 1

    # Different IP is unaffected
    assert limiter.check("5.6.7.8")[0] is True

    # After 61 seconds, original IP is allowed again
    now = 161.0
    assert limiter.check("1.2.3.4")[0] is True


def test_human_friendly_headlines_remove_technical_jargon() -> None:
    orders = parse_csv_bytes((FIXTURES / "orders_sample.csv").read_bytes())
    agg_res = execute_intent(
        orders, AnalysisIntent(operation="aggregate", metric_column="revenue", agg="sum")
    )
    assert agg_res.headline == "Total revenue: 960,190.00"

    inv = parse_csv_bytes((FIXTURES / "inventory_sample.csv").read_bytes())
    top_res = execute_intent(
        inv,
        AnalysisIntent(
            operation="top_n",
            group_by="item_name",
            metric_column="unit_cost",
            agg="mean",
            n=1,
            direction="desc",
        ),
    )
    assert top_res.headline == "Highest by average unit cost: Enterprise Server Rack (950,000.00)"
