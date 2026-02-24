from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field


class ScoreRequest(BaseModel):
    company_id: str = Field(min_length=1)
    as_of_ts: datetime
    horizon_days: int = Field(default=28, ge=14, le=42)


class BacktestRequest(BaseModel):
    start_date: datetime
    end_date: datetime
    horizon_days: int = Field(default=28, ge=14, le=42)
    universe: List[str] = Field(default_factory=list)


class ThroughputSnapshot(BaseModel):
    crawl_rate_pages_per_min: float
    queue_lag_p95_minutes: float
    extraction_latency_ms_p95: float
    failure_buckets: Dict[str, int]


class EvidenceNode(BaseModel):
    url: str
    captured_at: datetime
    node_type: Literal["claim", "reality", "novelty", "meta"]
    normalized_fact: str
    confidence: float = Field(ge=0.0, le=1.0)
    extractor_version: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvidenceEdge(BaseModel):
    source_idx: int
    target_idx: int
    relation: Literal["supports", "contradicts", "derived_from"]


class EvidenceGraph(BaseModel):
    graph_id: str
    company_id: str
    as_of_ts: datetime
    nodes: List[EvidenceNode]
    edges: List[EvidenceEdge]


class IPOScoreCard(BaseModel):
    company_id: str
    as_of_ts: datetime
    horizon_days: int
    score: float = Field(ge=-100.0, le=100.0)
    uncertainty: float = Field(ge=0.0, le=1.0)
    top_drivers: List[str]
    decay_half_life_days: float = Field(gt=0.0)
    evidence_graph_id: str
    lineage_hash: str
    invalid_if: List[str]


class BacktestMetrics(BaseModel):
    start_date: datetime
    end_date: datetime
    horizon_days: int
    universe_size: int
    baseline_ic: float
    meridian_ic: float
    ic_uplift_pct: float
    baseline_decile_spread_bps_month: float
    meridian_decile_spread_bps_month: float
    spread_uplift_bps_month: float
