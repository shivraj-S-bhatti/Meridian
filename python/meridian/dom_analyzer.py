from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import List

from bs4 import BeautifulSoup

from meridian.types import EvidenceNode


class DOMAnalyzer:
    """
    DOM extraction with deterministic fallback.
    LLM integration can be layered in behind this interface.
    """

    extractor_version = "dom-analyzer-v1"

    _CLAIM_PAT = re.compile(
        r"\b(expect|guidance|forecast|outlook|target|plan to|we believe)\b",
        re.IGNORECASE,
    )
    _REALITY_PAT = re.compile(
        r"\b(hiring|layoff|supplier|shipment|delay|demand|inventory|capacity)\b",
        re.IGNORECASE,
    )

    def analyze(self, company_id: str, url: str, html: str, captured_at: datetime | None = None) -> List[EvidenceNode]:
        ts = captured_at or datetime.now(timezone.utc)
        soup = BeautifulSoup(html, "html.parser")
        text = " ".join(soup.stripped_strings)

        nodes: List[EvidenceNode] = []

        for sentence in self._split_sentences(text):
            sentence = sentence.strip()
            if not sentence:
                continue

            if self._CLAIM_PAT.search(sentence):
                nodes.append(
                    EvidenceNode(
                        url=url,
                        captured_at=ts,
                        node_type="claim",
                        normalized_fact=sentence[:350],
                        confidence=0.72,
                        extractor_version=self.extractor_version,
                    )
                )

            if self._REALITY_PAT.search(sentence):
                nodes.append(
                    EvidenceNode(
                        url=url,
                        captured_at=ts,
                        node_type="reality",
                        normalized_fact=sentence[:350],
                        confidence=0.69,
                        extractor_version=self.extractor_version,
                    )
                )

        if not nodes:
            fallback = (text[:250] or "unstructured page with no extraction pattern match").strip()
            nodes.append(
                EvidenceNode(
                    url=url,
                    captured_at=ts,
                    node_type="meta",
                    normalized_fact=fallback,
                    confidence=0.40,
                    extractor_version=f"{self.extractor_version}-fallback",
                )
            )

        return nodes

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        return re.split(r"(?<=[.!?])\s+", text)
