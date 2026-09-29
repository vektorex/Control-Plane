import json
import logging
import re
import time
from typing import Any, Dict, List, Optional

from backend.app.services.evaluation.base import DeterministicEvaluator
from backend.app.services.evaluation.policies import EvaluationPolicy
from backend.app.services.evaluation.schemas import (
    CheckResult,
    CheckType,
    EvaluationContext,
    EvaluationFindingItem,
    FindingStatus,
)

logger = logging.getLogger("evaluation.format")


class FormatEvaluator(DeterministicEvaluator):
    """
    FormatEvaluator validates explicit structural and formatting requirements
    (JSON, Markdown, Bullet lists, Tables, Code blocks, Required sections)
    configured on the task, without enforcing subjective personal preferences.
    """
    check_type = CheckType.FORMAT

    BULLET_REGEX = re.compile(r"(?:^|\n)\s*(?:[-*•]|\d+\.)\s+", re.MULTILINE)
    TABLE_REGEX = re.compile(r"\|.+\|\s*\n\s*\|[-:\s|]+\|", re.MULTILINE)
    CODE_FENCE_REGEX = re.compile(r"```[\w]*\n[\s\S]*?```", re.MULTILINE)

    def _extract_json_str(self, text: str) -> str:
        """Extracts candidate JSON string from markdown code blocks or plain text."""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()
        
        match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", cleaned)
        if match:
            return match.group(1)
        return cleaned

    async def evaluate(
        self,
        ctx: EvaluationContext,
        policy: EvaluationPolicy,
    ) -> CheckResult:
        start_time = time.perf_counter()
        text = (ctx.output_text or "").strip()

        # Check if empty
        if not text:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            return CheckResult(
                type=CheckType.FORMAT,
                status=FindingStatus.FAILED,
                confidence=1.0,
                description="Output is empty, violating basic format requirements.",
                issues=["Output is empty."],
                findings=[
                    EvaluationFindingItem(
                        check_type=CheckType.FORMAT,
                        status=FindingStatus.FAILED,
                        confidence=1.0,
                        description="Output is empty.",
                        evidence_ids=[],
                        metadata={"error": "empty_output"},
                    )
                ],
                duration_ms=elapsed_ms,
            )

        # Detect expected format from context or explicit instructions
        expected_format = (ctx.expected_format or "").lower().strip()
        if not expected_format:
            # Check if task instructions explicitly demand JSON/Table/List/Code
            inst_lower = (ctx.task_instructions or "").lower()
            if "return valid json" in inst_lower or "respond in json" in inst_lower or "output json" in inst_lower or "format: json" in inst_lower:
                expected_format = "json"
            elif "as a table" in inst_lower or "markdown table" in inst_lower or "format: table" in inst_lower:
                expected_format = "table"
            elif "bullet list" in inst_lower or "bullet points" in inst_lower or "bulleted list" in inst_lower:
                expected_format = "bullet_list"
            elif "code block" in inst_lower or "return only code" in inst_lower:
                expected_format = "code"

        issues: List[str] = []
        findings: List[EvaluationFindingItem] = []
        parsed_metadata: Dict[str, Any] = {"detected_format": expected_format or "free_text"}

        # 1. JSON Validation
        if expected_format == "json":
            json_str = self._extract_json_str(text)
            try:
                parsed = json.loads(json_str)
                parsed_metadata["json_valid"] = True
                parsed_metadata["json_root_type"] = type(parsed).__name__

                # Validate schema if provided
                if ctx.format_schema:
                    required_keys = ctx.format_schema.get("required", [])
                    if isinstance(parsed, dict) and required_keys:
                        missing_keys = [k for k in required_keys if k not in parsed]
                        if missing_keys:
                            msg = f"JSON is missing required schema keys: {missing_keys}"
                            issues.append(msg)
                            findings.append(
                                EvaluationFindingItem(
                                    check_type=CheckType.FORMAT,
                                    status=FindingStatus.FAILED if policy.strict_mode else FindingStatus.WARNING,
                                    confidence=1.0,
                                    description=msg,
                                    evidence_ids=[],
                                    metadata={"missing_keys": missing_keys},
                                )
                            )

            except json.JSONDecodeError as jde:
                msg = f"Output is not valid JSON: {jde}"
                issues.append(msg)
                findings.append(
                    EvaluationFindingItem(
                        check_type=CheckType.FORMAT,
                        status=FindingStatus.FAILED,
                        confidence=1.0,
                        description=msg,
                        evidence_ids=[],
                        metadata={"json_error": str(jde)},
                    )
                )

        # 2. Table Validation
        elif expected_format == "table":
            if not self.TABLE_REGEX.search(text):
                msg = "Output was requested as a Table, but no valid Markdown table structure was detected."
                issues.append(msg)
                findings.append(
                    EvaluationFindingItem(
                        check_type=CheckType.FORMAT,
                        status=FindingStatus.FAILED if policy.strict_mode else FindingStatus.WARNING,
                        confidence=0.95,
                        description=msg,
                        evidence_ids=[],
                        metadata={"format": "table"},
                    )
                )

        # 3. Bullet List Validation
        elif expected_format in ("bullet_list", "list"):
            bullets = self.BULLET_REGEX.findall(text)
            if len(bullets) < 2:
                msg = "Output was requested as a Bullet List, but contains fewer than 2 list items."
                issues.append(msg)
                findings.append(
                    EvaluationFindingItem(
                        check_type=CheckType.FORMAT,
                        status=FindingStatus.FAILED if policy.strict_mode else FindingStatus.WARNING,
                        confidence=0.95,
                        description=msg,
                        evidence_ids=[],
                        metadata={"bullet_count": len(bullets)},
                    )
                )

        # 4. Code Block Validation
        elif expected_format == "code":
            if not self.CODE_FENCE_REGEX.search(text):
                msg = "Output was requested as Code, but does not contain code block fences (```)."
                issues.append(msg)
                findings.append(
                    EvaluationFindingItem(
                        check_type=CheckType.FORMAT,
                        status=FindingStatus.FAILED if policy.strict_mode else FindingStatus.WARNING,
                        confidence=0.95,
                        description=msg,
                        evidence_ids=[],
                        metadata={"format": "code"},
                    )
                )

        # 5. Required Sections Check
        if ctx.required_sections:
            for section in ctx.required_sections:
                sec_clean = section.lower().strip()
                if sec_clean not in text.lower():
                    msg = f"Required section '{section}' is missing from output format."
                    issues.append(msg)
                    findings.append(
                        EvaluationFindingItem(
                            check_type=CheckType.FORMAT,
                            status=FindingStatus.FAILED if policy.strict_mode else FindingStatus.WARNING,
                            confidence=1.0,
                            description=msg,
                            evidence_ids=[],
                            metadata={"missing_section": section},
                        )
                    )

        # Determine overall format status
        has_failed = any(f.status == FindingStatus.FAILED for f in findings)
        has_warning = any(f.status == FindingStatus.WARNING for f in findings) or bool(issues)

        if has_failed:
            overall_status = FindingStatus.FAILED
        elif has_warning:
            overall_status = FindingStatus.WARNING
        else:
            overall_status = FindingStatus.PASSED

        desc = (
            f"Format verification passed ({expected_format or 'valid text'})."
            if overall_status == FindingStatus.PASSED
            else f"Format verification identified {len(issues)} issue(s)."
        )

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        return CheckResult(
            type=CheckType.FORMAT,
            status=overall_status,
            confidence=1.0,
            description=desc,
            issues=issues,
            findings=findings,
            metadata=parsed_metadata,
            duration_ms=elapsed_ms,
        )
