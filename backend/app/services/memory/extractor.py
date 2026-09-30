"""
Extracts candidate memories from task context, user directives, and tool workflows.
Never exposes chain-of-thought or raw internal reasoning.
"""
import re
from typing import List, Optional
from uuid import UUID

from backend.app.services.memory.classifier import MemoryClassifier
from backend.app.services.memory.schemas import (
    CandidateMemory,
    MemoryImportance,
    MemoryScope,
    MemorySourceType,
    MemoryType,
)

PREFERENCE_TRIGGER_PATTERNS = [
    (re.compile(r"(?i)\b(?:always|prefer|preference|remember to|use|please use)\s+([a-zA-Z0-9_\-\.\s]{4,60})\s+(?:instead of|rather than|not)\s+([a-zA-Z0-9_\-\.\s]{4,60})\b"), "preference"),
    (re.compile(r"(?i)\b(?:my preferred|our standard|we use|default to)\s+([a-zA-Z0-9_\-\.\s]{4,80})\b"), "preference"),
    (re.compile(r"(?i)\b(?:note that|important fact|key architectural decision|decided to)\s+([^\.\n]{10,120})\b"), "decision"),
    (re.compile(r"(?i)\b(?:api endpoint|base url|service convention)\s+([^\.\n]{10,100})\b"), "technical_fact"),
]


class MemoryExtractor:
    """
    Extracts candidate structured memories from task prompts, interactions, or outputs.
    Safety constraint: NEVER includes chain-of-thought in output or reason.
    """

    @classmethod
    def extract_candidates_from_text(
        cls,
        text: str,
        source_type: MemorySourceType = MemorySourceType.TASK,
        source_id: Optional[str] = None,
        project_id: Optional[UUID] = None,
        default_scope: MemoryScope = MemoryScope.USER,
    ) -> List[CandidateMemory]:
        if not text or len(text.strip()) < 10:
            return []

        candidates: List[CandidateMemory] = []

        # 1. Deterministic heuristic pattern matching for common conventions and preferences
        for pattern, mem_type_str in PREFERENCE_TRIGGER_PATTERNS:
            matches = pattern.findall(text)
            for match in matches[:2]:  # Limit candidates
                if isinstance(match, tuple):
                    favored, alternative = match[0].strip(), match[1].strip()
                    title = f"Preference: {favored.capitalize()} over {alternative.capitalize()}"
                    content = f"Prefer {favored} instead of {alternative} for future tasks."
                    reason = "Identified recurring tool or library preference from task directive."
                else:
                    fact = match.strip()
                    title = f"Key Fact: {fact[:50].capitalize()}"
                    content = fact
                    reason = "Identified important technical context or convention."

                # Safety check via classifier
                classification = MemoryClassifier.classify(title, content, source_type=source_type.value)
                if classification.status == "rejected":
                    continue

                candidates.append(
                    CandidateMemory(
                        type=MemoryType(mem_type_str),
                        scope=default_scope,
                        title=title,
                        content=content,
                        reason=reason,
                        confidence=0.85,
                        source_type=source_type,
                        source_id=source_id,
                        importance=MemoryImportance.MEDIUM,
                        requires_confirmation=True,
                        project_id=project_id,
                    )
                )

        return candidates
