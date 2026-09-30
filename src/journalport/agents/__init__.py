"""Provider-neutral agent contracts; deterministic core does not depend on an agent SDK."""

from .transfer import (
    AgentProposal,
    DisclosureEntry,
    ScientificDiffReport,
    TransferSession,
    append_disclosure,
    build_proposal,
    classify_finding,
    load_session,
    minimize_abstract_context,
    save_session,
    scientific_diff,
    verification_allows_packaging,
)

__all__ = [
    "AgentProposal",
    "DisclosureEntry",
    "ScientificDiffReport",
    "TransferSession",
    "append_disclosure",
    "build_proposal",
    "classify_finding",
    "load_session",
    "minimize_abstract_context",
    "save_session",
    "scientific_diff",
    "verification_allows_packaging",
]
