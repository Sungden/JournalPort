"""Offline audit, transformation, and independent verification CLI."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from journalport import __version__
from journalport.benchmark import reproduce_guideline_extraction
from journalport.compliance.engine import audit_manuscript
from journalport.compliance.models import compliance_report_from_dict
from journalport.compliance.reports import render_html, render_json
from journalport.compliance.traces import evaluation_trace
from journalport.guidelines.discovery import discover_sources
from journalport.guidelines.retrieval import retrieve_source
from journalport.guidelines.workflow import load_snapshots, refresh_draft
from journalport.manuscript.model import CanonicalManuscript
from journalport.manuscript.parser_docx import parse_docx
from journalport.manuscript.parser_latex import parse_latex
from journalport.package.builder import build_package
from journalport.package.models import manifest_from_dict, package_plan_from_dict
from journalport.package.planner import create_package_plan
from journalport.package.reports import render_html as render_package_html
from journalport.package.reports import render_json as render_package_json
from journalport.package.verify import verify_package
from journalport.profiles.loader import ProfileRegistry
from journalport.profiles.models import ResolvedJournalProfile
from journalport.profiles.resolver import resolve_profile
from journalport.transform.approvals import proposed_content_hash
from journalport.transform.executor import execute_plan
from journalport.transform.models import (
    ActionLog,
    Approval,
    CandidateManifest,
    transformation_plan_from_dict,
)
from journalport.transform.planner import create_plan
from journalport.verify.models import verification_report_from_dict
from journalport.verify.reports import render_html as render_verification_html
from journalport.verify.reports import render_json as render_verification_json
from journalport.verify.verifier import verify_candidate


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="journalport")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    full = commands.add_parser(
        "full-format", help="profile-driven DOCX structure, layout and verification"
    )
    full.add_argument("manuscript", type=Path)
    full.add_argument("--journal", required=True)
    full.add_argument("--article-type", default="article")
    full.add_argument(
        "--stage",
        choices=("INITIAL_SUBMISSION", "REVISION", "FINAL_SUBMISSION", "ACCEPTED"),
        required=True,
    )
    full.add_argument("--profile-version", default="1.3.2")
    full.add_argument("--profiles", type=Path, default=_default_profiles_path())
    full.add_argument("--output", type=Path, required=True)
    full.add_argument("--plan-only", action="store_true")
    full.add_argument("--reviewed-plan", type=Path)
    full.add_argument("--render-executable")
    full.add_argument("--supplement", type=Path, action="append", default=[])
    full.add_argument(
        "--confirm-condition",
        metavar="RULE_ID",
        action="append",
        default=[],
        help="author-confirmed applicability of a verified conditional ordering rule; repeatable",
    )
    rewrite = commands.add_parser(
        "nature-rewrite", help="model-assisted full scientific rewrite into a Nature Article draft"
    )
    rewrite.add_argument("manuscript", type=Path)
    rewrite.add_argument(
        "--journal",
        choices=(
            "nature-communications",
            "nature-computational-science",
            "nature-machine-intelligence",
        ),
        required=True,
    )
    rewrite.add_argument("--output", type=Path, required=True)
    rewrite.add_argument("--backend", choices=("http", "codex"), default="http")
    rewrite.add_argument("--base-url", help="OpenAI-compatible model base URL")
    rewrite.add_argument("--codex-executable", default="codex")
    rewrite.add_argument("--model")
    rewrite.add_argument("--review-model")
    rewrite.add_argument("--max-attempts", type=int, default=3)
    rewrite.add_argument("--render-executable")
    rewrite.add_argument("--api-key-env", default="OPENAI_API_KEY")
    rewrite.add_argument(
        "--allow-remote", action="store_true", help="permit sending manuscript to this remote model"
    )
    structure = commands.add_parser(
        "restructure", help="reviewed IEEE-to-NC DOCX section migration"
    )
    structure.add_argument("manuscript", type=Path)
    structure.add_argument("--recipe", choices=("ieee-to-nature-communications",), required=True)
    structure.add_argument("--output", type=Path, required=True)
    structure.add_argument("--plan-only", action="store_true")
    structure.add_argument("--reviewed-plan", type=Path)
    audit = commands.add_parser("audit", help="read-only deterministic compliance audit")
    audit.add_argument("manuscript", type=Path)
    audit.add_argument("--journal", required=True)
    audit.add_argument("--article-type", default="article")
    audit.add_argument("--profile-version", default="1.1.0")
    audit.add_argument("--profiles", type=Path, default=_default_profiles_path())
    audit.add_argument("--output", type=Path, default=Path("journalport-audit"))
    audit.add_argument("--format", choices=("json", "html", "both"), default="both")
    plan = commands.add_parser("plan", help="create a dry-run transformation plan")
    plan.add_argument("manuscript", type=Path)
    plan.add_argument("--journal", required=True)
    plan.add_argument("--article-type", default="article")
    plan.add_argument("--profile-version", default="1.1.0")
    plan.add_argument("--profiles", type=Path, default=_default_profiles_path())
    plan.add_argument("--output", type=Path, default=Path("journalport-plan"))
    approve = commands.add_parser("approve", help="bind explicit approval to a local payload")
    approve.add_argument("plan", type=Path)
    approve.add_argument("--action", required=True)
    approve.add_argument("--payload", type=Path, required=True)
    approve.add_argument("--approved-by", required=True)
    approve.add_argument("--output", type=Path, required=True)
    apply = commands.add_parser("apply", help="apply only supported safe actions")
    apply.add_argument("plan", type=Path)
    apply.add_argument("--profiles", type=Path, default=_default_profiles_path())
    apply.add_argument("--output", type=Path, required=True)
    apply.add_argument("--approval", type=Path, action="append", default=[])
    apply.add_argument("--payload", action="append", default=[], metavar="ACTION_ID=FILE")
    verify = commands.add_parser("verify", help="independently verify a transformed candidate")
    verify.add_argument("--source", type=Path, required=True)
    verify.add_argument("--candidate", type=Path, required=True)
    verify.add_argument("--plan", type=Path, required=True)
    verify.add_argument("--log", type=Path, required=True)
    verify.add_argument("--manifest", type=Path, required=True)
    verify.add_argument("--report-before", type=Path, required=True)
    verify.add_argument("--profiles", type=Path, default=_default_profiles_path())
    verify.add_argument("--output", type=Path, default=Path("journalport-verification"))
    package = commands.add_parser("package", help="plan, build, or verify a submission package")
    package_commands = package.add_subparsers(dest="package_command", required=True)
    package_plan = package_commands.add_parser("plan")
    package_plan.add_argument("--candidate", type=Path, required=True)
    package_plan.add_argument("--verification-report", type=Path, required=True)
    package_plan.add_argument("--compliance-report", type=Path, required=True)
    package_plan.add_argument("--journal", required=True)
    package_plan.add_argument("--article-type", default="article")
    package_plan.add_argument("--profile-version", default="1.1.0")
    package_plan.add_argument("--profiles", type=Path, default=_default_profiles_path())
    package_plan.add_argument("--artifact", type=Path, action="append", default=[])
    package_plan.add_argument("--output", type=Path, default=Path("package-plan"))
    package_build = package_commands.add_parser("build")
    package_build.add_argument("plan", type=Path)
    package_build.add_argument("--output", type=Path, required=True)
    package_build.add_argument("--no-zip", action="store_true")
    package_verify = package_commands.add_parser("verify")
    package_verify.add_argument("package_root", type=Path)
    package_verify.add_argument("--profiles", type=Path, default=_default_profiles_path())
    profile_command = commands.add_parser("profile", help="discover and draft journal guidelines")
    profile_commands = profile_command.add_subparsers(dest="profile_command", required=True)
    discover = profile_commands.add_parser("discover")
    discover.add_argument("--journal", required=True)
    discover.add_argument("--article-type", default="article")
    discover.add_argument("--output", type=Path, default=Path("discovered_sources.json"))
    refresh = profile_commands.add_parser("refresh-draft")
    refresh.add_argument("--journal", required=True)
    refresh.add_argument("--article-type", default="article")
    refresh.add_argument("--snapshot", type=Path)
    refresh.add_argument("--profiles", type=Path, default=_default_profiles_path())
    refresh.add_argument("--profile-version", default="1.1.0")
    refresh.add_argument("--cache", type=Path, default=Path(".journalport-cache/guidelines"))
    refresh.add_argument("--output", type=Path, default=Path("profile_drafts"))
    replay = profile_commands.add_parser("extract-from-snapshot")
    replay.add_argument("snapshot", type=Path)
    replay.add_argument("--journal", required=True)
    replay.add_argument("--article-type", default="article")
    replay.add_argument("--profiles", type=Path, default=_default_profiles_path())
    replay.add_argument("--profile-version", default="1.1.0")
    replay.add_argument("--output", type=Path, default=Path("profile_drafts"))
    benchmark = commands.add_parser("benchmark", help="reproduce a frozen benchmark snapshot")
    benchmark_commands = benchmark.add_subparsers(dest="benchmark_command", required=True)
    extraction_benchmark = benchmark_commands.add_parser("guideline-extraction")
    extraction_benchmark.add_argument("--snapshot", type=Path)
    extraction_benchmark.add_argument("--output", type=Path)
    return parser


def _default_profiles_path() -> Path:
    checkout = Path("journal_profiles")
    bundled = Path(__file__).resolve().parent / "data" / "journal_profiles"
    return checkout if checkout.is_dir() else bundled


def _resolve_profile_version(
    profiles: Path, slug: str, article_type: str, version: str
) -> ResolvedJournalProfile:
    """Resolve the requested article profile through its immutable pinned parents."""
    registry = ProfileRegistry.from_directory(profiles)
    publisher = "publisher:nature-portfolio"
    journal = f"journal:{slug}"
    article = f"article-type:{slug}/{article_type}"
    article_profile = registry.get(article, version)
    journal_refs = [item for item in article_profile.parents if item.profile_id == journal]
    if len(journal_refs) != 1:
        raise ValueError("article profile must pin exactly one requested journal parent")
    journal_profile = registry.get(journal, journal_refs[0].profile_version)
    publisher_refs = [item for item in journal_profile.parents if item.profile_id == publisher]
    if len(publisher_refs) != 1:
        raise ValueError("journal profile must pin exactly one Nature Portfolio parent")
    pins = {
        publisher: publisher_refs[0].profile_version,
        journal: journal_refs[0].profile_version,
        article: version,
    }
    return resolve_profile(registry, publisher, journal, article, pins)


def _audit(args: argparse.Namespace) -> int:
    manuscript_path: Path = args.manuscript
    if manuscript_path.suffix.lower() == ".docx":
        manuscript = parse_docx(manuscript_path)
    elif manuscript_path.suffix.lower() == ".tex":
        manuscript = parse_latex(manuscript_path)
    else:
        raise SystemExit("audit supports .docx and .tex inputs")
    slug = str(args.journal)
    version = str(args.profile_version)
    profile = _resolve_profile_version(args.profiles, slug, str(args.article_type), version)
    report = audit_manuscript(manuscript, profile)
    output: Path = args.output
    output.mkdir(parents=True, exist_ok=True)
    if args.format in {"json", "both"}:
        (output / "compliance_report.json").write_text(render_json(report), encoding="utf-8")
        (output / "evaluation_trace.json").write_text(
            json.dumps(evaluation_trace(report), ensure_ascii=False, sort_keys=True, indent=2)
            + "\n",
            encoding="utf-8",
        )
    if args.format in {"html", "both"}:
        (output / "compliance_report.html").write_text(render_html(report), encoding="utf-8")
    return 0


def _parse_manuscript(path: Path) -> CanonicalManuscript:
    if path.suffix.lower() == ".docx":
        return parse_docx(path)
    if path.suffix.lower() == ".tex":
        return parse_latex(path)
    raise SystemExit("commands support .docx and .tex inputs")


def _plan(args: argparse.Namespace) -> int:
    manuscript = _parse_manuscript(args.manuscript)
    slug = str(args.journal)
    version = str(args.profile_version)
    profile = _resolve_profile_version(args.profiles, slug, str(args.article_type), version)
    report = audit_manuscript(manuscript, profile)
    plan = create_plan(manuscript, profile, report, args.manuscript)
    output: Path = args.output
    output.mkdir(parents=True, exist_ok=True)
    (output / "transformation_plan.json").write_text(
        json.dumps(plan.to_dict(), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / "compliance_report.json").write_text(render_json(report), encoding="utf-8")
    return 0


def _apply(args: argparse.Namespace) -> int:
    plan_path: Path = args.plan
    plan = transformation_plan_from_dict(json.loads(plan_path.read_text(encoding="utf-8")))
    report_path = plan_path.with_name("compliance_report.json")
    report = compliance_report_from_dict(json.loads(report_path.read_text(encoding="utf-8")))
    source = Path(plan.input_artifact_path)
    manuscript = _parse_manuscript(source)
    article = plan.profile_id
    slug = article.removeprefix("article-type:").rsplit("/", 1)[0]
    profile = _resolve_profile_version(
        args.profiles, slug, article.rsplit("/", 1)[1], plan.profile_version
    )
    approvals = tuple(
        Approval(**json.loads(path.read_text(encoding="utf-8"))) for path in args.approval
    )
    payloads: dict[str, str] = {}
    for specification in args.payload:
        action_id, separator, filename = specification.partition("=")
        if not separator or not action_id or not filename:
            raise ValueError("payload must use ACTION_ID=FILE")
        payloads[action_id] = Path(filename).read_text(encoding="utf-8")
    execute_plan(
        plan,
        manuscript,
        profile,
        report,
        args.output,
        approvals=approvals,
        payloads=payloads,
    )
    return 0


def _approve(args: argparse.Namespace) -> int:
    plan = transformation_plan_from_dict(json.loads(args.plan.read_text(encoding="utf-8")))
    matches = [item for item in plan.actions if item.action_id == args.action]
    if len(matches) != 1:
        raise ValueError("approval action is missing or ambiguous")
    action = matches[0]
    if not action.requires_approval or action.transformation_status != "SUPPORTED":
        raise ValueError("action is not eligible for executable approval")
    payload = args.payload.read_text(encoding="utf-8")
    if not payload.strip():
        raise ValueError("approved payload is empty")
    approval = Approval(
        "1.0.0",
        action.action_id,
        plan.plan_hash,
        proposed_content_hash(action, payload),
        "APPROVED",
        args.approved_by,
        datetime.now(UTC).isoformat(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(asdict(approval), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    os.chmod(args.output, 0o600)
    return 0


def _verify(args: argparse.Namespace) -> int:
    plan = transformation_plan_from_dict(json.loads(args.plan.read_text(encoding="utf-8")))
    before = compliance_report_from_dict(json.loads(args.report_before.read_text(encoding="utf-8")))
    log_value = json.loads(args.log.read_text(encoding="utf-8"))
    logs = tuple(
        ActionLog(
            **(
                item
                | {
                    "input_object_ids": tuple(item["input_object_ids"]),
                    "errors": tuple(item["errors"]),
                    "warnings": tuple(item["warnings"]),
                }
            )
        )
        for item in log_value["entries"]
    )
    manifest_value = json.loads(args.manifest.read_text(encoding="utf-8"))
    manifest = CandidateManifest(
        **(
            manifest_value
            | {
                "applied_action_ids": tuple(manifest_value["applied_action_ids"]),
                "pending_manual_action_ids": tuple(manifest_value["pending_manual_action_ids"]),
                "failed_action_ids": tuple(manifest_value["failed_action_ids"]),
            }
        )
    )
    original = _parse_manuscript(args.source)
    article = plan.profile_id
    slug = article.removeprefix("article-type:").rsplit("/", 1)[0]
    profile = _resolve_profile_version(
        args.profiles, slug, article.rsplit("/", 1)[1], plan.profile_version
    )
    report, after, delta = verify_candidate(
        source_path=args.source,
        candidate_path=args.candidate,
        original_manuscript=original,
        profile=profile,
        before_report=before,
        plan=plan,
        logs=logs,
        manifest=manifest,
    )
    output: Path = args.output
    output.mkdir(parents=True, exist_ok=True)
    (output / "verification_report.json").write_text(
        render_verification_json(report), encoding="utf-8"
    )
    (output / "post_transform_compliance_report.json").write_text(
        render_json(after), encoding="utf-8"
    )
    (output / "compliance_delta.json").write_text(render_verification_json(delta), encoding="utf-8")
    (output / "verification_report.html").write_text(
        render_verification_html(report, delta), encoding="utf-8"
    )
    return 0 if report.transformation_verification_status == "VERIFIED_CANDIDATE" else 2


def _resolve_cli_profile(
    profiles: Path, slug: str, article_type: str, version: str
) -> ResolvedJournalProfile:
    return _resolve_profile_version(profiles, slug, article_type, version)


def _package_plan(args: argparse.Namespace) -> int:
    verification = verification_report_from_dict(
        json.loads(args.verification_report.read_text(encoding="utf-8"))
    )
    compliance = compliance_report_from_dict(
        json.loads(args.compliance_report.read_text(encoding="utf-8"))
    )
    profile = _resolve_cli_profile(
        args.profiles, str(args.journal), str(args.article_type), str(args.profile_version)
    )
    package_plan = create_package_plan(
        candidate=args.candidate,
        verification_report_path=args.verification_report,
        verification_report=verification,
        compliance_report_path=args.compliance_report,
        compliance_report=compliance,
        profile=profile,
        auxiliary_paths=tuple(args.artifact),
    )
    output: Path = args.output
    output.mkdir(parents=True, exist_ok=True)
    (output / "submission_package_plan.json").write_text(
        json.dumps(package_plan.to_dict(), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0 if package_plan.plan_status == "READY_TO_BUILD" else 2


def _package_build(args: argparse.Namespace) -> int:
    package_plan = package_plan_from_dict(json.loads(args.plan.read_text(encoding="utf-8")))
    build_package(package_plan, args.output, create_zip=not args.no_zip)
    return 0


def _package_verify(args: argparse.Namespace) -> int:
    root: Path = args.package_root
    manifest = manifest_from_dict(
        json.loads((root / "submission_manifest.json").read_text(encoding="utf-8"))
    )
    verification = verification_report_from_dict(
        json.loads((root / "metadata/verification_report.json").read_text(encoding="utf-8"))
    )
    compliance = compliance_report_from_dict(
        json.loads(
            (root / "metadata/post_transform_compliance_report.json").read_text(encoding="utf-8")
        )
    )
    profile = _resolve_cli_profile(
        args.profiles, manifest.target_journal, manifest.article_type, manifest.profile_version
    )
    _, report = verify_package(
        root,
        profile=profile,
        verification_report=verification,
        compliance_report=compliance,
    )
    (root / "package_readiness_report.json").write_text(
        render_package_json(report), encoding="utf-8"
    )
    (root / "package_readiness_report.html").write_text(
        render_package_html(report), encoding="utf-8"
    )
    return (
        0
        if report.final_package_status not in {"PACKAGE_BLOCKED", "PACKAGE_VERIFICATION_FAILED"}
        else 2
    )


def _journal_slug(value: str) -> str:
    return value.strip().lower().replace(" ", "-")


def _profile_discover(args: argparse.Namespace) -> int:
    sources = discover_sources(_journal_slug(args.journal), str(args.article_type))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {"schema_version": "1.0.0", "sources": [asdict(item) for item in sources]},
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0 if sources else 2


def _profile_refresh(args: argparse.Namespace, *, snapshot: Path | None = None) -> int:
    slug = _journal_slug(args.journal)
    snapshot_path = snapshot or getattr(args, "snapshot", None)
    if snapshot_path is not None:
        snapshots = load_snapshots(snapshot_path)
    else:
        sources = discover_sources(slug, str(args.article_type))
        snapshots = tuple(retrieve_source(item, args.cache) for item in sources)
    registry = ProfileRegistry.from_directory(args.profiles)
    curated = registry.get(f"article-type:{slug}/{args.article_type}", args.profile_version)
    refresh_draft(
        journal=slug,
        article_type=str(args.article_type),
        snapshots=snapshots,
        output_root=args.output,
        curated_profile=curated,
    )
    return 0


def _dispatch(args: argparse.Namespace) -> int:
    if args.command == "nature-rewrite":
        from journalport.agents.nature_rewrite import compatible_model
        from journalport.agents.rewrite_backend import codex_model
        from journalport.agents.rewrite_workflow import rewrite_manuscript

        if args.backend == "codex":
            writer = codex_model(args.codex_executable, args.model)
            reviewer = codex_model(args.codex_executable, args.review_model or args.model)
            privacy = "CODEX_HOSTED"
        else:
            if not args.base_url or not args.model:
                raise ValueError("HTTP backend requires --base-url and --model")
            writer = compatible_model(
                args.base_url,
                args.model,
                allow_remote=args.allow_remote,
                api_key_env=args.api_key_env,
            )
            reviewer = compatible_model(
                args.base_url,
                args.review_model or args.model,
                allow_remote=args.allow_remote,
                api_key_env=args.api_key_env,
            )
            privacy = "REMOTE_MODEL_AUTHORIZED" if args.allow_remote else "LOCAL_MODEL"
        result = rewrite_manuscript(
            args.manuscript,
            args.output,
            journal=args.journal,
            writer=writer,
            reviewer=reviewer,
            privacy_mode=privacy,
            max_attempts=args.max_attempts,
            render_executable=args.render_executable,
        )
        print(json.dumps(result, indent=2))
        return 0
    if args.command == "restructure":
        from journalport.transform.scientific_structure import run_scientific_structure

        result = run_scientific_structure(
            args.manuscript, args.output, plan_only=args.plan_only, reviewed_plan=args.reviewed_plan
        )
        print(json.dumps(result, indent=2))
        return 0
    if args.command == "full-format":
        from journalport.transform.full_format import run_full_format

        profile = _resolve_cli_profile(
            args.profiles, args.journal, args.article_type, args.profile_version
        )
        result = run_full_format(
            args.manuscript,
            args.output,
            ProfileRegistry.from_directory(args.profiles),
            profile,
            journal=args.journal,
            article_type=args.article_type,
            stage=args.stage,
            plan_only=args.plan_only,
            approved_plan=args.reviewed_plan,
            render_executable=args.render_executable,
            supplements=tuple(args.supplement),
            conditional_applicability=dict.fromkeys(args.confirm_condition, True),
        )
        print(json.dumps(result, indent=2))
        return 0 if result["status"] in {"PLAN_READY", "VERIFIED_CANDIDATE"} else 2
    if args.command == "audit":
        return _audit(args)
    if args.command == "plan":
        return _plan(args)
    if args.command == "approve":
        return _approve(args)
    if args.command == "apply":
        return _apply(args)
    if args.command == "verify":
        return _verify(args)
    if args.command == "package":
        if args.package_command == "plan":
            return _package_plan(args)
        if args.package_command == "build":
            return _package_build(args)
        if args.package_command == "verify":
            return _package_verify(args)
    if args.command == "profile":
        if args.profile_command == "discover":
            return _profile_discover(args)
        if args.profile_command == "refresh-draft":
            return _profile_refresh(args)
        if args.profile_command == "extract-from-snapshot":
            return _profile_refresh(args, snapshot=args.snapshot)
    if args.command == "benchmark" and args.benchmark_command == "guideline-extraction":
        value = reproduce_guideline_extraction(args.snapshot)
        rendered = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
        return 0
    raise SystemExit("unsupported command")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        return _dispatch(args)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        print(f"journalport: input or schema error: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
