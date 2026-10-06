"""
Fault Injection Engine and Failure Profiles for Step 41: AI Agent Simulation.
Deterministic, seeded, bounded fault injection without uncontrolled randomness.
"""
from datetime import datetime, timezone
import random
from typing import Any, Dict, List, Optional
import uuid

from backend.app.core.logging import logger
from backend.app.services.simulation.errors import FaultInjectionConfigError


SUPPORTED_FAULTS = {
    "model_timeout",
    "model_rate_limit",
    "model_unavailable",
    "tool_timeout",
    "tool_failure",
    "connector_timeout",
    "connector_failure",
    "retrieval_empty",
    "retrieval_low_quality",
    "memory_unavailable",
    "knowledge_unavailable",
    "evaluation_failure",
    "approval_timeout",
    "budget_exhausted",
    "job_failure",
    "event_delivery_failure",
    "partial_agent_failure",
    "agent_message_delay",
    "agent_message_loss",
}


class FaultType:
    MODEL_TIMEOUT = "model_timeout"
    MODEL_RATE_LIMIT = "model_rate_limit"
    MODEL_UNAVAILABLE = "model_unavailable"
    TOOL_TIMEOUT = "tool_timeout"
    TOOL_FAILURE = "tool_failure"
    CONNECTOR_TIMEOUT = "connector_timeout"
    CONNECTOR_FAILURE = "connector_failure"
    RETRIEVAL_EMPTY = "retrieval_empty"
    RETRIEVAL_LOW_QUALITY = "retrieval_low_quality"
    MEMORY_UNAVAILABLE = "memory_unavailable"
    KNOWLEDGE_UNAVAILABLE = "knowledge_unavailable"
    EVALUATION_FAILURE = "evaluation_failure"
    APPROVAL_TIMEOUT = "approval_timeout"
    BUDGET_EXHAUSTED = "budget_exhausted"
    JOB_FAILURE = "job_failure"
    EVENT_DELIVERY_FAILURE = "event_delivery_failure"
    PARTIAL_AGENT_FAILURE = "partial_agent_failure"
    AGENT_MESSAGE_DELAY = "agent_message_delay"
    AGENT_MESSAGE_LOSS = "agent_message_loss"


class FaultMode:
    FIXED = "fixed"
    PERCENTAGE = "percentage"
    COUNT = "count"
    SEQUENCE = "sequence"


class FaultConfig:
    """Strongly typed fault definition."""

    def __init__(
        self,
        fault_type: str,
        mode: str = "fixed",
        probability: float = 1.0,
        max_count: int = 1,
        steps: Optional[List[int]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        target: Optional[str] = None,
    ):
        self.fault_type = fault_type
        self.mode = mode
        self.probability = probability
        self.max_count = max_count
        self.steps = steps or [1]
        self.parameters = parameters or {}
        if error_message:
            self.parameters["error_message"] = error_message
        self.target = target or "*"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "probability": self.probability,
            "max_count": self.max_count,
            "steps": self.steps,
            "parameters": self.parameters,
        }


class FaultEngine:
    """
    Evaluates and injects deterministic faults during simulation based on a seeded pseudorandom sequence.
    """

    def __init__(
        self,
        fault_config: Optional[Dict[str, Any]] = None,
        faults: Optional[List[Any]] = None,
        seed: int = 42,
    ):
        self.seed = seed
        self.rng = random.Random(seed)
        self.injected_faults: List[Dict[str, Any]] = []
        self._step_counter = 0

        self.fault_config = dict(fault_config or {})
        if faults:
            for f in faults:
                if isinstance(f, FaultConfig):
                    key = f"{f.fault_type}:{f.target}" if f.target != "*" else f.fault_type
                    self.fault_config[key] = f.to_dict()
                elif isinstance(f, dict):
                    ft = f.get("fault_type")
                    if ft:
                        self.fault_config[ft] = f

    def should_inject(self, fault_type: str, target: str = "*", step_index: Optional[int] = None) -> bool:
        """Convenience method returning boolean indicating whether fault triggers."""
        return self.should_inject_fault(fault_type, target, step_index) is not None


    def should_inject_fault(
        self,
        fault_type: str,
        target: str,
        step_index: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Determines whether a fault should trigger according to deterministic rules.
        """
        if fault_type not in SUPPORTED_FAULTS:
            logger.warning(f"[FaultEngine] Unsupported fault type requested: '{fault_type}'")
            return None

        # Check if configured
        cfg = self.fault_config.get(fault_type) or self.fault_config.get(f"{fault_type}:{target}")
        if not cfg:
            return None

        mode = cfg.get("mode", "fixed")  # fixed, percentage, count, sequence
        parameters = cfg.get("parameters", {})
        trigger = False

        if mode == "fixed":
            trigger = bool(cfg.get("enabled", True))
        elif mode == "percentage":
            prob = float(cfg.get("probability", 1.0))
            # Use deterministic seeded roll
            roll = self.rng.random()
            trigger = roll <= prob
        elif mode == "count":
            max_count = int(cfg.get("max_count", 1))
            current_count = sum(1 for f in self.injected_faults if f["fault_type"] == fault_type and f["target"] == target)
            trigger = current_count < max_count
        elif mode == "sequence":
            target_steps = cfg.get("steps", [1])
            curr_step = step_index if step_index is not None else self._step_counter
            trigger = curr_step in target_steps

        if trigger:
            record = {
                "id": str(uuid.uuid4()),
                "fault_type": fault_type,
                "target": target,
                "parameters": parameters,
                "trigger_condition": {"mode": mode, "config": cfg},
                "injected_at": datetime.now(timezone.utc),
                "result": "injected",
            }
            self.injected_faults.append(record)
            logger.info(f"[FaultEngine] Injected fault '{fault_type}' into target '{target}'.")
            return record

        return None

    def get_injected_records(self) -> List[Dict[str, Any]]:
        return list(self.injected_faults)
