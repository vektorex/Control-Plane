import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.db.models.evaluation_lab import (
    EvaluationCase,
    EvaluationExperiment,
    EvaluationExperimentRun,
)
from backend.app.services.evaluation_lab.errors import ExperimentNotFoundError
from backend.app.services.evaluation_lab.schemas import (
    RegressionCheckResponse,
    RegressionItem,
)
from backend.app.services.observability.events import TraceEventStatus, TraceEventType
from backend.app.services.observability.tracer import ExecutionTracer

logger = logging.getLogger("evaluation_lab.regression")


class RegressionDetector:
    """
    Deterministic regression detector comparing baseline experiment vs candidate experiment.
    Applies explicit diagnostic thresholds without subjective scoring.
    """

    @classmethod
    async def detect_regressions(
        cls,
        session: AsyncSession,
        baseline_experiment_id: UUID,
        candidate_experiment_id: UUID,
        workspace_id: Optional[UUID] = None,
    ) -> RegressionCheckResponse:
        """
        Evaluates deterministic regressions across cases, evaluators, latency, and cost.
        """
        stmt_base = select(EvaluationExperiment).where(EvaluationExperiment.id == baseline_experiment_id)
        stmt_cand = select(EvaluationExperiment).where(EvaluationExperiment.id == candidate_experiment_id)
        if workspace_id:
            stmt_base = stmt_base.where(EvaluationExperiment.workspace_id == workspace_id)
            stmt_cand = stmt_cand.where(EvaluationExperiment.workspace_id == workspace_id)

        base_exp = (await session.execute(stmt_base)).scalar_one_or_none()
        cand_exp = (await session.execute(stmt_cand)).scalar_one_or_none()

        if not base_exp:
            raise ExperimentNotFoundError(f"Baseline experiment {baseline_experiment_id} not found")
        if not cand_exp:
            raise ExperimentNotFoundError(f"Candidate experiment {candidate_experiment_id} not found")

        # Load runs with cases
        runs_b_stmt = (
            select(EvaluationExperimentRun, EvaluationCase)
            .join(EvaluationCase, EvaluationExperimentRun.case_id == EvaluationCase.id)
            .where(EvaluationExperimentRun.experiment_id == base_exp.id)
        )
        runs_c_stmt = (
            select(EvaluationExperimentRun, EvaluationCase)
            .join(EvaluationCase, EvaluationExperimentRun.case_id == EvaluationCase.id)
            .where(EvaluationExperimentRun.experiment_id == cand_exp.id)
        )

        rows_base = (await session.execute(runs_b_stmt)).all()
        rows_cand = (await session.execute(runs_c_stmt)).all()

        map_base = {c.case_key: (r, c) for r, c in rows_base}
        map_cand = {c.case_key: (r, c) for r, c in rows_cand}

        regressions: List[RegressionItem] = []

        # 1. Check individual case regressions
        for key, (r_base, c_base) in map_base.items():
            if key not in map_cand:
                continue

            r_cand, c_cand = map_cand[key]

            # Rule A: previously passed -> now failed or error
            if r_base.status == "passed" and r_cand.status in ("failed", "error"):
                regressions.append(
                    RegressionItem(
                        case_id=str(c_cand.id),
                        case_key=key,
                        check="case_status",
                        baseline_result=r_base.status,
                        candidate_result=r_cand.status,
                        reason=f"Case status regressed from '{r_base.status}' to '{r_cand.status}'",
                    )
                )

            # Rule B: previously passed -> now warning
            elif r_base.status == "passed" and r_cand.status == "warning":
                regressions.append(
                    RegressionItem(
                        case_id=str(c_cand.id),
                        case_key=key,
                        check="case_warning",
                        baseline_result="passed",
                        candidate_result="warning",
                        reason="Case raised verification warnings in candidate run",
                    )
                )

            # Rule C: Evaluator check lost (grounding, citation, format, completeness, safety)
            eval_b = {
                f.get("check_type"): f.get("passed")
                for f in (r_base.evaluation_result or {}).get("evaluation_findings", [])
            }
            eval_c = {
                f.get("check_type"): f.get("passed")
                for f in (r_cand.evaluation_result or {}).get("evaluation_findings", [])
            }

            for check_name, passed_b in eval_b.items():
                if passed_b is True and eval_c.get(check_name) is False:
                    regressions.append(
                        RegressionItem(
                            case_id=str(c_cand.id),
                            case_key=key,
                            check=f"evaluator_{check_name}",
                            baseline_result="passed",
                            candidate_result="failed",
                            reason=f"Evaluator check '{check_name}' passed in baseline but failed in candidate",
                        )
                    )

            # Rule D: Specific assertions lost (required_fields, output_format, citation_exists, etc.)
            asserts_b = {
                a.get("assertion_type"): a.get("passed")
                for a in (r_base.evaluation_result or {}).get("assertions", [])
            }
            asserts_c = {
                a.get("assertion_type"): a.get("passed")
                for a in (r_cand.evaluation_result or {}).get("assertions", [])
            }

            for a_type, pass_b in asserts_b.items():
                if pass_b is True and asserts_c.get(a_type) is False:
                    regressions.append(
                        RegressionItem(
                            case_id=str(c_cand.id),
                            case_key=key,
                            check=f"assertion_{a_type}",
                            baseline_result="passed",
                            candidate_result="failed",
                            reason=f"Assertion '{a_type}' satisfied in baseline but failed in candidate",
                        )
                    )

        # 2. Check Macro Aggregate Thresholds
        # Failure rate threshold
        total_b = len(rows_base) or 1
        total_c = len(rows_cand) or 1
        failed_b = sum(1 for r, _ in rows_base if r.status in ("failed", "error"))
        failed_c = sum(1 for r, _ in rows_cand if r.status in ("failed", "error"))

        rate_b = failed_b / total_b
        rate_c = failed_c / total_c
        failure_rate_increase = round(rate_c - rate_b, 4)

        if failure_rate_increase > settings.MAX_FAILURE_RATE_INCREASE:
            regressions.append(
                RegressionItem(
                    case_id="aggregate",
                    case_key="aggregate_failure_rate",
                    check="failure_rate_threshold",
                    baseline_result=f"{round(rate_b * 100, 1)}%",
                    candidate_result=f"{round(rate_c * 100, 1)}%",
                    reason=(
                        f"Failure rate increased by {round(failure_rate_increase * 100, 1)}%, "
                        f"exceeding threshold of {round(settings.MAX_FAILURE_RATE_INCREASE * 100, 1)}%"
                    ),
                )
            )

        # Latency threshold
        avg_lat_b = sum(r.latency_ms or 0 for r, _ in rows_base) / total_b
        avg_lat_c = sum(r.latency_ms or 0 for r, _ in rows_cand) / total_c
        lat_pct_increase = 0.0
        if avg_lat_b > 0:
            lat_pct_increase = round(((avg_lat_c - avg_lat_b) / avg_lat_b) * 100, 1)

        if lat_pct_increase > settings.MAX_LATENCY_INCREASE_PERCENT:
            regressions.append(
                RegressionItem(
                    case_id="aggregate",
                    case_key="aggregate_latency",
                    check="latency_threshold",
                    baseline_result=f"{round(avg_lat_b, 1)}ms",
                    candidate_result=f"{round(avg_lat_c, 1)}ms",
                    reason=(
                        f"Average latency increased by {lat_pct_increase}%, "
                        f"exceeding threshold of {settings.MAX_LATENCY_INCREASE_PERCENT}%"
                    ),
                )
            )

        # Cost threshold
        total_cost_b = sum(r.estimated_cost or 0.0 for r, _ in rows_base)
        total_cost_c = sum(r.estimated_cost or 0.0 for r, _ in rows_cand)
        cost_pct_increase = 0.0
        if total_cost_b > 0:
            cost_pct_increase = round(((total_cost_c - total_cost_b) / total_cost_b) * 100, 1)

        if cost_pct_increase > settings.MAX_COST_INCREASE_PERCENT:
            regressions.append(
                RegressionItem(
                    case_id="aggregate",
                    case_key="aggregate_cost",
                    check="cost_threshold",
                    baseline_result=f"${round(total_cost_b, 6)}",
                    candidate_result=f"${round(total_cost_c, 6)}",
                    reason=(
                        f"Total estimated cost increased by {cost_pct_increase}%, "
                        f"exceeding threshold of {settings.MAX_COST_INCREASE_PERCENT}%"
                    ),
                )
            )

        regression_detected = len(regressions) > 0

        # Record telemetry event if regression detected
        if regression_detected:
            tracer = ExecutionTracer(run_id=cand_exp.id, workspace_id=cand_exp.workspace_id)
            tracer.record_event(
                event_type=TraceEventType.EVALUATION_REGRESSION_DETECTED,
                status=TraceEventStatus.COMPLETED,
                step_type="regression_detected",
                metadata={"regression_count": len(regressions), "baseline_id": str(baseline_experiment_id)},
            )
            try:
                await tracer.flush_to_db(session)
            except Exception:
                pass

        return RegressionCheckResponse(
            regression_detected=regression_detected,
            regressions=regressions,
            metrics_deltas={
                "failure_rate_baseline": rate_b,
                "failure_rate_candidate": rate_c,
                "failure_rate_delta": failure_rate_increase,
                "avg_latency_baseline_ms": round(avg_lat_b, 1),
                "avg_latency_candidate_ms": round(avg_lat_c, 1),
                "latency_pct_increase": lat_pct_increase,
                "cost_baseline": round(total_cost_b, 6),
                "cost_candidate": round(total_cost_c, 6),
                "cost_pct_increase": cost_pct_increase,
            },
        )
