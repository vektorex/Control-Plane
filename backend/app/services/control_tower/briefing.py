"""
AI Briefing service for Step 45: Control Tower.
Uses AIGateway to summarize authorized facts only.
Cannot execute actions. Cannot access data outside authorization context.
Clearly distinguishes: observed fact | derived state | recommendation.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.services.control_tower.aggregation import ControlTowerAggregator
from backend.app.services.control_tower.attention import AttentionService


class ControlTowerBriefingService:
    """
    Summarizes authorized system state using AIGateway.
    AI briefing is an optional enhancement - Control Tower functions normally without it.
    Never exposes unauthorized records. Never executes actions.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.aggregator = ControlTowerAggregator(session)
        self.attention_svc = AttentionService(session)

    async def generate_briefing(
        self,
        workspace_id: str,
        user_id: str,
        mode: str = "standard",
        project_id: Optional[str] = None,
        since_hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Retrieve authorized state, then optionally summarize with AIGateway.
        Falls back gracefully if AIGateway is unavailable.
        Statements are typed: observed | derived | recommendation.
        """
        generated_at = datetime.now(timezone.utc)
        statements: List[Dict[str, Any]] = []
        source_refs: List[Dict[str, str]] = []

        # 1. Retrieve authorized facts
        try:
            overview = await self.aggregator.aggregate_overview(workspace_id, project_id)
            attention_items = await self.attention_svc.get_prioritized_attention(
                workspace_id=workspace_id,
                limit=20,
                status="open",
                project_id=project_id,
            )
        except Exception as exc:
            logger.warning(f"[Briefing] Failed to gather facts: {exc}")
            return self._fallback_briefing(generated_at)

        sections = overview.get("sections", {})

        # 2. Build observed fact statements from raw counts
        def count_val(section_name: str) -> Optional[int]:
            s = sections.get(section_name, {})
            return s.get("count") if s.get("available") else None

        obs_facts = []
        for section_key, label in [
            ("active_tasks", "active task(s)"),
            ("active_workflows", "active workflow(s)"),
            ("pending_approvals", "pending approval(s)"),
            ("failed_jobs", "failed job(s)"),
            ("active_agents", "active AI agent run(s)"),
            ("open_security_incidents", "open security incident(s)"),
            ("stale_plans", "stale work plan(s)"),
            ("blocked_outcomes", "blocked outcome(s)"),
            ("open_attention_items", "open attention item(s)"),
        ]:
            v = count_val(section_key)
            if v is not None and v > 0:
                stmt = {
                    "type": "observed",
                    "text": f"{v} {label}.",
                    "source_type": section_key,
                    "source_id": None,
                    "source_label": section_key.replace("_", " ").title(),
                }
                obs_facts.append(stmt)
                source_refs.append({"type": section_key, "label": section_key})
            elif v is None:
                # Data unavailable - never report as zero
                obs_facts.append({
                    "type": "observed",
                    "text": f"{section_key.replace('_', ' ').title()}: data currently unavailable.",
                    "source_type": section_key,
                    "source_id": None,
                    "source_label": section_key,
                })

        statements.extend(obs_facts)

        # 3. Derived state statements from attention items
        critical_items = [a for a in attention_items if a["severity"] == "critical"]
        if critical_items:
            statements.append({
                "type": "derived",
                "text": f"{len(critical_items)} critical attention item(s) require immediate review.",
                "source_type": "attention_items",
                "source_id": None,
                "source_label": "Attention Items",
            })

        # Security items must always be surfaced
        security_items = [a for a in attention_items if a["attention_type"] == "security_incident"]
        if security_items:
            statements.append({
                "type": "derived",
                "text": f"{len(security_items)} security incident(s) are active. Review via Security Operations.",
                "source_type": "security",
                "source_id": None,
                "source_label": "Security Operations",
            })

        # 4. Recommendations
        recs = self._derive_recommendations(sections, attention_items)
        statements.extend(recs)

        # 5. Optionally enhance with AIGateway summary (optional enhancement)
        ai_generated = False
        if mode in ("standard", "detailed"):
            try:
                enhanced = await self._ai_enhance(
                    statements, workspace_id, mode, since_hours
                )
                if enhanced:
                    statements = enhanced
                    ai_generated = True
            except Exception as exc:
                # AI enhancement failure does NOT break the briefing
                logger.warning(f"[Briefing] AIGateway enhancement failed (non-critical): {exc}")

        return {
            "mode": mode,
            "generated_at": generated_at.isoformat(),
            "statements": statements,
            "ai_generated": ai_generated,
            "disclaimer": (
                "AI-generated summary of authorized facts. "
                "Verify critical decisions from source records. "
                "AI cannot execute actions."
            ),
            "source_references": source_refs,
        }

    def _derive_recommendations(
        self, sections: Dict, attention_items: List[Dict]
    ) -> List[Dict[str, Any]]:
        recs = []
        failed_jobs = (sections.get("failed_jobs") or {}).get("count")
        if failed_jobs and failed_jobs > 0:
            recs.append({
                "type": "recommendation",
                "text": f"Review {failed_jobs} failed job(s) - consider retrying or investigating root causes.",
                "source_type": "jobs",
                "source_id": None,
                "source_label": "Jobs",
            })
        pending = (sections.get("pending_approvals") or {}).get("count")
        if pending and pending > 0:
            recs.append({
                "type": "recommendation",
                "text": f"Review {pending} pending approval(s) to unblock waiting work.",
                "source_type": "approvals",
                "source_id": None,
                "source_label": "Approvals",
            })
        stale_plans = (sections.get("stale_plans") or {}).get("count")
        if stale_plans and stale_plans > 0:
            recs.append({
                "type": "recommendation",
                "text": f"Revalidate {stale_plans} stale work plan(s) before relying on them.",
                "source_type": "plans",
                "source_id": None,
                "source_label": "Work Plans",
            })
        return recs

    async def _ai_enhance(
        self,
        statements: List[Dict],
        workspace_id: str,
        mode: str,
        since_hours: int,
    ) -> Optional[List[Dict]]:
        """
        Optional AIGateway enhancement of the briefing.
        Only summarizes already-retrieved authorized facts.
        Cannot access data outside the authorized context.
        """
        try:
            from backend.app.services.ai_gateway.gateway import AIGateway
            gw = AIGateway()
            fact_text = "\n".join(
                f"[{s['type'].upper()}] {s['text']}" for s in statements
            )
            prompt = (
                f"You are a work operations assistant. Summarize the following authorized "
                f"system state facts in {mode} mode. Do NOT fabricate information. "
                f"Do NOT take actions. Clearly separate: OBSERVED FACTS, DERIVED STATE, and RECOMMENDATIONS.\n\n"
                f"AUTHORIZED FACTS:\n{fact_text}\n\n"
                f"Provide a clear, concise briefing."
            )
            response = await gw.complete(prompt=prompt, max_tokens=800)
            if response and response.text:
                return statements + [{
                    "type": "derived",
                    "text": f"[AI Summary] {response.text.strip()}",
                    "source_type": "ai_briefing",
                    "source_id": None,
                    "source_label": "AI Briefing (summary of above facts)",
                }]
        except Exception:
            pass
        return None

    def _fallback_briefing(self, generated_at: datetime) -> Dict[str, Any]:
        return {
            "mode": "brief",
            "generated_at": generated_at.isoformat(),
            "statements": [{
                "type": "observed",
                "text": "System state could not be retrieved at this time. Please refresh or check individual sections.",
                "source_type": "system",
                "source_id": None,
                "source_label": "System",
            }],
            "ai_generated": False,
            "disclaimer": "Briefing partially unavailable. Individual sections may still be operational.",
            "source_references": [],
        }
