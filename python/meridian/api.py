from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI, HTTPException

from meridian.backtest import run_purged_walkforward
from meridian.config import settings
from meridian.scoring import ipo_dislocation_score
from meridian.storage import Storage
from meridian.types import BacktestRequest, IPOScoreCard, ScoreRequest, ThroughputSnapshot

app = FastAPI(title="Meridian", version="0.1.0")
store = Storage(settings.database_url)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/ipo/score", response_model=IPOScoreCard)
def score(payload: ScoreRequest) -> IPOScoreCard:
    return ipo_dislocation_score(
        company_id=payload.company_id,
        as_of_ts=payload.as_of_ts,
        horizon_days=payload.horizon_days,
        storage=store,
    )


@app.get("/v1/ipo/{company_id}/evidence-graph")
def evidence_graph(company_id: str, as_of: datetime):
    graph = store.latest_graph_for_company(company_id)
    if graph is None:
        card = ipo_dislocation_score(
            company_id=company_id,
            as_of_ts=as_of,
            horizon_days=28,
            storage=store,
        )
        graph = store.get_graph(card.evidence_graph_id)

    if graph is None:
        raise HTTPException(status_code=404, detail="evidence graph not found")
    return graph


@app.post("/v1/ipo/backtest")
def backtest(payload: BacktestRequest):
    return run_purged_walkforward(
        start_date=payload.start_date,
        end_date=payload.end_date,
        horizon_days=payload.horizon_days,
        universe=payload.universe,
        storage=store,
    )


@app.get("/v1/system/throughput", response_model=ThroughputSnapshot)
def throughput() -> ThroughputSnapshot:
    return store.throughput()
