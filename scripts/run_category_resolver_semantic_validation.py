"""Run frozen semantic validation matrix against live catalog resolver."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path

from app.category_resolver.catalog_snapshot import build_resolver_catalog_snapshot
from app.category_resolver.constants import RESOLVER_VERSION
from app.category_resolver.engine import CategoryResolverEngine
from app.category_resolver.intent_semantics import IntentAction, interpret_intent
from app.db.base import Base  # noqa: F401
from app.db.session import async_session_maker
from app.repositories.category_alias_repository import CategoryAliasRepository
from app.repositories.category_moderation_rule_repository import CategoryModerationRuleRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.category_routing_rule_repository import CategoryRoutingRuleRepository
from app.repositories.vehicle_repository import VehicleAliasRepository
from app.seeds.transport_canonical import RETIRED_TRANSPORT_SLUGS
from app.services.category_routing_service import CategoryRoutingService
from app.services.category_snapshot import CategorySnapshotProvider

MATRIX_PATH = Path(__file__).resolve().parents[1] / "app" / "category_resolver" / "semantic_validation_v1.json"


@dataclass
class CaseResult:
    case_id: str
    ok_action: bool
    ok_category: bool
    ok_status: bool
    predicted_action: str
    predicted_slug: str | None
    predicted_status: str
    expected_action: str
    acceptable_slugs: list[str]
    expected_status: list[str]
    error_tags: list[str] = field(default_factory=list)
    top2_margin: float | None = None


@dataclass
class MatrixReport:
    label: str
    total: int
    action_accuracy: float
    category_accuracy: float
    suggested_rate: float
    ambiguous_rate: float
    no_match_rate: float
    retired_violations: int
    failures: list[CaseResult] = field(default_factory=list)


async def run_matrix(label: str = "run") -> MatrixReport:
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    cases = matrix["cases"]

    async with async_session_maker() as session:
        catalog = await build_resolver_catalog_snapshot(
            session,
            CategoryRepository(session),
            CategoryAliasRepository(session),
            CategoryRoutingRuleRepository(session),
            CategoryModerationRuleRepository(session),
            VehicleAliasRepository(session),
            locale="ru",
        )
        provider = CategorySnapshotProvider(
            CategoryRepository(session),
            CategoryAliasRepository(session),
            CategoryRoutingRuleRepository(session),
            CategoryModerationRuleRepository(session),
            VehicleAliasRepository(session),
            locale="ru",
        )
        engine = CategoryResolverEngine(CategoryRoutingService(provider))

        results: list[CaseResult] = []
        for case in cases:
            visual = tuple(case.get("visual_concepts") or [])
            sem = interpret_intent(case["intent_text"])
            out = await engine.resolve(
                raw_intent_text=case["intent_text"],
                catalog=catalog,
                visual_concepts=visual,
            )
            acceptable = case.get("acceptable_slugs") or []
            if case.get("expected_category_slug"):
                acceptable = list({case["expected_category_slug"], *acceptable})
            exp_status = case.get("expected_status") or ["suggested", "ambiguous"]
            ok_action = sem.action.value == case["expected_action"]
            slug = out.suggested_slug
            ok_category = slug in acceptable if acceptable else slug is None
            ok_status = out.status.value in exp_status
            tags: list[str] = []
            if not ok_action:
                tags.append("ACTION_ERROR")
            if not ok_category:
                tags.append(_classify_category_error(case, sem.action.value, slug))
            if slug and slug in RETIRED_TRANSPORT_SLUGS:
                tags.append("RETIRED_VIOLATION")
            margin = None
            scores = out.evidence_summary.get("scores") or []
            if len(scores) >= 2:
                margin = float(scores[0]["score"]) - float(scores[1]["score"])
            results.append(
                CaseResult(
                    case_id=case["case_id"],
                    ok_action=ok_action,
                    ok_category=ok_category,
                    ok_status=ok_status,
                    predicted_action=sem.action.value,
                    predicted_slug=slug,
                    predicted_status=out.status.value,
                    expected_action=case["expected_action"],
                    acceptable_slugs=acceptable,
                    expected_status=exp_status,
                    error_tags=tags,
                    top2_margin=margin,
                )
            )

    n = len(results)
    failures = [r for r in results if not (r.ok_action and r.ok_category and r.ok_status)]
    return MatrixReport(
        label=label,
        total=n,
        action_accuracy=sum(r.ok_action for r in results) / n,
        category_accuracy=sum(r.ok_category for r in results) / n,
        suggested_rate=sum(r.predicted_status == "suggested" for r in results) / n,
        ambiguous_rate=sum(r.predicted_status == "ambiguous" for r in results) / n,
        no_match_rate=sum(r.predicted_status == "no_match" for r in results) / n,
        retired_violations=sum("RETIRED_VIOLATION" in r.error_tags for r in results),
        failures=failures,
    )


def _classify_category_error(case: dict, action: str, slug: str | None) -> str:
    rationale = case.get("rationale_tag", "")
    if action != case["expected_action"]:
        return "ACTION_ERROR"
    if slug is None:
        return "CATALOG_RETRIEVAL_ERROR"
    if "service" in rationale and slug.startswith("transport-"):
        return "RANKING_ERROR"
    if "job" in rationale:
        return "RANKING_ERROR"
    if "visual" in rationale:
        return "VISUAL_OVERRIDE_ERROR"
    return "RANKING_ERROR"


def report_to_dict(r: MatrixReport) -> dict:
    return {
        "label": r.label,
        "resolver_version": RESOLVER_VERSION,
        "total": r.total,
        "action_accuracy": round(r.action_accuracy, 4),
        "category_accuracy": round(r.category_accuracy, 4),
        "suggested_rate": round(r.suggested_rate, 4),
        "ambiguous_rate": round(r.ambiguous_rate, 4),
        "no_match_rate": round(r.no_match_rate, 4),
        "retired_violations": r.retired_violations,
        "failures": [
            {
                "case_id": f.case_id,
                "predicted_action": f.predicted_action,
                "expected_action": f.expected_action,
                "predicted_slug": f.predicted_slug,
                "acceptable_slugs": f.acceptable_slugs,
                "predicted_status": f.predicted_status,
                "expected_status": f.expected_status,
                "error_tags": f.error_tags,
                "top2_margin": f.top2_margin,
            }
            for f in r.failures
        ],
    }


async def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="baseline")
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    report = await run_matrix(args.label)
    data = report_to_dict(report)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    if args.out:
        Path(args.out).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
