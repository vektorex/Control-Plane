"""
Database-backed TriggerScheduler with cron validation, timezone handling, and safe due-trigger claiming.
"""
import uuid
import zoneinfo
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.db.models.trigger import WorkflowTrigger, TriggerRun
from backend.app.services.triggers.errors import TriggerValidationError


class CronFieldParser:
    """Parses and matches a single cron field."""

    @staticmethod
    def parse_field(field_str: str, min_val: int, max_val: int) -> Set[int]:
        """
        Parses a cron field string supporting '*', ',', '-', and '/'.
        Returns a set of matched integers.
        """
        field_str = field_str.strip()
        matched: Set[int] = set()

        # Handle list separated by commas: e.g. "1,2,5"
        for part in field_str.split(","):
            part = part.strip()
            if not part:
                continue

            # Handle step: e.g. "*/5" or "10-20/2"
            step = 1
            if "/" in part:
                subparts = part.split("/")
                if len(subparts) != 2:
                    raise TriggerValidationError(f"Invalid cron step syntax: '{part}'")
                try:
                    step = int(subparts[1])
                    if step <= 0:
                        raise ValueError()
                except ValueError:
                    raise TriggerValidationError(f"Invalid cron step value: '{subparts[1]}'")
                part = subparts[0]

            if part == "*":
                start, end = min_val, max_val
            elif "-" in part:
                range_parts = part.split("-")
                if len(range_parts) != 2:
                    raise TriggerValidationError(f"Invalid cron range syntax: '{part}'")
                try:
                    start, end = int(range_parts[0]), int(range_parts[1])
                except ValueError:
                    raise TriggerValidationError(f"Invalid cron range numbers: '{part}'")
            else:
                try:
                    val = int(part)
                    start, end = val, val
                except ValueError:
                    raise TriggerValidationError(f"Invalid cron number: '{part}'")

            if start < min_val or end > max_val or start > end:
                raise TriggerValidationError(
                    f"Cron values out of bounds [{min_val}, {max_val}]: got {start}-{end}"
                )

            for v in range(start, end + 1, step):
                matched.add(v)

        return matched


class TriggerScheduler:
    """
    Evaluates recurring schedules, validates cron and timezones, and claims due triggers.
    """

    PREDEFINED_SCHEDULES = {
        "@hourly": "0 * * * *",
        "hourly": "0 * * * *",
        "every hour": "0 * * * *",
        "@daily": "0 0 * * *",
        "daily": "0 0 * * *",
        "every day": "0 0 * * *",
        "@weekly": "0 0 * * 0",
        "weekly": "0 0 * * 0",
        "every week": "0 0 * * 0",
    }

    @classmethod
    def normalize_expression(cls, expr: str) -> str:
        """Translates predefined shortcuts to standard 5-part cron."""
        cleaned = expr.strip().lower()
        if cleaned in cls.PREDEFINED_SCHEDULES:
            return cls.PREDEFINED_SCHEDULES[cleaned]
        return expr.strip()

    @classmethod
    def validate_timezone(cls, tz_name: str) -> zoneinfo.ZoneInfo:
        """Validates that tz_name is a recognized IANA timezone."""
        if not tz_name:
            return zoneinfo.ZoneInfo("UTC")
        try:
            return zoneinfo.ZoneInfo(tz_name)
        except Exception:
            raise TriggerValidationError(f"Invalid timezone: '{tz_name}'. Must be a valid IANA timezone name.")

    @classmethod
    def parse_cron(cls, expression: str) -> Tuple[Set[int], Set[int], Set[int], Set[int], Set[int]]:
        """
        Parses a 5-field cron expression:
        minute (0-59), hour (0-23), day of month (1-31), month (1-12), day of week (0-6)
        """
        expr = cls.normalize_expression(expression)
        parts = expr.split()
        if len(parts) != 5:
            raise TriggerValidationError(
                f"Cron expression must have exactly 5 fields (minute hour dom month dow). Got {len(parts)} fields: '{expression}'"
            )

        minutes = CronFieldParser.parse_field(parts[0], 0, 59)
        hours = CronFieldParser.parse_field(parts[1], 0, 23)
        doms = CronFieldParser.parse_field(parts[2], 1, 31)
        months = CronFieldParser.parse_field(parts[3], 1, 12)
        # In cron, both 0 and 7 can represent Sunday
        raw_dows = CronFieldParser.parse_field(parts[4], 0, 7)
        dows = {0 if d == 7 else d for d in raw_dows}

        return minutes, hours, doms, months, dows

    @classmethod
    def compute_next_run(
        cls,
        expression: str,
        tz_name: str = "UTC",
        after_dt: Optional[datetime] = None,
    ) -> datetime:
        """
        Computes the next datetime when the cron expression matches, starting strictly after after_dt.
        Ensures minimum schedule interval >= 60 seconds.
        """
        tz = cls.validate_timezone(tz_name)
        minutes, hours, doms, months, dows = cls.parse_cron(expression)

        if after_dt is None:
            after_dt = datetime.now(timezone.utc)
        elif after_dt.tzinfo is None:
            after_dt = after_dt.replace(tzinfo=timezone.utc)

        # Convert to target timezone
        local_dt = after_dt.astimezone(tz)
        
        # Advance by 1 minute to ensure next run is strictly in the future
        curr = (local_dt + timedelta(minutes=1)).replace(second=0, microsecond=0)

        # Search up to 525,600 minutes (1 year)
        max_minutes = 525600
        for _ in range(max_minutes):
            # Python weekday(): Monday is 0 and Sunday is 6
            # Cron day of week: Sunday is 0, Monday is 1, ..., Saturday is 6
            # Conversion: (curr.weekday() + 1) % 7
            cron_dow = (curr.weekday() + 1) % 7

            if (
                curr.month in months
                and curr.day in doms
                and cron_dow in dows
                and curr.hour in hours
                and curr.minute in minutes
            ):
                # Return in UTC
                return curr.astimezone(timezone.utc)

            curr += timedelta(minutes=1)

        raise TriggerValidationError(f"Could not compute next run within 1 year for schedule '{expression}'.")

    @classmethod
    async def validate_schedule_config(
        cls,
        config: Dict[str, Any],
        session: AsyncSession,
        workspace_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        Validates schedule configuration and enforces workspace scheduled triggers limit.
        """
        sched = config.get("schedule", config)
        expr = sched.get("expression") or sched.get("cron") or "0 * * * *"
        tz_str = sched.get("timezone", "UTC")

        # Validate timezone and cron
        cls.validate_timezone(tz_str)
        cls.parse_cron(expr)

        # Enforce MAX_SCHEDULED_WORKFLOWS_PER_WORKSPACE
        max_allowed = getattr(settings, "MAX_SCHEDULED_WORKFLOWS_PER_WORKSPACE", 50)
        stmt = (
            select(func.count(WorkflowTrigger.id))
            .where(
                WorkflowTrigger.workspace_id == workspace_id,
                WorkflowTrigger.trigger_type == "schedule",
                WorkflowTrigger.status.in_(["active", "paused"]),
            )
        )
        res = await session.execute(stmt)
        count = res.scalar() or 0
        if count >= max_allowed:
            raise TriggerValidationError(
                f"Workspace scheduled triggers limit reached ({count}/{max_allowed}). Delete or archive existing scheduled triggers."
            )

        return {
            "kind": "cron",
            "expression": cls.normalize_expression(expr),
            "timezone": tz_str,
        }

    @classmethod
    async def identify_and_claim_due_triggers(
        cls,
        session: AsyncSession,
    ) -> List[WorkflowTrigger]:
        """
        Finds active scheduled triggers where next_run_at <= now,
        updates last_triggered_at and schedules next_run_at atomically.
        """
        now = datetime.now(timezone.utc)

        stmt = (
            select(WorkflowTrigger)
            .where(
                WorkflowTrigger.trigger_type == "schedule",
                WorkflowTrigger.status == "active",
                WorkflowTrigger.next_run_at <= now,
            )
            .with_for_update(skip_locked=True)
        )
        result = await session.execute(stmt)
        due_triggers = list(result.scalars().all())

        for trigger in due_triggers:
            sched_cfg = trigger.configuration.get("schedule", trigger.configuration)
            expr = sched_cfg.get("expression", "0 * * * *")
            tz_str = sched_cfg.get("timezone", "UTC")

            trigger.last_triggered_at = now
            try:
                trigger.next_run_at = cls.compute_next_run(expr, tz_str, after_dt=now)
            except Exception as e:
                logger.error(f"[Scheduler] Failed to compute next run for trigger {trigger.id}: {e}")
                # Fallback: advance 1 hour
                trigger.next_run_at = now + timedelta(hours=1)

        if due_triggers:
            await session.commit()

        return due_triggers
