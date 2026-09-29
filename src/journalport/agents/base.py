"""Minimal provider-neutral extraction interface."""

from __future__ import annotations

from typing import Protocol

from journalport.guidelines.models import CandidateRule, EvidenceUnit


class AgentExtractor(Protocol):
    provider: str
    model: str
    version: str

    def extract_requirements(
        self, evidence_units: tuple[EvidenceUnit, ...]
    ) -> tuple[CandidateRule, ...]: ...
