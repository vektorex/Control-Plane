"""
Deterministic Outcome and Objective Health Evaluator for Step 43:
AI Outcome Intelligence & Work Impact Layer.
Evaluates health transparently with explicit, explainable rules.
"""
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from backend.app.services.outcomes.models import (
    Objective,
    Outcome,
    OutcomeMilestone,
    OutcomeTarget,
    OutcomeEvidence,
)
from backend.app.services.outcomes.registry import (
    MilestoneStatus,
    OutcomeHealthStatus,
    OutcomeStatus,
)


class HealthEvaluator:
    """
    Evaluates health for Objectives and Outcomes based purely on deterministic criteria.
    Never outputs subjective or arbitrary scores.
    """

    STALENESS_THRESHOLD_DAYS: int = 30

    @classmethod
    def evaluate_objective_health(
        cls,
        milestones: List[Any],
        targets: List[Any],
        outcomes: List[Any],
        objective: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Evaluates an Objective's health based on deterministic criteria.
        Works with SQLAlchemy models or plain dicts.
        """
        now = datetime.now(timezone.utc)
        reasons: List[str] = []
        is_blocked = False
        is_at_risk = False
        is_stale = False

        obj_status = "active"
        if objective is not None:
            obj_status = getattr(objective, "status", None) or (objective.get("status") if isinstance(objective, dict) else "active")

        # 1. Check completed or cancelled
        if obj_status in {"completed", "cancelled", "archived"}:
            return {
                "status": obj_status,
                "health_status": obj_status,
                "is_healthy": obj_status == "completed",
                "reasons": [f"Objective is in terminal status '{obj_status}'."],
                "checked_at": now,
                "details": {"status": obj_status},
            }

        # 2. Check milestones
        overdue_milestones = 0
        blocked_milestones = 0
        for m in milestones:
            m_status = getattr(m, "status", None) or (m.get("status") if isinstance(m, dict) else "")
            m_name = getattr(m, "name", None) or (m.get("name") if isinstance(m, dict) else "Unnamed")
            m_due = getattr(m, "due_at", None) or (m.get("due_at") if isinstance(m, dict) else None)

            if m_status == MilestoneStatus.BLOCKED.value or m_status == "blocked":
                blocked_milestones += 1
                reasons.append(f"Milestone '{m_name}' is BLOCKED.")
            elif m_status == MilestoneStatus.MISSED.value or m_status == "missed":
                overdue_milestones += 1
                reasons.append(f"Milestone '{m_name}' is marked MISSED.")
            elif m_due and m_status != MilestoneStatus.COMPLETED.value and m_status != "completed" and m_due < now:
                overdue_milestones += 1
                reasons.append(f"Milestone '{m_name}' is overdue (due: {m_due.isoformat()}).")

        if blocked_milestones > 0:
            is_blocked = True

        if overdue_milestones > 0:
            is_at_risk = True

        # 3. Check targets
        for t in targets:
            t_status = getattr(t, "status", None) or (t.get("status") if isinstance(t, dict) else "")
            t_name = getattr(t, "name", None) or (t.get("name") if isinstance(t, dict) else "Target")
            t_date = getattr(t, "target_date", None) or (t.get("target_date") if isinstance(t, dict) else None)

            if t_date and t_status != "achieved" and t_date < now:
                is_at_risk = True
                reasons.append(f"Target '{t_name}' missed target date ({t_date.isoformat()}).")
            elif t_status == "at_risk":
                is_at_risk = True
                reasons.append(f"Target '{t_name}' is marked at_risk.")

        # 4. Check staleness
        if objective is not None:
            last_updated = getattr(objective, "updated_at", None) or getattr(objective, "created_at", None) or now
            if (now - last_updated) > timedelta(days=cls.STALENESS_THRESHOLD_DAYS):
                is_stale = True
                reasons.append(f"Objective has not been updated in over {cls.STALENESS_THRESHOLD_DAYS} days.")

        # 5. Check outcome failures/disputes
        failed_outcomes = [
            o for o in outcomes
            if (getattr(o, "status", None) or (o.get("status") if isinstance(o, dict) else "")) == "failed"
        ]
        disputed_outcomes = [
            o for o in outcomes
            if (getattr(o, "status", None) or (o.get("status") if isinstance(o, dict) else "")) == "disputed"
        ]
        if failed_outcomes:
            is_at_risk = True
            reasons.append(f"{len(failed_outcomes)} associated outcome(s) have failed.")
        if disputed_outcomes:
            is_at_risk = True
            reasons.append(f"{len(disputed_outcomes)} associated outcome(s) are disputed.")

        # Determine final status
        if is_blocked:
            status = OutcomeHealthStatus.BLOCKED.value
        elif is_at_risk:
            status = OutcomeHealthStatus.AT_RISK.value
        elif is_stale:
            status = OutcomeHealthStatus.STALE.value
        else:
            status = OutcomeHealthStatus.HEALTHY.value
            reasons.append("All milestones and targets are currently on track.")

        return {
            "status": status,
            "health_status": status,
            "is_healthy": status == OutcomeHealthStatus.HEALTHY.value,
            "reasons": reasons,
            "checked_at": now,
            "details": {
                "blocked_milestones": blocked_milestones,
                "overdue_milestones": overdue_milestones,
                "total_targets": len(targets),
                "total_outcomes": len(outcomes),
            },
        }

    @classmethod
    def check_staleness(
        cls,
        outcome: Any,
        validity_days: int = 30,
    ) -> Dict[str, Any]:
        """Checks if outcome or targets exceed validity window."""
        now = datetime.now(timezone.utc)
        updated_at = getattr(outcome, "updated_at", None) or (outcome.get("updated_at") if isinstance(outcome, dict) else None)
        if updated_at is None:
            updated_at = now

        delta_days = (now - updated_at).days
        if delta_days > validity_days:
            return {
                "is_stale": True,
                "reason": f"Target/outcome not updated for {delta_days} days (validity window: {validity_days} days).",
            }
        return {"is_stale": False, "reason": "Fresh"}

    @classmethod
    def evaluate_outcome_health(
        cls,
        outcome: Outcome,
        evidence_list: List[OutcomeEvidence],
    ) -> Dict[str, Any]:
        """
        Evaluates an individual Outcome's health.
        """
        now = datetime.now(timezone.utc)
        reasons: List[str] = []

        if outcome.status == OutcomeStatus.VERIFIED.value:
            return {
                "status": OutcomeHealthStatus.VERIFIED.value,
                "is_healthy": True,
                "reasons": ["Outcome is verified with required evidence."],
                "checked_at": now,
                "details": {"status": outcome.status},
            }

        if outcome.status == OutcomeStatus.DISPUTED.value:
            return {
                "status": OutcomeHealthStatus.DISPUTED.value,
                "is_healthy": False,
                "reasons": ["Outcome is currently disputed by human or policy evaluation."],
                "checked_at": now,
                "details": {"status": outcome.status},
            }

        if outcome.status == OutcomeStatus.FAILED.value:
            return {
                "status": OutcomeHealthStatus.FAILED.value,
                "is_healthy": False,
                "reasons": ["Outcome execution or verification failed."],
                "checked_at": now,
                "details": {"status": outcome.status},
            }

        # Check staleness
        latest_evidence_time = max([e.created_at for e in evidence_list], default=outcome.updated_at or outcome.created_at)
        if (now - latest_evidence_time) > timedelta(days=cls.STALENESS_THRESHOLD_DAYS):
            return {
                "status": OutcomeHealthStatus.STALE.value,
                "is_healthy": False,
                "reasons": [f"No new evidence or updates recorded for over {cls.STALENESS_THRESHOLD_DAYS} days."],
                "checked_at": now,
                "details": {"latest_evidence_time": latest_evidence_time.isoformat()},
            }

        # Check evidence requirements
        reqs = outcome.requirements or {}
        req_types = reqs.get("required_evidence_types") or reqs.get("required_evidence", [])
        if req_types:
            present_types = {e.evidence_type for e in evidence_list}
            missing = [rt for rt in req_types if rt not in present_types]
            if missing:
                reasons.append(f"Missing required evidence: {', '.join(missing)}.")
                return {
                    "status": OutcomeHealthStatus.AT_RISK.value,
                    "is_healthy": False,
                    "reasons": reasons,
                    "checked_at": now,
                    "details": {"missing_evidence": missing},
                }

        reasons.append("Outcome is actively progressing towards fulfillment.")
        return {
            "status": OutcomeHealthStatus.HEALTHY.value,
            "is_healthy": True,
            "reasons": reasons,
            "checked_at": now,
            "details": {"evidence_count": len(evidence_list)},
        }
