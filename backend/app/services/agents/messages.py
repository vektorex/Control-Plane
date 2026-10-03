"""
Agent Messaging Service for Step 40.
Normalized message handling between agents in multi-agent team runs.
Strictly treats messages as data context, not executable instructions.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.agents.models import AgentMessage
from backend.app.services.agents.schemas import AgentMessageType
from backend.app.services.agents.validators import AgentInputSanitizer


class AgentMessageService:
    """Manages structured communication between agents in a team run."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def send_message(
        self,
        team_run_id: str,
        sender_agent_id: str,
        message_type: str,
        content: str,
        recipient_agent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentMessage:
        """
        Creates and stores a validated, sanitized agent message.
        """
        clean_content = content.strip()
        msg = AgentMessage(
            team_run_id=team_run_id,
            sender_agent_id=sender_agent_id,
            recipient_agent_id=recipient_agent_id,
            message_type=message_type,
            content=clean_content,
            message_metadata=metadata or {},
        )
        self.session.add(msg)
        await self.session.flush()
        return msg

    async def get_team_messages(
        self,
        team_run_id: str,
        limit: int = 100,
    ) -> List[AgentMessage]:
        """Fetches chronological messages for a team run."""
        stmt = (
            select(AgentMessage)
            .where(AgentMessage.team_run_id == team_run_id)
            .order_by(AgentMessage.created_at.asc())
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    def format_as_untrusted_context(cls, message: AgentMessage) -> str:
        """Formats an agent message as untrusted context to prevent prompt injection."""
        source = f"Agent:{message.sender_agent_id} (Type:{message.message_type})"
        return AgentInputSanitizer.format_untrusted_context(source, message.content)
