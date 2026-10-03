"""
Multi-Agent Team Orchestration Coordinator for Step 40.
Manages team execution, role assignments, cross-agent context, conflict detection, and final synthesis.
"""
from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.services.agents.errors import (
    AgentLifecycleError,
    AgentTeamNotFoundError,
    AgentTeamVersionNotFoundError,
)
from backend.app.services.agents.events import AgentEventPublisher
from backend.app.services.agents.messages import AgentMessageService
from backend.app.services.agents.models import (
    AgentConflict,
    AgentTeam,
    AgentTeamMember,
    AgentTeamRun,
    AgentTeamVersion,
)
from backend.app.services.agents.planner import TeamPlanner
from backend.app.services.agents.runtime import AgentRuntime
from backend.app.services.agents.schemas import AgentTeamStatus
from backend.app.services.events.constants import SystemEventType


class TeamOrchestrationCoordinator:
    """Coordinates governed multi-agent team runs."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.agent_runtime = AgentRuntime(session)
        self.message_service = AgentMessageService(session)
        self.event_publisher = AgentEventPublisher(session)

    async def execute_team_run(
        self,
        team_id: str,
        workspace_id: str,
        user_id: str,
        input_data: Dict[str, Any],
        team_version_id: Optional[str] = None,
        project_id: Optional[str] = None,
        objective_override: Optional[str] = None,
        dry_run: bool = False,
    ) -> AgentTeamRun:
        """
        Executes the governed lifecycle for a multi-agent team run:
        1. Resolve Team and TeamVersion
        2. Validate team active status and membership
        3. Generate and validate structured plan
        4. Initialize AgentTeamRun record
        5. Execute assignments across stages
        6. Transmit structured messages
        7. Detect any substantive discrepancies / conflicts
        8. Synthesize final results
        9. Persist and emit events
        """
        start_time = time.time()

        # 1. Resolve Team
        team = await self.session.get(AgentTeam, team_id)
        if not team or team.workspace_id != workspace_id:
            raise AgentTeamNotFoundError(team_id)

        if team.status != AgentTeamStatus.ACTIVE.value:
            raise AgentLifecycleError(
                current_status=team.status,
                target_status="executing",
                reason=f"Team '{team_id}' is '{team.status}'. Only active teams can execute tasks.",
            )

        # 2. Resolve TeamVersion
        target_version_id = team_version_id or team.current_version_id
        if not target_version_id:
            raise AgentTeamVersionNotFoundError(team_id)

        team_version = await self.session.get(AgentTeamVersion, target_version_id)
        if not team_version or team_version.team_id != team.id:
            raise AgentTeamVersionNotFoundError(team_id, version_id=target_version_id)

        # Fetch members
        stmt = select(AgentTeamMember).where(AgentTeamMember.team_version_id == team_version.id)
        res = await self.session.execute(stmt)
        members = list(res.scalars().all())
        if not members:
            raise AgentTeamVersionNotFoundError(team_id, version_id=team_version.id)

        member_dicts = [
            {
                "agent_id": m.agent_id,
                "agent_version_id": m.agent_version_id,
                "role": m.role,
                "capabilities": m.capabilities or [],
                "responsibilities": m.responsibilities or "",
                "limits": m.limits or {},
            }
            for m in members
        ]

        objective = objective_override or team_version.objective

        # 3. Create plan
        team_run_id = str(uuid.uuid4())
        plan = TeamPlanner.generate_plan(
            team_run_id=team_run_id,
            objective=objective,
            members=member_dicts,
            user_input=input_data,
            coordination_policy=team_version.coordination_policy,
        )

        # 4. Initialize AgentTeamRun
        team_run = AgentTeamRun(
            id=team_run_id,
            team_id=team.id,
            team_version_id=team_version.id,
            workspace_id=workspace_id,
            project_id=project_id or team.project_id,
            initiated_by=user_id,
            objective=objective,
            status="planning",
            plan=plan,
            shared_context={"initial_input": input_data, "stage_findings": {}},
            final_synthesis=None,
            cost=0.0,
            latency=0.0,
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(team_run)
        await self.session.flush()

        await self.event_publisher.emit_team_run_event(
            event_type=SystemEventType.AGENT_TEAM_RUN_STARTED.value,
            workspace_id=workspace_id,
            team_run_id=team_run.id,
            team_id=team.id,
            payload={"objective": objective, "plan": plan},
            project_id=team_run.project_id,
            actor_id=user_id,
        )

        team_run.status = "executing"
        findings_by_agent: Dict[str, Any] = {}
        total_team_cost = 0.0

        try:
            # 5. Execute assignments in planned order
            for assignment in plan.get("assignments", []):
                ag_id = assignment["agent_id"]
                assign_id = assignment["assignment_id"]

                # Emit assignment created event
                await self.event_publisher.emit_team_run_event(
                    event_type=SystemEventType.AGENT_TEAM_ASSIGNMENT_CREATED.value,
                    workspace_id=workspace_id,
                    team_run_id=team_run.id,
                    team_id=team.id,
                    payload={"assignment": assignment},
                    project_id=team_run.project_id,
                )

                # Send task assignment message
                await self.message_service.send_message(
                    team_run_id=team_run.id,
                    sender_agent_id=ag_id,
                    message_type="task_assignment",
                    content=assignment.get("description", "Team task assignment"),
                    metadata={"assignment_id": assign_id},
                )

                # Execute member agent
                agent_input = {
                    "team_objective": objective,
                    "assignment": assignment,
                    "team_shared_context": team_run.shared_context,
                }

                member_match = next((m for m in member_dicts if m["agent_id"] == ag_id), None)
                ver_id = member_match["agent_version_id"] if member_match else None

                agent_run = await self.agent_runtime.execute_agent_run(
                    agent_id=ag_id,
                    workspace_id=workspace_id,
                    user_id=user_id,
                    input_data=agent_input,
                    version_id=ver_id,
                    project_id=team_run.project_id,
                    dry_run=dry_run,
                )

                total_team_cost += agent_run.cost
                agent_output_text = (agent_run.output or {}).get("text", "")
                findings_by_agent[ag_id] = agent_output_text

                # Update shared context
                curr_context = dict(team_run.shared_context or {})
                stage_findings = curr_context.get("stage_findings", {})
                stage_findings[ag_id] = agent_output_text
                curr_context["stage_findings"] = stage_findings
                team_run.shared_context = curr_context

                # Send task result message
                await self.message_service.send_message(
                    team_run_id=team_run.id,
                    sender_agent_id=ag_id,
                    message_type="task_result",
                    content=agent_output_text[:500],
                    metadata={"assignment_id": assign_id, "run_id": agent_run.id},
                )

                # Emit assignment completed event
                await self.event_publisher.emit_team_run_event(
                    event_type=SystemEventType.AGENT_TEAM_ASSIGNMENT_COMPLETED.value,
                    workspace_id=workspace_id,
                    team_run_id=team_run.id,
                    team_id=team.id,
                    payload={"assignment_id": assign_id, "agent_id": ag_id, "cost": agent_run.cost},
                    project_id=team_run.project_id,
                )

            # 7. Discrepancy & Conflict detection check
            # If we have multiple agents, check if their outputs contain explicit contradictions
            agent_ids = list(findings_by_agent.keys())
            if len(agent_ids) >= 2:
                # Check for conflict keywords
                out_a = findings_by_agent[agent_ids[0]].lower()
                out_b = findings_by_agent[agent_ids[1]].lower()
                if ("disagree" in out_b or "conflict" in out_b or "reject" in out_b) and len(out_b) > 20:
                    conflict = AgentConflict(
                        team_run_id=team_run.id,
                        subject="Analysis discrepancy in team outputs",
                        agent_a_id=agent_ids[0],
                        agent_b_id=agent_ids[1],
                        position_a=findings_by_agent[agent_ids[0]][:400],
                        position_b=findings_by_agent[agent_ids[1]][:400],
                        evidence_a={"source": "agent_execution", "agent_id": agent_ids[0]},
                        evidence_b={"source": "agent_execution", "agent_id": agent_ids[1]},
                        status="open",
                    )
                    self.session.add(conflict)
                    await self.session.flush()

                    await self.event_publisher.emit_team_run_event(
                        event_type=SystemEventType.AGENT_TEAM_CONFLICT_DETECTED.value,
                        workspace_id=workspace_id,
                        team_run_id=team_run.id,
                        team_id=team.id,
                        payload={"conflict_id": conflict.id, "subject": conflict.subject},
                        project_id=team_run.project_id,
                    )

            # 8. Final Synthesis
            team_run.final_synthesis = {
                "objective": objective,
                "summary": f"Team '{team.name}' successfully coordinated across {len(member_dicts)} agents.",
                "member_contributions": {ag: text[:300] for ag, text in findings_by_agent.items()},
                "status": "completed",
            }
            team_run.status = "completed"
            team_run.completed_at = datetime.now(timezone.utc)
            team_run.cost = total_team_cost
            team_run.latency = round(time.time() - start_time, 4)

            # Send final result message
            lead_agent_id = next((m["agent_id"] for m in member_dicts if m["role"] == "lead"), member_dicts[0]["agent_id"])
            await self.message_service.send_message(
                team_run_id=team_run.id,
                sender_agent_id=lead_agent_id,
                message_type="final_result",
                content=team_run.final_synthesis["summary"],
                metadata={"final_synthesis": team_run.final_synthesis},
            )

            await self.event_publisher.emit_team_run_event(
                event_type=SystemEventType.AGENT_TEAM_RUN_COMPLETED.value,
                workspace_id=workspace_id,
                team_run_id=team_run.id,
                team_id=team.id,
                payload={
                    "status": "completed",
                    "cost": team_run.cost,
                    "latency": team_run.latency,
                },
                project_id=team_run.project_id,
            )

            await self.session.commit()
            return team_run

        except Exception as e:
            logger.error(f"Team run '{team_run.id}' failed: {e}")
            team_run.status = "failed"
            team_run.error = {"message": str(e), "type": type(e).__name__}
            team_run.completed_at = datetime.now(timezone.utc)
            team_run.latency = round(time.time() - start_time, 4)
            await self.session.commit()
            raise
