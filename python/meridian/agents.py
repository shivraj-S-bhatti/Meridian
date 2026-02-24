from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

from meridian.types import EvidenceEdge, EvidenceNode


@dataclass(frozen=True)
class AgentVersions:
    claim: str = "claim-agent-v1"
    reality: str = "reality-agent-v1"
    novelty: str = "novelty-agent-v1"
    skeptic: str = "skeptic-agent-v1"
    portfolio: str = "portfolio-agent-v1"


class ClaimAgent:
    def run(self, nodes: List[EvidenceNode]) -> List[EvidenceNode]:
        return [n for n in nodes if n.node_type == "claim"]


class RealityAgent:
    _NEG_HINTS = ("delay", "layoff", "inventory", "weak", "shortage")
    _POS_HINTS = ("hiring", "demand", "expansion", "capacity", "shipment")

    def score(self, nodes: List[EvidenceNode]) -> float:
        if not nodes:
            return 0.0

        score = 0.0
        for node in nodes:
            text = node.normalized_fact.lower()
            for token in self._NEG_HINTS:
                if token in text:
                    score -= 0.35
            for token in self._POS_HINTS:
                if token in text:
                    score += 0.35
        return max(-1.0, min(1.0, score / max(1, len(nodes))))


class NoveltyAgent:
    def contradiction_strength(self, claim_nodes: List[EvidenceNode], reality_score: float) -> float:
        claim_bias = 0.0
        if claim_nodes:
            positives = sum(1 for c in claim_nodes if any(t in c.normalized_fact.lower() for t in ("growth", "upside", "strong", "beat")))
            negatives = sum(1 for c in claim_nodes if any(t in c.normalized_fact.lower() for t in ("risk", "soft", "pressure", "miss")))
            claim_bias = (positives - negatives) / max(1, len(claim_nodes))

        return min(1.0, abs(claim_bias - reality_score))


class SkepticAgent:
    def accept(self, claim_nodes: List[EvidenceNode], reality_nodes: List[EvidenceNode], as_of_ts: datetime) -> tuple[bool, List[str]]:
        invalid_if: List[str] = []

        if len(claim_nodes) < 1:
            invalid_if.append("insufficient_claim_coverage")
        if len(reality_nodes) < 2:
            invalid_if.append("insufficient_reality_coverage")

        stale_count = 0
        now = as_of_ts if as_of_ts.tzinfo else as_of_ts.replace(tzinfo=timezone.utc)
        for n in claim_nodes + reality_nodes:
            age_days = (now - n.captured_at).days
            if age_days > 45:
                stale_count += 1
        if stale_count > max(1, (len(claim_nodes) + len(reality_nodes)) // 2):
            invalid_if.append("evidence_stale")

        return (len(invalid_if) == 0, invalid_if)


class PortfolioAgent:
    def score(
        self,
        contradiction_strength: float,
        reality_score: float,
        evidence_count: int,
        horizon_days: int,
    ) -> tuple[float, float, float]:
        direction = -1.0 if reality_score < 0 else 1.0
        magnitude = min(1.0, contradiction_strength * (0.5 + min(1.0, evidence_count / 10.0)))
        score = max(-100.0, min(100.0, direction * magnitude * 100.0))

        uncertainty = max(0.1, min(0.95, 0.75 - (evidence_count / 40.0) + (1.0 - contradiction_strength) * 0.2))
        decay_half_life_days = max(5.0, float(horizon_days) * (0.5 + contradiction_strength))
        return score, uncertainty, decay_half_life_days


def build_edges(nodes: List[EvidenceNode]) -> List[EvidenceEdge]:
    edges: List[EvidenceEdge] = []
    claim_idxs = [i for i, n in enumerate(nodes) if n.node_type == "claim"]
    reality_idxs = [i for i, n in enumerate(nodes) if n.node_type == "reality"]

    for c in claim_idxs:
        for r in reality_idxs:
            rel = "contradicts"
            edges.append(EvidenceEdge(source_idx=c, target_idx=r, relation=rel))

    for i in range(1, len(nodes)):
        edges.append(EvidenceEdge(source_idx=i - 1, target_idx=i, relation="derived_from"))

    return edges
