from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import List

from meridian.agents import (
    AgentVersions,
    ClaimAgent,
    NoveltyAgent,
    PortfolioAgent,
    RealityAgent,
    SkepticAgent,
    build_edges,
)
from meridian.config import settings
from meridian.dom_analyzer import DOMAnalyzer
from meridian.storage import Storage
from meridian.types import EvidenceGraph, EvidenceNode, IPOScoreCard


def _seed_pages(company_id: str, as_of_ts: datetime) -> list[tuple[str, str]]:
    seed = hashlib.sha256(f"{company_id}:{as_of_ts.date().isoformat()}".encode("utf-8")).hexdigest()
    polarity = int(seed[:2], 16) % 2

    if polarity == 0:
        claim = (
            "Management expects strong demand and capacity expansion with resilient margin outlook over the next two quarters."
        )
        reality = (
            "Supplier channel commentary indicates shipment delays, inventory pressure, and softer near-term demand."
        )
    else:
        claim = (
            "Management guides conservatively and flags execution risk while maintaining liquidity discipline."
        )
        reality = (
            "Hiring acceleration and distribution expansion suggest demand momentum and improving fulfillment capacity."
        )

    pages = [
        (
            f"https://example.com/{company_id}/roadshow",
            f"<html><body><h1>{company_id} Roadshow</h1><p>{claim}</p></body></html>",
        ),
        (
            f"https://example.com/{company_id}/channel-check",
            f"<html><body><h1>{company_id} Channel</h1><p>{reality}</p></body></html>",
        ),
        (
            f"https://example.com/{company_id}/filing-note",
            f"<html><body><p>{claim} {reality}</p></body></html>",
        ),
    ]
    return pages


def ipo_dislocation_score(
    company_id: str,
    as_of_ts: datetime,
    horizon_days: int = 28,
    storage: Storage | None = None,
    dom_analyzer: DOMAnalyzer | None = None,
) -> IPOScoreCard:
    store = storage or Storage(settings.database_url)
    analyzer = dom_analyzer or DOMAnalyzer()

    if as_of_ts.tzinfo is None:
        as_of_ts = as_of_ts.replace(tzinfo=timezone.utc)

    nodes: List[EvidenceNode] = []
    for url, html in _seed_pages(company_id, as_of_ts):
        nodes.extend(analyzer.analyze(company_id=company_id, url=url, html=html, captured_at=as_of_ts))

    claim_agent = ClaimAgent()
    reality_agent = RealityAgent()
    novelty_agent = NoveltyAgent()
    skeptic_agent = SkepticAgent()
    portfolio_agent = PortfolioAgent()

    claim_nodes = claim_agent.run(nodes)
    reality_nodes = [n for n in nodes if n.node_type == "reality"]

    reality_score = reality_agent.score(reality_nodes)
    contradiction_strength = novelty_agent.contradiction_strength(claim_nodes=claim_nodes, reality_score=reality_score)
    accepted, invalid_if = skeptic_agent.accept(claim_nodes=claim_nodes, reality_nodes=reality_nodes, as_of_ts=as_of_ts)

    score, uncertainty, half_life = portfolio_agent.score(
        contradiction_strength=contradiction_strength,
        reality_score=reality_score,
        evidence_count=len(nodes),
        horizon_days=horizon_days,
    )

    if not accepted:
        score *= 0.45
        uncertainty = min(0.95, uncertainty + 0.2)

    graph_id = f"graph-{hashlib.md5(f'{company_id}:{as_of_ts.isoformat()}'.encode('utf-8')).hexdigest()[:12]}"
    lineage_hash = store.lineage_hash(
        company_id=company_id,
        as_of_ts=as_of_ts,
        nodes=nodes,
        pipeline_version=settings.pipeline_version,
    )

    graph = EvidenceGraph(
        graph_id=graph_id,
        company_id=company_id,
        as_of_ts=as_of_ts,
        nodes=nodes,
        edges=build_edges(nodes),
    )

    versions = AgentVersions()
    top_drivers = [
        f"contradiction_strength={contradiction_strength:.3f}",
        f"reality_score={reality_score:.3f}",
        f"agent_versions={versions.claim},{versions.reality},{versions.novelty},{versions.skeptic},{versions.portfolio}",
    ]

    card = IPOScoreCard(
        company_id=company_id,
        as_of_ts=as_of_ts,
        horizon_days=horizon_days,
        score=round(score, 4),
        uncertainty=round(uncertainty, 4),
        top_drivers=top_drivers,
        decay_half_life_days=round(half_life, 3),
        evidence_graph_id=graph_id,
        lineage_hash=lineage_hash,
        invalid_if=invalid_if,
    )

    store.save_graph(graph)
    store.save_facts(company_id, nodes)
    store.save_score_card(card)
    return card
