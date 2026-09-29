"""Conservative evidence-only extractor used for fixtures and offline replay."""

from __future__ import annotations

import re

from journalport.profiles.models import JSONValue

from .hashing import canonical_hash
from .models import CandidateRule, EvidenceUnit

EXTRACTOR_VERSION = "1.0.0"


class DeterministicEvidenceExtractor:
    provider = "journalport-deterministic-fixture"
    model = "regex-evidence-v1"
    version = EXTRACTOR_VERSION

    def _rule(
        self,
        evidence: EvidenceUnit,
        rule_id: str,
        category: str,
        target: str,
        operator: str,
        value: JSONValue,
        unit: str | None,
        *,
        confidence: str = "HIGH",
        applicability: str = "ALWAYS",
        condition: str | None = None,
    ) -> CandidateRule:
        identity = canonical_hash([rule_id, value, evidence.evidence_id])
        return CandidateRule(
            "1.0.0",
            f"candidate:{identity.split(':', 1)[1][:24]}",
            rule_id,
            category,
            target,
            operator,
            value,
            unit,
            target if target in {"abstract", "title", "references", "main_text"} else "EXPLICIT",
            applicability,
            condition,
            confidence == "HIGH",
            category in {"LIMIT", "FILE", "STATEMENT", "IDENTITY"},
            "BLOCKING" if category != "REFERENCE" else "WARNING",
            "NONE" if category == "IDENTITY" else "AUTHOR_APPROVAL_REQUIRED",
            (evidence.evidence_id,),
            confidence,
            "Direct deterministic interpretation of cited official evidence.",
        )

    def extract_requirements(
        self, evidence_units: tuple[EvidenceUnit, ...]
    ) -> tuple[CandidateRule, ...]:
        rules: list[CandidateRule] = []
        for evidence in evidence_units:
            if evidence.authority_level > 5:
                continue
            text = evidence.evidence_text
            lower = text.lower()
            if "article limits" in lower:
                rules.append(
                    self._rule(
                        evidence,
                        "identity.article_type",
                        "IDENTITY",
                        "article_type",
                        "EQ",
                        "Article",
                        None,
                    )
                )
            patterns = (
                (r"title\s+(\d[\d,]*)\s+words", "title.max_words", "LIMIT", "title", "words"),
                (
                    r"abstract\s+(\d[\d,]*)\s+words",
                    "abstract.max_words",
                    "LIMIT",
                    "abstract",
                    "words",
                ),
                (
                    r"main text(?: ideally)?\s+(\d[\d,]*)\s+words",
                    "main_text.max_words",
                    "LIMIT",
                    "main_text",
                    "words",
                ),
                (
                    r"display items(?: up to)?\s+(\d[\d,]*)",
                    "display_items.max_count",
                    "FIGURE",
                    "figures_and_tables",
                    "items",
                ),
            )
            for pattern, rule_id, category, target, unit in patterns:
                match = re.search(pattern, lower)
                if match:
                    rules.append(
                        self._rule(
                            evidence,
                            rule_id,
                            category,
                            target,
                            "LTE",
                            int(match.group(1).replace(",", "")),
                            unit,
                        )
                    )
            if "include" in lower and "cover letter" in lower:
                rules.append(
                    self._rule(
                        evidence,
                        "cover_letter.required",
                        "FILE",
                        "cover_letter",
                        "EXISTS",
                        True,
                        None,
                    )
                )
            if (
                "supplementary information optional" in lower
                or "optional supplementary information" in lower
            ):
                rules.append(
                    self._rule(
                        evidence,
                        "supplement.allowed",
                        "FILE",
                        "supplementary_information",
                        "EXISTS",
                        "OPTIONAL",
                        None,
                    )
                )
            extended = re.search(r"up to\s+(\d+)\s+extended data", lower)
            if extended:
                rules.append(
                    self._rule(
                        evidence,
                        "extended_data.max_count",
                        "FIGURE",
                        "extended_data",
                        "LTE",
                        int(extended.group(1)),
                        "items",
                        applicability="CONDITIONAL",
                        condition="If Extended Data are used",
                    )
                )
            statement_patterns = (
                (
                    "competing-interest",
                    "statements.competing_interests.required",
                    "competing_interests",
                ),
                (
                    "data-availability statement",
                    "statements.data_availability.required",
                    "data_availability",
                ),
                (
                    "author-contribution statement",
                    "statements.author_contributions.required",
                    "author_contributions",
                ),
            )
            for token, rule_id, target in statement_patterns:
                if token in lower and ("requires" in lower or "must include" in lower):
                    rules.append(
                        self._rule(evidence, rule_id, "STATEMENT", target, "EXISTS", True, None)
                    )
        unique = {item.candidate_rule_id: item for item in rules}
        return tuple(sorted(unique.values(), key=lambda item: item.candidate_rule_id))
