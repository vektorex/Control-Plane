import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.app.services.task_intelligence.confidence import ConfidenceCalculator
from backend.app.services.task_intelligence.schemas import (
    ComplexityLevel,
    ExecutionMode,
    RequirementSource,
    RequirementValue,
    TaskAnalysis,
    TaskAnalysisRequirementsSummary,
    TaskRequirements,
    TaskType,
)


class RuleBasedTaskAnalyzer:
    """
    Production-grade deterministic task analyzer using conservative, pattern-based signals.
    Detects knowledge requirements, tools, connectors, vision, memory, structured output,
    HITL external action candidates, and classifies task intent and complexity.
    """

    # Keyword / Pattern definitions
    WEB_SEARCH_PATTERNS = [
        r"\b(?:search\s+(?:the\s+)?web|search\s+online|browse\s+(?:the\s+)?web|look\s+up\s+online)\b",
        r"\b(?:latest|current|today'?s?|recent|breaking\s+news|what\s+happened\s+today|news\s+about)\b",
        r"\b(?:stock\s+price|live\s+data|weather\s+(?:today|now|forecast))\b",
    ]

    DOCUMENT_RETRIEVAL_PATTERNS = [
        r"\b(?:(?:from|with|in)\s+(?:my\s+)?documents?|in\s+(?:the\s+)?pdf|search\s+(?:my\s+)?documentation)\b",
        r"\b(?:uploaded\s+files?|in\s+my\s+files?|from\s+the\s+uploaded\s+doc(?:ument)?s?|my\s+documents?)\b",
        r"\b(?:knowledge\s*base|reference\s+(?:manual|guide|doc)|internal\s+docs?)\b",
    ]

    CONNECTOR_PATTERNS = [
        r"\b(?:from\s+my\s+github|github\s+repo(?:sitory)?|github\s+issue|github\s+pr|pull\s+request)\b",
        r"\b(?:git\s+repo|repository\s+commits?|github\s+discussions?)\b",
        r"\b(?:jira\s+ticket|slack\s+channel|linear\s+issue|notion\s+page)\b",
    ]

    STRUCTURED_OUTPUT_PATTERNS = [
        r"\b(?:return\s+json|in\s+json\s+format|output\s+as\s+json|as\s+a\s+json\s+object)\b",
        r"\b(?:json\s+schema|structured\s+format|in\s+a\s+table|markdown\s+table|csv\s+format)\b",
    ]

    VISION_PATTERNS = [
        r"\b(?:analyze\s+this\s+(?:image|screenshot|picture|photo)|look\s+at\s+this\s+(?:picture|image|photo|screenshot))\b",
        r"\b(?:(?:in\s+)?this\s+screenshot|screenshot|image\s+of|diagram\s+shown|inspect\s+the\s+graphic|screenshot\s+error)\b",
    ]

    AUDIO_PATTERNS = [
        r"\b(?:transcribe|transcript|audio|listen\s+to|voice\s+note|recording|meeting\s+recording|podcast|mp3|wav|m4a)\b",
    ]

    VIDEO_PATTERNS = [
        r"\b(?:video|mp4|webm|scenes?|keyframes?|watch\s+this\s+clip)\b",
    ]

    TABLE_PATTERNS = [
        r"\b(?:csv|xlsx|excel|spreadsheet|structured\s+table|rows\s+and\s+columns|sheets?|revenue\s+trend)\b",
    ]

    MEMORY_PATTERNS = [
        r"\b(?:remember\s+this|save\s+(?:this\s+)?preference|store\s+(?:this\s+)?in\s+memory)\b",
        r"\b(?:use\s+my\s+usual\s+(?:coding\s+)?style|as\s+usual|recall\s+my\s+preferences?)\b",
        r"\b(?:in\s+future\s+remember|keep\s+in\s+mind\s+for\s+next\s+time)\b",
    ]

    EXTERNAL_ACTION_PATTERNS = [
        r"\b(?:create\s+(?:a\s+)?(?:github\s+issue|ticket|pr|commit|repo))\b",
        r"\b(?:send\s+(?:an?\s+)?(?:email|slack\s+message|webhook)|post\s+(?:to|message))\b",
        r"\b(?:delete\s+(?:file|database|record|deployment)|update\s+(?:record|row|database))\b",
        r"\b(?:deploy\s+(?:to\s+production|service)|merge\s+pull\s+request|push\s+to\s+main)\b",
    ]

    TASK_TYPE_HEURISTICS = [
        (TaskType.WORKFLOW_EXECUTION, [r"\b(?:run\s+workflow|trigger\s+workflow|execute\s+pipeline|run\s+pipeline)\b"]),
        (TaskType.DEBUGGING, [r"\b(?:debug|fix\s+(?:the\s+)?bug|fix\s+error|traceback|syntaxerror|exception|why\s+is\s+this\s+failing)\b"]),
        (TaskType.CODING, [r"\b(?:write\s+code|implement|create\s+(?:a\s+)?(?:function|class|script|api)|python\s+code|javascript|typescript)\b"]),
        (TaskType.RESEARCH, [r"\b(?:research|investigate|find\s+information|deep\s+dive|survey|explore\s+recent)\b"]),
        (TaskType.SUMMARIZATION, [r"\b(?:summarize|summary|tldr|tl;dr|brief\s+overview|key\s+takeaways|recap)\b"]),
        (TaskType.DOCUMENT_ANALYSIS, [r"\b(?:analyze\s+(?:the\s+)?document|review\s+contract|audit\s+pdf|policy\s+review)\b"]),
        (TaskType.DATA_ANALYSIS, [r"\b(?:analyze\s+(?:this\s+)?(?:data|csv|spreadsheet|dataset)|statistics|compute\s+metrics|trend\s+analysis|visualize\s+data)\b"]),
        (TaskType.EXTRACTION, [r"\b(?:extract\s+entities|extract\s+all|parse\s+(?:out|from)|pull\s+out|gather\s+list\s+of)\b"]),
        (TaskType.COMPARISON, [r"\b(?:compare|differences?\s+between|pros\s+and\s+cons|versus|\bvs\b|tradeoffs?)\b"]),
        (TaskType.TRANSFORMATION, [r"\b(?:convert|translate|reformat|transform\s+(?:to|into)|rewrite\s+as)\b"]),
        (TaskType.PLANNING, [r"\b(?:create\s+(?:a\s+)?plan|roadmap|step\s*by\s*step\s+plan|strategy|project\s+plan)\b"]),
        (TaskType.CONTENT_GENERATION, [r"\b(?:write\s+(?:a\s+)?(?:blog|essay|article|story|letter)|draft\s+(?:an?\s+)?email|generate\s+content)\b"]),
        (TaskType.QUESTION_ANSWERING, [r"\b(?:what\s+is|how\s+to|how\s+do\s+I|explain|why\s+does|can\s+you\s+tell\s+me)\b"]),
    ]

    def __init__(self) -> None:
        # Precompile regex for peak efficiency
        self._compiled_web_search = [re.compile(p, re.IGNORECASE) for p in self.WEB_SEARCH_PATTERNS]
        self._compiled_doc_retrieval = [re.compile(p, re.IGNORECASE) for p in self.DOCUMENT_RETRIEVAL_PATTERNS]
        self._compiled_connectors = [re.compile(p, re.IGNORECASE) for p in self.CONNECTOR_PATTERNS]
        self._compiled_structured_out = [re.compile(p, re.IGNORECASE) for p in self.STRUCTURED_OUTPUT_PATTERNS]
        self._compiled_vision = [re.compile(p, re.IGNORECASE) for p in self.VISION_PATTERNS]
        self._compiled_audio = [re.compile(p, re.IGNORECASE) for p in self.AUDIO_PATTERNS]
        self._compiled_video = [re.compile(p, re.IGNORECASE) for p in self.VIDEO_PATTERNS]
        self._compiled_table = [re.compile(p, re.IGNORECASE) for p in self.TABLE_PATTERNS]
        self._compiled_memory = [re.compile(p, re.IGNORECASE) for p in self.MEMORY_PATTERNS]
        self._compiled_external_action = [re.compile(p, re.IGNORECASE) for p in self.EXTERNAL_ACTION_PATTERNS]
        self._compiled_task_types = [
            (t_type, [re.compile(p, re.IGNORECASE) for p in p_list])
            for t_type, p_list in self.TASK_TYPE_HEURISTICS
        ]

    def _matches_any(self, text: str, patterns: List[re.Pattern]) -> bool:
        return any(bool(p.search(text)) for p in patterns)

    def _find_matching_patterns(self, text: str, patterns: List[re.Pattern]) -> List[str]:
        matched = []
        for p in patterns:
            found = p.findall(text)
            if found:
                matched.extend(found if isinstance(found[0], str) else [f[0] for f in found if f])
        return matched

    def analyze(
        self,
        task_text: str,
        context_text: Optional[str] = None,
        user_overrides: Optional[Dict[str, Any]] = None,
    ) -> Tuple[TaskAnalysis, TaskRequirements]:
        """
        Execute deterministic analysis on the input task and optional context.
        Returns a tuple of (TaskAnalysis, TaskRequirements).
        """
        prompt = (task_text or "").strip()
        context = (context_text or "").strip()
        full_text = f"{prompt}\n{context}".strip()
        overrides = user_overrides or {}

        # 1. Detect capability requirements
        web_search = self._matches_any(full_text, self._compiled_web_search)
        doc_retrieval = self._matches_any(full_text, self._compiled_doc_retrieval)
        connectors = self._matches_any(full_text, self._compiled_connectors)
        structured_output = self._matches_any(full_text, self._compiled_structured_out)
        vision = self._matches_any(full_text, self._compiled_vision)
        audio = self._matches_any(full_text, self._compiled_audio)
        video = self._matches_any(full_text, self._compiled_video)
        table = self._matches_any(full_text, self._compiled_table)
        multimodal = bool(vision or audio or video or (doc_retrieval and (vision or audio)))
        memory = self._matches_any(full_text, self._compiled_memory)
        external_action = self._matches_any(full_text, self._compiled_external_action)

        # 2. Extract detected signals for confidence tracking
        detected_signals: List[str] = []
        if web_search:
            detected_signals.append("web_search")
        if doc_retrieval:
            detected_signals.append("doc_retrieval")
        if connectors:
            detected_signals.append("connectors")
        if structured_output:
            detected_signals.append("structured_output")
        if vision:
            detected_signals.append("vision")
        if audio:
            detected_signals.append("audio")
        if video:
            detected_signals.append("video")
        if table:
            detected_signals.append("table")
        if multimodal:
            detected_signals.append("multimodal")
        if memory:
            detected_signals.append("memory")
        if external_action:
            detected_signals.append("external_action")

        # 3. Classify task type
        classified_type = TaskType.UNKNOWN
        for t_type, patterns in self._compiled_task_types:
            if self._matches_any(full_text, patterns):
                classified_type = t_type
                detected_signals.append(f"type_{t_type.value}")
                break

        # Fallback task type heuristics
        if classified_type == TaskType.UNKNOWN or classified_type == TaskType.QUESTION_ANSWERING:
            if table:
                classified_type = TaskType.DATA_ANALYSIS
            elif web_search:
                classified_type = TaskType.RESEARCH
            elif doc_retrieval:
                classified_type = TaskType.DOCUMENT_ANALYSIS
            elif structured_output:
                classified_type = TaskType.EXTRACTION
            elif classified_type == TaskType.UNKNOWN:
                classified_type = TaskType.QUESTION_ANSWERING

        # 4. Determine suggested execution mode
        retrieval_active = doc_retrieval or bool(context_text)
        tools_active = web_search or connectors

        if classified_type == TaskType.WORKFLOW_EXECUTION:
            suggested_mode = ExecutionMode.WORKFLOW
        elif (retrieval_active and tools_active) or (web_search and doc_retrieval) or (connectors and doc_retrieval):
            suggested_mode = ExecutionMode.ORCHESTRATED
        elif tools_active:
            suggested_mode = ExecutionMode.TOOL_ASSISTED
        elif retrieval_active:
            suggested_mode = ExecutionMode.RETRIEVAL
        else:
            suggested_mode = ExecutionMode.DIRECT

        # 5. Classify execution complexity
        if suggested_mode == ExecutionMode.DIRECT:
            complexity = ComplexityLevel.SIMPLE
        elif suggested_mode in (ExecutionMode.RETRIEVAL, ExecutionMode.TOOL_ASSISTED):
            complexity = ComplexityLevel.MODERATE
        else:
            complexity = ComplexityLevel.COMPLEX

        # 6. Evaluation policy recommendation
        evaluation_required = False
        evaluation_mode = "off"
        if classified_type in (TaskType.RESEARCH, TaskType.CODING, TaskType.DOCUMENT_ANALYSIS, TaskType.DATA_ANALYSIS):
            evaluation_required = True
            evaluation_mode = "standard"
        elif external_action:
            evaluation_required = True
            evaluation_mode = "strict"

        # 7. Model capability requirements
        model_caps: List[str] = ["chat", "streaming"]
        if tools_active or external_action:
            model_caps.append("tools")
        if vision:
            model_caps.append("vision")
        if audio:
            model_caps.append("audio_transcription")
        if video:
            model_caps.append("video")
        if multimodal:
            model_caps.append("multimodal_input")
        if structured_output:
            model_caps.append("structured_output")
        if doc_retrieval or len(full_text.split()) > 1000:
            model_caps.append("long_context")

        # 8. Calculate confidence
        confidence = ConfidenceCalculator.evaluate_signal_confidence(
            matched_signals=detected_signals,
            total_tokens=len(full_text.split()),
        )

        # 9. Build user-safe explanation (Never expose chain of thought)
        explanation_parts = []
        if classified_type != TaskType.UNKNOWN:
            explanation_parts.append(f"Classified as {classified_type.value.replace('_', ' ')}")
        if vision:
            explanation_parts.append("requires vision / image understanding")
        if audio:
            explanation_parts.append("requires audio transcription")
        if video:
            explanation_parts.append("requires video analysis")
        if table:
            explanation_parts.append("requires structured table data analysis")
        if web_search:
            explanation_parts.append("requires web search for current information")
        if doc_retrieval:
            explanation_parts.append("requires document retrieval from knowledge base")
        if connectors:
            explanation_parts.append("requires external connector integration")
        if external_action:
            explanation_parts.append("detected potential external action requiring approval")
        if structured_output:
            explanation_parts.append("structured output format requested")
        if memory:
            explanation_parts.append("references persistent memory or user preferences")
        if not explanation_parts:
            explanation_parts.append("standard direct text generation")

        explanation = "; ".join(explanation_parts) + "."

        # Build TaskAnalysis
        analysis = TaskAnalysis(
            task_type=classified_type,
            intent=prompt[:150] if prompt else "Unspecified intent",
            requirements=TaskAnalysisRequirementsSummary(
                memory=memory,
                documents=doc_retrieval,
                web_search=web_search,
                connectors=connectors,
                tools=tools_active,
                retrieval=retrieval_active,
                evaluation=evaluation_required,
                structured_output=structured_output,
                human_approval=external_action,
            ),
            constraints=["structured_output"] if structured_output else [],
            suggested_execution_mode=suggested_mode,
            confidence=confidence,
            explanation=explanation,
            detected_entities=detected_signals,
            created_at=datetime.now(timezone.utc),
        )

        # Build fine-grained TaskRequirements with provenance tracking
        source = RequirementSource.DETERMINISTIC_RULE
        retrieval_strat = "hybrid" if doc_retrieval else None

        requirements = TaskRequirements(
            memory_required=RequirementValue(value=memory, source=source, confidence=confidence),
            document_retrieval_required=RequirementValue(value=doc_retrieval, source=source, confidence=confidence),
            web_search_required=RequirementValue(value=web_search, source=source, confidence=confidence),
            connector_required=RequirementValue(value=connectors, source=source, confidence=confidence),
            tools_required=RequirementValue(value=tools_active, source=source, confidence=confidence),
            retrieval_strategy=RequirementValue(value=retrieval_strat, source=source, confidence=confidence),
            retrieval_scope=RequirementValue(value="project", source=source, confidence=confidence),
            multi_query_allowed=RequirementValue(value=bool(doc_retrieval and web_search), source=source, confidence=confidence),
            structured_output_required=RequirementValue(value=structured_output, source=source, confidence=confidence),
            vision_required=RequirementValue(value=vision, source=source, confidence=confidence),
            audio_required=RequirementValue(value=audio, source=source, confidence=confidence),
            video_required=RequirementValue(value=video, source=source, confidence=confidence),
            table_required=RequirementValue(value=table, source=source, confidence=confidence),
            document_required=RequirementValue(value=doc_retrieval, source=source, confidence=confidence),
            multimodal_required=RequirementValue(value=multimodal, source=source, confidence=confidence),
            streaming_required=RequirementValue(value=True, source=source, confidence=1.0),
            evaluation_required=RequirementValue(value=evaluation_required, source=source, confidence=confidence),
            evaluation_mode=RequirementValue(value=evaluation_mode, source=source, confidence=confidence),
            human_approval_required=RequirementValue(value=external_action, source=source, confidence=confidence),
            workflow_required=RequirementValue(value=bool(suggested_mode == ExecutionMode.WORKFLOW), source=source, confidence=confidence),
            model_capabilities=RequirementValue(value=model_caps, source=source, confidence=confidence),
            max_execution_complexity=RequirementValue(value=complexity.value, source=source, confidence=confidence),
        )

        return analysis, requirements
