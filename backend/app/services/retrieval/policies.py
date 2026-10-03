from __future__ import annotations
from abc import ABC, abstractmethod
import re
from typing import Any, List, Optional, TYPE_CHECKING
from uuid import UUID

from backend.app.config import settings
from backend.app.db.models.task import Task
from backend.app.services.retrieval.decision import (
    RetrievalDecision,
    RetrievalMode,
    RetrievalScope,
    RetrievalStrategy,
)

if TYPE_CHECKING:
    from backend.app.services.context.models import ContextItem


class RetrievalDecisionProvider(ABC):
    """
    Abstract interface for retrieval decision engines.
    Enables pluggable routing strategies (RuleBased, LLM-based, or Hybrid)
    without modifying the RetrievalRouter or ContextEngine.
    """

    @abstractmethod
    async def decide(
        self,
        task: Task,
        context_items: Optional[List[ContextItem]] = None,
        **kwargs: Any,
    ) -> RetrievalDecision:
        """
        Evaluates task instructions, context signals, and parameters
        to return a structured RetrievalDecision.
        """
        pass


class RuleBasedDecisionProvider(RetrievalDecisionProvider):
    """
    Deterministic rule-based decision provider.
    Combines user overrides, task intent detection, phrase structure,
    and factual grounding signals to route retrieval without LLM overhead.
    """

    # Non-retrieval closed-form directives (unless overridden by knowledge signals)
    NON_RETRIEVAL_PATTERNS = [
        re.compile(r"^\s*(hello|hi|hey|greetings|good\s+(morning|afternoon|evening))\b", re.IGNORECASE),
        re.compile(r"\bsummarize\s+(this|the\s+following|the\s+above|the\s+text\s+below|this\s+paragraph|this\s+sentence|the\s+attached)\b", re.IGNORECASE),
        re.compile(r"\b(fix|correct)\s+(the\s+)?(spelling|grammar|typo|punctuation)\b", re.IGNORECASE),
        re.compile(r"\btranslate\s+(this|the\s+following)\s+(to|into)\b", re.IGNORECASE),
        re.compile(r"\b(write|generate)\s+a\s+(poem|haiku|short\s+story|joke|greeting)\b", re.IGNORECASE),
        re.compile(r"^\s*(calculate|compute|solve|what\s+is)\s+[0-9\+\-\*\/\^\(\)\s\.\=]+$", re.IGNORECASE),
    ]

    # Exact match / phrase search signals
    EXACT_PHRASE_PATTERNS = [
        re.compile(r"\b(find|search|lookup|look\s+up|locate)\s+(the\s+)?(exact\s+phrase|exact\s+match|verbatim|literal|exact\s+text)\b", re.IGNORECASE),
        re.compile(r"\bexact\s+phrase\b", re.IGNORECASE),
        re.compile(r"\bfind\s+the\s+exact\b", re.IGNORECASE),
        re.compile(r"\bwhere\s+does\s+it\s+(say|mention|state|contain)\b", re.IGNORECASE),
        re.compile(r"\bsearch\s+for\s+the\s+phrase\b", re.IGNORECASE),
        re.compile(r"\bverbatim\s+match\b", re.IGNORECASE),
    ]

    # Semantic concept / conceptual understanding signals
    SEMANTIC_CONCEPT_PATTERNS = [
        re.compile(r"\bexplain\s+(the\s+)?concepts?\b", re.IGNORECASE),
        re.compile(r"\bconceptually\s+(explain|describe|analyze)\b", re.IGNORECASE),
        re.compile(r"\bhigh[- ]level\s+(overview|understanding|explanation|summary\s+of\s+concepts?)\b", re.IGNORECASE),
        re.compile(r"\bdescribe\s+(the\s+)?(concept|idea|principles?)\b", re.IGNORECASE),
        re.compile(r"\bsemantic\s+(meaning|similarity|relationships?)\b", re.IGNORECASE),
    ]

    # Multi-faceted / comprehensive inquiry signals
    MULTI_QUERY_PATTERNS = [
        re.compile(r"\b(comprehensive\s+overview|all\s+aspects\s+of|multi[- ]part\s+analysis)\b", re.IGNORECASE),
        re.compile(r"\b(investigate\s+everything\s+about|explore\s+multiple\s+perspectives)\b", re.IGNORECASE),
        re.compile(r"\b(thorough\s+and\s+exhaustive\s+review|in[- ]depth\s+multi[- ]angle)\b", re.IGNORECASE),
    ]

    # Explicit project knowledge / codebase grounding signals
    PROJECT_KNOWLEDGE_PATTERNS = [
        re.compile(r"\b(our|in\s+our|from\s+our)\s+(project|documentation|docs|codebase|implementation|repo|app|api|jwt|auth|system|architecture|backend|frontend|service)\b", re.IGNORECASE),
        re.compile(r"\b(what\s+does\s+our|how\s+does\s+our|where\s+in\s+our|compare\s+our)\b", re.IGNORECASE),
        re.compile(r"\b(uploaded\s+documentation|project\s+documentation|project\s+knowledge\s+base|project\s+files)\b", re.IGNORECASE),
        re.compile(r"\b(compare|contrast)\s+.+\s+(with|against)\s+.+\b", re.IGNORECASE),
        re.compile(r"\b(how\s+do\s+we|how\s+does\s+the\s+system|what\s+is\s+the\s+implementation)\b", re.IGNORECASE),
        re.compile(r"\b(architecture|specification|requirements|endpoints?|schemas?|config|pipeline)\b", re.IGNORECASE),
    ]

    # Workspace-wide scope signals
    WORKSPACE_SCOPE_PATTERNS = [
        re.compile(r"\b(across\s+all\s+projects|entire\s+workspace|all\s+projects|workspace[- ]wide|in\s+the\s+workspace)\b", re.IGNORECASE),
        re.compile(r"\b(across\s+workspaces?|global\s+workspace)\b", re.IGNORECASE),
    ]

    # Graph relationship and entity dependency signals
    GRAPH_RELATIONSHIP_PATTERNS = [
        re.compile(r"\b(what|which)\s+(services?|apps?|components?|modules?|apis?|endpoints?)\s+(depend\s+on|use|call|import|invoke)\b", re.IGNORECASE),
        re.compile(r"\b(dependencies|dependency\s+tree|dependency\s+graph|depend\s+on|depends\s+on)\b", re.IGNORECASE),
        re.compile(r"\b(who\s+owns|ownership\s+of|owned\s+by|assigned\s+to|created\s+by)\b", re.IGNORECASE),
        re.compile(r"\b(what\s+is\s+connected\s+to|how\s+are\s+.+\s+connected|relationship\s+between|entity\s+relationship)\b", re.IGNORECASE),
        re.compile(r"\b(belongs\s+to|member\s+of|part\s+of|deployed\s+to|configured\s+by)\b", re.IGNORECASE),
        re.compile(r"\bknowledge\s+graph\b", re.IGNORECASE),
    ]

    # Multimodal artifact directives (screenshots, audio, spreadsheets, video)
    MULTIMODAL_PATTERNS = [
        re.compile(r"\b(screenshot(\s+error)?|in\s+this\s+screenshot|analyze\s+this\s+image|diagram\s+shown)\b", re.IGNORECASE),
        re.compile(r"\b(meeting\s+recording|audio\s+file|what\s+does\s+this\s+meeting\s+recording\s+say|transcribe\s+this\s+audio)\b", re.IGNORECASE),
        re.compile(r"\b(spreadsheet|csv|xlsx|excel\s+sheet|analyze\s+this\s+spreadsheet)\b", re.IGNORECASE),
        re.compile(r"\b(video\s+clip|keyframes?|scenes?\s+in\s+this\s+video)\b", re.IGNORECASE),
    ]

    async def decide(
        self,
        task: Task,
        context_items: Optional[List[ContextItem]] = None,
        **kwargs: Any,
    ) -> RetrievalDecision:
        """
        Determines the retrieval decision using deterministic priority rules.
        """
        # 1. Extract combined text representation
        task_text = self._extract_task_text(task, **kwargs)
        clean_text = task_text.strip()

        # 2. Extract user settings & overrides
        mode_val = kwargs.get("retrieval_mode")
        if mode_val is None and hasattr(task, "metadata_json") and task.metadata_json:
            mode_val = task.metadata_json.get("retrieval_mode")

        # Handle backward-compatible boolean flag
        legacy_enabled = kwargs.get("retrieval_enabled")
        if mode_val is None:
            if legacy_enabled is True:
                mode_val = RetrievalMode.ALWAYS.value
            elif legacy_enabled is False:
                mode_val = RetrievalMode.AUTO.value
            else:
                mode_val = RetrievalMode.AUTO.value

        mode = str(mode_val).lower().strip()
        strategy_override = kwargs.get("retrieval_strategy")
        scope_override = kwargs.get("retrieval_scope")
        top_k_val = kwargs.get("retrieval_top_k", settings.RAG_DEFAULT_TOP_K)

        # Enforce top_k safety clamping
        top_k = self._clamp_top_k(top_k_val)

        # Determine target search query
        query = kwargs.get("query") or self._extract_clean_query(task, clean_text)

        # 3. Process Mode: NEVER
        if mode == RetrievalMode.NEVER.value:
            return RetrievalDecision(
                retrieval_required=False,
                strategy=RetrievalStrategy.NONE,
                scope=RetrievalScope.PROJECT,
                top_k=top_k,
                query=query,
                reason="Retrieval disabled by user override (mode='never').",
                confidence=1.0,
                metadata={"mode": RetrievalMode.NEVER.value},
            )

        # 4. Resolve Scope
        scope = self._resolve_scope(clean_text, scope_override, kwargs.get("retrieval_project_scope"))

        # 5. Process Mode: ALWAYS
        if mode == RetrievalMode.ALWAYS.value:
            strategy = self._parse_strategy(strategy_override) or RetrievalStrategy.HYBRID
            return RetrievalDecision(
                retrieval_required=True,
                strategy=strategy,
                scope=scope,
                top_k=top_k,
                query=query,
                reason="Retrieval explicitly requested by user override (mode='always').",
                confidence=1.0,
                metadata={"mode": RetrievalMode.ALWAYS.value, "strategy_override": bool(strategy_override)},
            )

        # 6. Process explicit Strategy override in AUTO mode
        if strategy_override:
            parsed_strat = self._parse_strategy(strategy_override)
            if parsed_strat == RetrievalStrategy.NONE:
                return RetrievalDecision(
                    retrieval_required=False,
                    strategy=RetrievalStrategy.NONE,
                    scope=scope,
                    top_k=top_k,
                    query=query,
                    reason="Explicit strategy override set to 'none'.",
                    confidence=1.0,
                    metadata={"mode": RetrievalMode.AUTO.value, "strategy_override": strategy_override},
                )
            elif parsed_strat is not None:
                return RetrievalDecision(
                    retrieval_required=True,
                    strategy=parsed_strat,
                    scope=scope,
                    top_k=top_k,
                    query=query,
                    reason=f"Retrieval enabled via explicit strategy override ('{parsed_strat.value}').",
                    confidence=1.0,
                    metadata={"mode": RetrievalMode.AUTO.value, "strategy_override": strategy_override},
                )

        # 7. Empty or missing task content -> No retrieval
        if not clean_text:
            return RetrievalDecision(
                retrieval_required=False,
                strategy=RetrievalStrategy.NONE,
                scope=scope,
                top_k=top_k,
                query="",
                reason="Task has no actionable instructions or directive text.",
                confidence=1.0,
                metadata={"mode": RetrievalMode.AUTO.value},
            )

        # 8. Check for project knowledge grounding signals FIRST
        # (If a task says "Compare our JWT implementation with documentation", it needs retrieval even if "Compare" is used)
        has_project_grounding = any(p.search(clean_text) for p in self.PROJECT_KNOWLEDGE_PATTERNS)

        # 9. Check non-retrieval patterns (only if no explicit project grounding was detected)
        if not has_project_grounding:
            for pat in self.NON_RETRIEVAL_PATTERNS:
                if pat.search(clean_text):
                    return RetrievalDecision(
                        retrieval_required=False,
                        strategy=RetrievalStrategy.NONE,
                        scope=scope,
                        top_k=top_k,
                        query=query,
                        reason="Task is a closed-form/conversational directive not requiring external knowledge retrieval.",
                        confidence=0.95,
                        metadata={"matched_pattern": pat.pattern},
                    )

        # 10. Check Graph Relationship & Dependency Patterns
        for pat in self.GRAPH_RELATIONSHIP_PATTERNS:
            if pat.search(clean_text):
                strat = RetrievalStrategy.HYBRID_GRAPH if has_project_grounding else RetrievalStrategy.GRAPH
                return RetrievalDecision(
                    retrieval_required=True,
                    strategy=strat,
                    scope=scope,
                    top_k=top_k,
                    query=query,
                    reason="Task inquires about dependencies, entity relationships, or system component connections.",
                    confidence=0.91,
                    metadata={"matched_pattern": pat.pattern, "graph_retrieval": True},
                )

        # 11. Check Multimodal Artifact Directives
        has_artifacts = bool(kwargs.get("artifacts") or kwargs.get("artifact_ids"))
        meta = getattr(task, "metadata_json", None) or {}
        if not has_artifacts and (meta.get("artifacts") or meta.get("artifact_ids") or meta.get("input_artifacts")):
            has_artifacts = True

        for pat in self.MULTIMODAL_PATTERNS:
            if pat.search(clean_text) or has_artifacts:
                return RetrievalDecision(
                    retrieval_required=True,
                    strategy=RetrievalStrategy.MULTIMODAL,
                    scope=scope,
                    top_k=top_k,
                    query=query,
                    reason="Task directive or referenced artifacts require multimodal artifact processing.",
                    confidence=0.94,
                    metadata={"matched_pattern": pat.pattern if pat.search(clean_text) else "attached_artifacts", "multimodal": True},
                )

        # 12. Check Exact Phrase / Keyword Search Patterns
        for pat in self.EXACT_PHRASE_PATTERNS:
            if pat.search(clean_text):
                return RetrievalDecision(
                    retrieval_required=True,
                    strategy=RetrievalStrategy.KEYWORD,
                    scope=scope,
                    top_k=top_k,
                    query=self._extract_exact_phrase_target(clean_text) or query,
                    reason="Task requests exact keyword or verbatim phrase lookup in documentation.",
                    confidence=0.92,
                    metadata={"matched_pattern": pat.pattern},
                )

        # 11. Check Semantic Concept Patterns
        for pat in self.SEMANTIC_CONCEPT_PATTERNS:
            if pat.search(clean_text):
                return RetrievalDecision(
                    retrieval_required=True,
                    strategy=RetrievalStrategy.VECTOR,
                    scope=scope,
                    top_k=top_k,
                    query=query,
                    reason="Task requests high-level semantic concept explanation or overview.",
                    confidence=0.88,
                    metadata={"matched_pattern": pat.pattern},
                )

        # 12. Check Multi-Query Patterns
        for pat in self.MULTI_QUERY_PATTERNS:
            if pat.search(clean_text):
                return RetrievalDecision(
                    retrieval_required=True,
                    strategy=RetrievalStrategy.MULTI_QUERY,
                    scope=scope,
                    top_k=top_k,
                    query=query,
                    reason="Task requires multi-angle, comprehensive information synthesis across knowledge sources.",
                    confidence=0.86,
                    metadata={"matched_pattern": pat.pattern},
                )

        # 13. Project Grounding / Factual Inquiry -> Default to Hybrid
        if has_project_grounding:
            return RetrievalDecision(
                retrieval_required=True,
                strategy=RetrievalStrategy.HYBRID,
                scope=scope,
                top_k=top_k,
                query=query,
                reason="Task requires factual knowledge grounding against project documentation and codebase.",
                confidence=0.90,
                metadata={"grounding": True},
            )

        # 14. Fallback Heuristic for interrogatives / factual queries
        if self._is_interrogative_or_factual(clean_text):
            return RetrievalDecision(
                retrieval_required=True,
                strategy=RetrievalStrategy.HYBRID,
                scope=scope,
                top_k=top_k,
                query=query,
                reason="Task asks a question likely requiring knowledge retrieval grounding.",
                confidence=0.80,
                metadata={"heuristic": "interrogative"},
            )

        # 15. Default: No retrieval required for generic standalone tasks
        return RetrievalDecision(
            retrieval_required=False,
            strategy=RetrievalStrategy.NONE,
            scope=scope,
            top_k=top_k,
            query=query,
            reason="No specific knowledge retrieval triggers identified in task directive.",
            confidence=0.85,
            metadata={"default": True},
        )

    def _extract_task_text(self, task: Task, **kwargs: Any) -> str:
        parts = []
        title = getattr(task, "title", None)
        instructions = getattr(task, "instructions", None)
        description = getattr(task, "description", None)
        if title:
            parts.append(title)
        if instructions:
            parts.append(instructions)
        elif description:
            parts.append(description)
        return " ".join(parts)

    def _extract_clean_query(self, task: Task, full_text: str) -> str:
        instructions = getattr(task, "instructions", None)
        title = getattr(task, "title", None)
        if instructions and instructions.strip():
            return instructions.strip()
        if title and title.strip():
            return title.strip()
        return full_text.strip()

    def _extract_exact_phrase_target(self, text: str) -> Optional[str]:
        # Extract quoted substrings if available, e.g. 'refresh token' or "refresh token"
        quotes = re.findall(r"['\"]([^'\"]{2,})['\"]", text)
        if quotes:
            return quotes[0].strip()
        return None

    def _resolve_scope(
        self,
        text: str,
        scope_override: Optional[str],
        project_scope_flag: Optional[bool] = None,
    ) -> RetrievalScope:
        if scope_override:
            normalized = scope_override.lower().strip()
            if normalized == "workspace":
                return RetrievalScope.WORKSPACE
            if normalized == "project":
                return RetrievalScope.PROJECT

        if project_scope_flag is False:
            return RetrievalScope.WORKSPACE

        for pat in self.WORKSPACE_SCOPE_PATTERNS:
            if pat.search(text):
                return RetrievalScope.WORKSPACE

        return RetrievalScope.PROJECT

    def _parse_strategy(self, strat_str: Optional[str]) -> Optional[RetrievalStrategy]:
        if not strat_str:
            return None
        clean = strat_str.lower().strip()
        try:
            return RetrievalStrategy(clean)
        except ValueError:
            return None

    def _clamp_top_k(self, top_k: Any) -> int:
        try:
            val = int(top_k)
            return max(1, min(val, settings.MAX_RETRIEVAL_TOP_K))
        except (ValueError, TypeError):
            return settings.RAG_DEFAULT_TOP_K

    def _is_interrogative_or_factual(self, text: str) -> bool:
        lower = text.lower()
        if lower.endswith("?"):
            return True
        question_starters = ("what", "how", "where", "which", "who", "why", "can we", "does our", "is there")
        return any(lower.startswith(q) for q in question_starters)
