from datetime import datetime, timezone

from meridian.backtest import run_purged_walkforward
from meridian.scoring import ipo_dislocation_score
from meridian.storage import Storage


def test_score_shape() -> None:
    card = ipo_dislocation_score(
        company_id="ACME-IPO",
        as_of_ts=datetime(2026, 2, 24, 15, 30, tzinfo=timezone.utc),
        horizon_days=28,
        storage=Storage(),
    )
    assert card.company_id == "ACME-IPO"
    assert -100 <= card.score <= 100
    assert 0 <= card.uncertainty <= 1
    assert card.evidence_graph_id.startswith("graph-")


def test_replay_lineage_hash_deterministic() -> None:
    as_of = datetime(2026, 2, 24, 15, 30, tzinfo=timezone.utc)
    one = ipo_dislocation_score("NOVA-IPO", as_of, 28, storage=Storage())
    two = ipo_dislocation_score("NOVA-IPO", as_of, 28, storage=Storage())
    assert one.lineage_hash == two.lineage_hash


def test_backtest_outputs_metrics() -> None:
    metrics = run_purged_walkforward(
        start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        end_date=datetime(2026, 2, 1, tzinfo=timezone.utc),
        horizon_days=28,
        universe=["ACME-IPO", "NOVA-IPO"],
        storage=Storage(),
    )
    assert metrics.universe_size == 2
    assert metrics.meridian_ic >= metrics.baseline_ic
