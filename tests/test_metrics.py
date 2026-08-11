import math

from app import metrics
from app.metrics import percentile


def _reset() -> None:
    metrics.TRAFFIC = 0
    metrics.REQUEST_LATENCIES.clear()
    metrics.REQUEST_COSTS.clear()
    metrics.REQUEST_TOKENS_IN.clear()
    metrics.REQUEST_TOKENS_OUT.clear()
    metrics.QUALITY_SCORES.clear()
    metrics.ERRORS.clear()


def test_percentile_basic() -> None:
    assert percentile([100, 200, 300, 400], 50) >= 100


def test_percentile_matches_nearest_rank() -> None:
    for size in (10, 20, 33, 100):
        values = list(range(1, size + 1))
        for p in (50, 90, 95, 99):
            expected = float(values[math.ceil(p / 100 * size) - 1])
            assert percentile(values, p) == expected, f"size={size} p={p}"


def test_percentile_does_not_overestimate_p50() -> None:
    # round((50/100)*10 + 0.5) = round(5.5) = 6 vì Python làm tròn về số chẵn,
    # khiến bản cũ trả về phần tử thứ 6 (giá trị 6) thay vì thứ 5 (giá trị 5).
    assert percentile(list(range(1, 11)), 50) == 5.0


def test_percentile_edge_cases() -> None:
    assert percentile([], 95) == 0.0
    assert percentile([42], 99) == 42.0
    assert percentile([5, 1, 3], 100) == 5.0


def test_snapshot_error_rate_counts_failed_requests() -> None:
    _reset()
    for _ in range(9):
        metrics.record_request(
            latency_ms=1000, cost_usd=0.001, tokens_in=10, tokens_out=20, quality_score=0.9
        )
    metrics.record_error("RuntimeError")

    snap = metrics.snapshot()
    assert snap["error_rate_pct"] == 10.0
    assert snap["traffic"] == 9
    assert snap["error_breakdown"] == {"RuntimeError": 1}
    _reset()


def test_snapshot_error_rate_is_zero_without_traffic() -> None:
    _reset()
    assert metrics.snapshot()["error_rate_pct"] == 0.0
