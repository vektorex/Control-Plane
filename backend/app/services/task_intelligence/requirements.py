from typing import Any, Dict, List, Optional

from backend.app.services.task_intelligence.schemas import (
    ComplexityLevel,
    ExecutionMode,
    ExecutionRequirements,
    RequirementSource,
    RequirementValue,
    TaskAnalysis,
    TaskRequirements,
    TaskType,
)


class TaskRequirementResolver:
    """
    Production-grade requirement resolver that harmonizes deterministic signals,
    LLM proposals, user instructions, and application/security policies.

    PRECEDENCE HIERARCHY:
    1. Security policy (cannot be overridden by user or model)
    2. Explicit user instruction / configuration (overrides model suggestions)
    3. Application policy (overrides model suggestions)
    4. Deterministic rules / baseline invariants (model suggestions cannot weaken)
    5. Model suggestions (advisory proposals)
    6. Conservative defaults for uncertain requirements
    """

    @classmethod
    def merge_requirements(
        cls,
        deterministic_reqs: TaskRequirements,
        llm_reqs: Optional[TaskRequirements] = None,
        user_overrides: Optional[Dict[str, Any]] = None,
        workspace_policy: Optional[Dict[str, Any]] = None,
    ) -> TaskRequirements:
        """
        Merges deterministic requirements and LLM suggestions under strict precedence.
        """
        overrides = user_overrides or {}
        policy = workspace_policy or {}

        merged = deterministic_reqs.model_copy(deep=True)

        if llm_reqs:
            # Model suggestions can add/elevate requirements if deterministic was False
            # but model suggestions CANNOT weaken hard deterministic requirements.
            fields_to_check = [
                ("web_search_required", bool),
                ("document_retrieval_required", bool),
                ("connector_required", bool),
                ("tools_required", bool),
                ("structured_output_required", bool),
                ("vision_required", bool),
                ("audio_required", bool),
                ("video_required", bool),
                ("table_required", bool),
                ("document_required", bool),
                ("multimodal_required", bool),
                ("evaluation_required", bool),
                ("human_approval_required", bool),
                ("memory_required", bool),
            ]

            for field_name, val_type in fields_to_check:
                det_item: RequirementValue = getattr(deterministic_reqs, field_name)
                llm_item: RequirementValue = getattr(llm_reqs, field_name)

                # If deterministic rule already detected it, keep deterministic rule
                if det_item.value:
                    continue

                # If deterministic did not detect, but LLM did, adopt LLM proposal
                if llm_item.value:
                    setattr(
                        merged,
                        field_name,
                        RequirementValue(
                            value=llm_item.value,
                            source=RequirementSource.LLM_ANALYSIS,
                            confidence=llm_item.confidence,
                        ),
                    )

            # Merge model capabilities without duplicates
            det_caps = set(deterministic_reqs.model_capabilities.value or [])
            llm_caps = set(llm_reqs.model_capabilities.value or [])
            combined_caps = sorted(list(det_caps.union(llm_caps)))
            merged.model_capabilities = RequirementValue(
                value=combined_caps,
                source=RequirementSource.LLM_ANALYSIS if llm_caps else RequirementSource.DETERMINISTIC_RULE,
                confidence=max(deterministic_reqs.model_capabilities.confidence, llm_reqs.model_capabilities.confidence),
            )

        # -------------------------------------------------------------
        # 2. Apply Explicit User Overrides (User intent overrides model)
        # -------------------------------------------------------------
        # Web search toggle
        if "enable_web_search" in overrides and overrides["enable_web_search"] is not None:
            merged.web_search_required = RequirementValue(
                value=bool(overrides["enable_web_search"]),
                source=RequirementSource.USER,
                confidence=1.0,
            )

        # Retrieval mode override
        ret_mode = overrides.get("retrieval_mode")
        if ret_mode == "never":
            merged.document_retrieval_required = RequirementValue(
                value=False,
                source=RequirementSource.USER,
                confidence=1.0,
            )
        elif ret_mode == "always":
            merged.document_retrieval_required = RequirementValue(
                value=True,
                source=RequirementSource.USER,
                confidence=1.0,
            )

        # Tool mode override
        tool_mode = overrides.get("tool_mode")
        if tool_mode == "disabled":
            merged.tools_required = RequirementValue(
                value=False,
                source=RequirementSource.USER,
                confidence=1.0,
            )
            # If tools disabled, web search is also disabled unless explicitly turned on
            if overrides.get("enable_web_search") is not True:
                merged.web_search_required = RequirementValue(
                    value=False,
                    source=RequirementSource.USER,
                    confidence=1.0,
                )
        elif tool_mode == "enabled":
            merged.tools_required = RequirementValue(
                value=True,
                source=RequirementSource.USER,
                confidence=1.0,
            )

        # Evaluation mode override
        if "evaluation_mode" in overrides and overrides["evaluation_mode"] is not None:
            eval_mode = str(overrides["evaluation_mode"]).lower()
            merged.evaluation_mode = RequirementValue(
                value=eval_mode,
                source=RequirementSource.USER,
                confidence=1.0,
            )
            merged.evaluation_required = RequirementValue(
                value=bool(eval_mode != "off"),
                source=RequirementSource.USER,
                confidence=1.0,
            )

        # Expected format override
        if "expected_format" in overrides and overrides["expected_format"]:
            fmt = str(overrides["expected_format"]).lower()
            if fmt in ("json", "table", "csv"):
                merged.structured_output_required = RequirementValue(
                    value=True,
                    source=RequirementSource.USER,
                    confidence=1.0,
                )

        # -------------------------------------------------------------
        # 1. Apply Security & Workspace Policies (Overrides user and model)
        # -------------------------------------------------------------
        # Workspace policy: disallowed web search
        if policy.get("allow_web_search") is False:
            merged.web_search_required = RequirementValue(
                value=False,
                source=RequirementSource.POLICY,
                confidence=1.0,
            )

        # Workspace policy: disallowed external connectors
        if policy.get("allow_connectors") is False:
            merged.connector_required = RequirementValue(
                value=False,
                source=RequirementSource.POLICY,
                confidence=1.0,
            )

        # Workspace policy: forced evaluation
        if policy.get("force_evaluation") is True:
            merged.evaluation_required = RequirementValue(
                value=True,
                source=RequirementSource.POLICY,
                confidence=1.0,
            )
            if merged.evaluation_mode.value == "off":
                merged.evaluation_mode = RequirementValue(
                    value="standard",
                    source=RequirementSource.POLICY,
                    confidence=1.0,
                )

        # Workspace policy: forced human approval on any external action
        if merged.human_approval_required.value:
            merged.human_approval_required = RequirementValue(
                value=True,
                source=RequirementSource.POLICY,
                confidence=1.0,
            )

        return merged

    @classmethod
    def resolve_execution_requirements(
        cls,
        analysis: TaskAnalysis,
        requirements: TaskRequirements,
        user_overrides: Optional[Dict[str, Any]] = None,
        workspace_policy: Optional[Dict[str, Any]] = None,
    ) -> ExecutionRequirements:
        """
        Converts the merged TaskRequirements and TaskAnalysis into an authoritative
        ExecutionRequirements configuration for the Orchestrator.
        """
        overrides = user_overrides or {}
        policy = workspace_policy or {}

        # 1. Resolve final execution mode
        exec_mode = analysis.suggested_execution_mode.value
        user_exec_mode = overrides.get("execution_mode")
        if user_exec_mode and user_exec_mode.lower() not in ("auto", "none"):
            exec_mode = user_exec_mode.lower()
        else:
            # Recompute mode based on merged requirements
            ret_active = bool(requirements.document_retrieval_required.value)
            tools_active = bool(requirements.tools_required.value or requirements.web_search_required.value or requirements.connector_required.value)

            if analysis.task_type == TaskType.WORKFLOW_EXECUTION or overrides.get("workflow_id"):
                exec_mode = ExecutionMode.WORKFLOW.value
            elif ret_active and tools_active:
                exec_mode = ExecutionMode.ORCHESTRATED.value
            elif tools_active:
                exec_mode = ExecutionMode.TOOL_ASSISTED.value
            elif ret_active:
                exec_mode = ExecutionMode.RETRIEVAL.value
            else:
                exec_mode = ExecutionMode.DIRECT.value

        # 2. Resolve factual complexity
        if exec_mode == ExecutionMode.DIRECT.value:
            complexity = ComplexityLevel.SIMPLE.value
        elif exec_mode in (ExecutionMode.RETRIEVAL.value, ExecutionMode.TOOL_ASSISTED.value):
            complexity = ComplexityLevel.MODERATE.value
        else:
            complexity = ComplexityLevel.COMPLEX.value

        # 3. Build retrieval configuration
        retrieval_enabled = bool(requirements.document_retrieval_required.value)
        retrieval_config = {
            "enabled": retrieval_enabled,
            "strategy": requirements.retrieval_strategy.value or ("hybrid" if retrieval_enabled else None),
            "scope": requirements.retrieval_scope.value or "project",
            "multi_query": bool(requirements.multi_query_allowed.value),
            "top_k": int(overrides.get("retrieval_top_k") or 8),
        }

        # 4. Build tools configuration
        allowed_tools = list(overrides.get("tools_enabled") or [])
        web_search_on = bool(requirements.web_search_required.value)
        if web_search_on and "web_search" not in allowed_tools:
            allowed_tools.append("web_search")

        tools_enabled = bool(requirements.tools_required.value or web_search_on)
        tools_config = {
            "enabled": tools_enabled,
            "allowed_tools": allowed_tools,
            "web_search": web_search_on,
        }

        # 5. Build connectors configuration
        connector_on = bool(requirements.connector_required.value)
        connectors_config = {
            "enabled": connector_on,
            "required_providers": ["github"] if connector_on else [],
        }

        # 6. Build memory configuration
        memory_on = bool(requirements.memory_required.value)
        memory_config = {
            "enabled": memory_on,
            "read_enabled": memory_on,
            "write_candidate": memory_on and ("remember" in analysis.intent.lower() or "save" in analysis.intent.lower()),
        }

        # 7. Build model capability requirements
        model_caps = set(requirements.model_capabilities.value or [])
        if tools_enabled or connector_on:
            model_caps.add("tools")
        if requirements.vision_required.value:
            model_caps.add("vision")
        if requirements.structured_output_required.value:
            model_caps.add("structured_output")

        model_reqs_config = {
            "capabilities": sorted(list(model_caps)),
            "min_context_tokens": int(overrides.get("max_context_tokens") or 8000),
            "structured_output": bool(requirements.structured_output_required.value),
            "vision": bool(requirements.vision_required.value),
            "requires_tools": bool(tools_enabled or connector_on),
        }

        # 8. Build evaluation configuration
        eval_enabled = bool(requirements.evaluation_required.value)
        eval_mode = requirements.evaluation_mode.value or "off"
        evaluation_config = {
            "enabled": eval_enabled,
            "mode": eval_mode,
        }

        # 9. Build human approval configuration
        hitl_on = bool(requirements.human_approval_required.value)
        human_approval_config = {
            "required": hitl_on,
            "action_type": "external_action" if hitl_on else None,
        }

        # 10. Build workflow configuration
        wf_on = bool(exec_mode == ExecutionMode.WORKFLOW.value)
        workflow_config = {
            "required": wf_on,
            "workflow_id": overrides.get("workflow_id"),
        }

        # 11. Bounded limits
        limits = {
            "max_tokens": min(int(overrides.get("max_tokens") or 8000), 16000),
            "max_iterations": min(int(overrides.get("max_agent_iterations") or 3), 5),
            "timeout_seconds": 60,
        }

        return ExecutionRequirements(
            execution_mode=exec_mode,
            task_type=analysis.task_type.value,
            complexity=complexity,
            retrieval=retrieval_config,
            tools=tools_config,
            connectors=connectors_config,
            memory=memory_config,
            model_requirements=model_reqs_config,
            evaluation=evaluation_config,
            human_approval=human_approval_config,
            workflow=workflow_config,
            streaming=bool(requirements.streaming_required.value),
            structured_output=bool(requirements.structured_output_required.value),
            limits=limits,
            version="1.0",
        )
