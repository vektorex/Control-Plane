import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.evaluation_lab import (
    EvaluationCase,
    EvaluationExperiment,
    EvaluationExperimentRun,
)
from backend.app.services.evaluation_lab.errors import ExperimentNotFoundError
from backend.app.services.evaluation_lab.schemas import EvaluationComparisonResponse

logger = logging.getLogger("evaluation_lab.comparator")


class EvaluationComparator:
    """
    Factual differential comparator between two evaluation experiments.
    Never produces subjective scores, winners, or rankings.
    Presents empirical deltas across cases, assertions, evaluators, usage, and cost.
    """

    @classmethod
    async def compare_experiments(
        cls,
        session: AsyncSession,
        experiment_a_id: UUID,
        experiment_b_id: UUID,
        workspace_id: Optional[UUID] = None,
    ) -> EvaluationComparisonResponse:
        # 1. Fetch both experiments
        exp_a_stmt = select(EvaluationExperiment).where(EvaluationExperiment.id == experiment_a_id)
        exp_b_stmt = select(EvaluationExperiment).where(EvaluationExperiment.id == experiment_b_id)
        if workspace_id:
            exp_a_stmt = exp_a_stmt.where(EvaluationExperiment.workspace_id == workspace_id)
            exp_b_stmt = exp_b_stmt.where(EvaluationExperiment.workspace_id == workspace_id)

        exp_a = (await session.execute(exp_a_stmt)).scalar_one_or_none()
        exp_b = (await session.execute(exp_b_stmt)).scalar_one_or_none()

        if not exp_a:
            raise ExperimentNotFoundError(f"Experiment A ({experiment_a_id}) not found")
        if not exp_b:
            raise ExperimentNotFoundError(f"Experiment B ({experiment_b_id}) not found")

        # 2. Fetch runs for both experiments
        runs_a_stmt = (
            select(EvaluationExperimentRun, EvaluationCase)
            .join(EvaluationCase, EvaluationExperimentRun.case_id == EvaluationCase.id)
            .where(EvaluationExperimentRun.experiment_id == exp_a.id)
        )
        runs_b_stmt = (
            select(EvaluationExperimentRun, EvaluationCase)
            .join(EvaluationCase, EvaluationExperimentRun.case_id == EvaluationCase.id)
            .where(EvaluationExperimentRun.experiment_id == exp_b.id)
        )

        rows_a = (await session.execute(runs_a_stmt)).all()
        rows_b = (await session.execute(runs_b_stmt)).all()

        map_a = {c.case_key: (r, c) for r, c in rows_a}
        map_b = {c.case_key: (r, c) for r, c in rows_b}

        # 3. Compute Summary Statistics for A and B
        def summarize(rows):
            runs = [r for r, _ in rows]
            total = len(runs)
            passed = sum(1 for r in runs if r.status == "passed")
            failed = sum(1 for r in runs if r.status == "failed")
            warning = sum(1 for r in runs if r.status == "warning")
            error = sum(1 for r in runs if r.status == "error")
            total_lat = sum(r.latency_ms or 0 for r in runs)
            avg_lat = round(total_lat / total, 1) if total > 0 else 0
            total_tok = sum((r.input_tokens or 0) + (r.output_tokens or 0) for r in runs)
            total_cost = round(sum(r.estimated_cost or 0.0 for r in runs), 6)
            return {
                "total_cases": total,
                "passed": passed,
                "failed": failed,
                "warning": warning,
                "error": error,
                "average_latency_ms": avg_lat,
                "total_tokens": total_tok,
                "estimated_cost": total_cost,
            }

        sum_a = summarize(rows_a)
        sum_b = summarize(rows_b)

        # 4. Factual Case Differences
        all_keys = sorted(set(map_a.keys()) | set(map_b.keys()))
        case_diffs = []
        assertion_diffs = []
        eval_diffs = []
        regressions = []

        for key in all_keys:
            entry_a = map_a.get(key)
            entry_b = map_b.get(key)

            status_a = entry_a[0].status if entry_a else "not_in_experiment_a"
            status_b = entry_b[0].status if entry_b else "not_in_experiment_b"

            if status_a != status_b:
                case_diffs.append({
                    "case_key": key,
                    "case_name": (entry_a[1].name if entry_a else entry_b[1].name),
                    "status_a": status_a,
                    "status_b": status_b,
                    "latency_a_ms": entry_a[0].latency_ms if entry_a else None,
                    "latency_b_ms": entry_b[0].latency_ms if entry_b else None,
                })

                # Check regression: previously passed in A, now failed or warning in B
                if status_a == "passed" and status_b in ("failed", "warning", "error"):
                    regressions.append({
                        "case_key": key,
                        "check": "case_status",
                        "baseline_result": status_a,
                        "candidate_result": status_b,
                        "reason": f"Case changed from '{status_a}' in Experiment A to '{status_b}' in Experiment B",
                    })

            # Compare assertion level results if both exist
            if entry_a and entry_b:
                res_a = entry_a[0].evaluation_result or {}
                res_b = entry_b[0].evaluation_result or {}

                asserts_a = {a.get("assertion_type", str(i)): a for i, a in enumerate(res_a.get("assertions", []))}
                asserts_b = {a.get("assertion_type", str(i)): a for i, a in enumerate(res_b.get("assertions", []))}

                for a_type in set(asserts_a.keys()) | set(asserts_b.keys()):
                    val_a = asserts_a.get(a_type, {})
                    val_b = asserts_b.get(a_type, {})
                    passed_a = val_a.get("passed")
                    passed_b = val_b.get("passed")

                    if passed_a != passed_b:
                        assertion_diffs.append({
                            "case_key": key,
                            "assertion_type": a_type,
                            "passed_a": passed_a,
                            "passed_b": passed_b,
                            "message_a": val_a.get("message"),
                            "message_b": val_b.get("message"),
                        })

                # Compare Evaluator findings (grounding, completeness, format, citation, safety)
                findings_a = {f.get("check_type", str(i)): f for i, f in enumerate(res_a.get("evaluation_findings", []))}
                findings_b = {f.get("check_type", str(i)): f for i, f in enumerate(res_b.get("evaluation_findings", []))}

                for f_type in set(findings_a.keys()) | set(findings_b.keys()):
                    find_a = findings_a.get(f_type, {})
                    find_b = findings_b.get(f_type, {})
                    pass_a = find_a.get("passed")
                    pass_b = find_b.get("passed")

                    if pass_a != pass_b:
                        eval_diffs.append({
                            "case_key": key,
                            "check_type": f_type,
                            "passed_a": pass_a,
                            "passed_b": pass_b,
                            "message_a": find_a.get("message"),
                            "message_b": find_b.get("message"),
                        })

        return EvaluationComparisonResponse(
            experiment_a={
                "id": str(exp_a.id),
                "name": exp_a.name,
                "target_type": exp_a.target_type,
                "target_configuration": exp_a.target_configuration,
                "summary": sum_a,
            },
            experiment_b={
                "id": str(exp_b.id),
                "name": exp_b.name,
                "target_type": exp_b.target_type,
                "target_configuration": exp_b.target_configuration,
                "summary": sum_b,
            },
            summary={
                "cases_difference": len(case_diffs),
                "assertions_difference": len(assertion_diffs),
                "evaluations_difference": len(eval_diffs),
                "regressions_count": len(regressions),
            },
            case_differences=case_diffs,
            assertion_differences=assertion_diffs,
            evaluation_differences=eval_diffs,
            latency_difference={
                "baseline_avg_ms": sum_a["average_latency_ms"],
                "candidate_avg_ms": sum_b["average_latency_ms"],
                "delta_ms": round(sum_b["average_latency_ms"] - sum_a["average_latency_ms"], 1),
            },
            token_difference={
                "baseline_tokens": sum_a["total_tokens"],
                "candidate_tokens": sum_b["total_tokens"],
                "delta_tokens": sum_b["total_tokens"] - sum_a["total_tokens"],
            },
            cost_difference={
                "baseline_cost": sum_a["estimated_cost"],
                "candidate_cost": sum_b["estimated_cost"],
                "delta_cost": round(sum_b["estimated_cost"] - sum_a["estimated_cost"], 6),
            },
            regressions=regressions,
        )
