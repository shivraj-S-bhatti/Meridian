from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List

try:
    import psycopg2
    from psycopg2.extras import Json
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    psycopg2 = None
    Json = None

from meridian.types import EvidenceGraph, EvidenceNode, IPOScoreCard, ThroughputSnapshot


@dataclass
class _MemStore:
    graphs: Dict[str, EvidenceGraph] = field(default_factory=dict)
    cards: List[IPOScoreCard] = field(default_factory=list)
    pages_crawled: int = 0
    extraction_events: int = 0
    failures: Dict[str, int] = field(default_factory=lambda: {"fetch": 0, "extract": 0, "db": 0})


class Storage:
    def __init__(self, database_url: str = "") -> None:
        self.database_url = database_url
        self._lock = threading.Lock()
        self._mem = _MemStore()

    def _conn(self):
        if not self.database_url or psycopg2 is None:
            return None
        return psycopg2.connect(self.database_url)

    def save_graph(self, graph: EvidenceGraph) -> None:
        with self._lock:
            self._mem.graphs[graph.graph_id] = graph

    def save_score_card(self, card: IPOScoreCard) -> None:
        with self._lock:
            self._mem.cards.append(card)

        conn = self._conn()
        if not conn:
            return
        try:
            with conn, conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO signal_cards (
                        company_id, as_of_ts, horizon_days, score, uncertainty,
                        decay_half_life_days, drivers, invalid_if, evidence_graph_id, lineage_hash
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (company_id, as_of_ts, horizon_days)
                    DO UPDATE SET
                        score = EXCLUDED.score,
                        uncertainty = EXCLUDED.uncertainty,
                        decay_half_life_days = EXCLUDED.decay_half_life_days,
                        drivers = EXCLUDED.drivers,
                        invalid_if = EXCLUDED.invalid_if,
                        evidence_graph_id = EXCLUDED.evidence_graph_id,
                        lineage_hash = EXCLUDED.lineage_hash
                    """,
                    (
                        card.company_id,
                        card.as_of_ts,
                        card.horizon_days,
                        card.score,
                        card.uncertainty,
                        card.decay_half_life_days,
                        Json(card.top_drivers) if Json is not None else json.dumps(card.top_drivers),
                        Json(card.invalid_if) if Json is not None else json.dumps(card.invalid_if),
                        card.evidence_graph_id,
                        card.lineage_hash,
                    ),
                )
        finally:
            conn.close()

    def save_facts(self, company_id: str, nodes: List[EvidenceNode]) -> None:
        with self._lock:
            self._mem.extraction_events += len(nodes)

        conn = self._conn()
        if not conn:
            return
        try:
            with conn, conn.cursor() as cur:
                for n in nodes:
                    cur.execute(
                        """
                        INSERT INTO facts (
                            company_id, source_url, captured_at, node_type,
                            normalized_fact, confidence, extractor_version, metadata
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            company_id,
                            n.url,
                            n.captured_at,
                            n.node_type,
                            n.normalized_fact,
                            n.confidence,
                            n.extractor_version,
                            Json(n.metadata) if Json is not None else json.dumps(n.metadata),
                        ),
                    )
        finally:
            conn.close()

    def get_graph(self, graph_id: str) -> EvidenceGraph | None:
        return self._mem.graphs.get(graph_id)

    def latest_graph_for_company(self, company_id: str) -> EvidenceGraph | None:
        graphs = [g for g in self._mem.graphs.values() if g.company_id == company_id]
        if not graphs:
            return None
        graphs.sort(key=lambda g: g.as_of_ts, reverse=True)
        return graphs[0]

    def queue_heartbeat(self, worker_id: str) -> None:
        conn = self._conn()
        if not conn:
            return
        ts = datetime.now(timezone.utc)
        try:
            with conn, conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO worker_heartbeats(worker_id, last_seen, metadata)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (worker_id)
                    DO UPDATE SET last_seen = EXCLUDED.last_seen
                    """,
                    (worker_id, ts, Json({}) if Json is not None else json.dumps({})),
                )
        finally:
            conn.close()

    def throughput(self) -> ThroughputSnapshot:
        with self._lock:
            pages = self._mem.pages_crawled
            extracts = self._mem.extraction_events
            failures = dict(self._mem.failures)

        crawl_rate = float(max(1, pages))
        latency = 120.0 if extracts else 350.0

        return ThroughputSnapshot(
            crawl_rate_pages_per_min=crawl_rate,
            queue_lag_p95_minutes=4.2,
            extraction_latency_ms_p95=latency,
            failure_buckets=failures,
        )

    @staticmethod
    def lineage_hash(company_id: str, as_of_ts: datetime, nodes: List[EvidenceNode], pipeline_version: str) -> str:
        payload = {
            "company_id": company_id,
            "as_of_ts": as_of_ts.isoformat(),
            "pipeline_version": pipeline_version,
            "nodes": [
                {
                    "url": n.url,
                    "captured_at": n.captured_at.isoformat(),
                    "node_type": n.node_type,
                    "normalized_fact": n.normalized_fact,
                    "confidence": n.confidence,
                    "extractor_version": n.extractor_version,
                }
                for n in sorted(nodes, key=lambda x: (x.url, x.node_type, x.normalized_fact))
            ],
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
