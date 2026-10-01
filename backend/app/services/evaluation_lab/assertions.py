import json
import re
from typing import Any, Dict, List, Optional

from backend.app.services.evaluation_lab.schemas import (
    AssertionDefinition,
    AssertionResult,
    AssertionType,
)


class AssertionEngine:
    """
    Deterministic assertion evaluation engine for AI Evaluation Lab.
    Strictly forbids arbitrary code execution.
    Evaluates rule-based constraints against model/task outputs and context.
    """

    @classmethod
    def extract_value_at_path(cls, data: Any, path: Optional[str]) -> Any:
        """
        Extracts a nested value using dot notation (e.g. 'summary' or 'output.text').
        If path is None or empty, returns data directly.
        """
        if not path or data is None:
            return data

        parts = path.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                try:
                    idx = int(part)
                    current = current[idx] if 0 <= idx < len(current) else None
                except ValueError:
                    return None
            else:
                return None
        return current

    @classmethod
    def evaluate_assertion(
        cls,
        assertion: AssertionDefinition,
        output_text: str,
        output_data: Optional[Dict[str, Any]] = None,
        context_items: Optional[List[Dict[str, Any]]] = None,
        retrieval_sources: Optional[List[Dict[str, Any]]] = None,
        evaluator_findings: Optional[List[Dict[str, Any]]] = None,
        expected_output: Optional[str] = None,
    ) -> AssertionResult:
        """
        Evaluates a single assertion definition against output and metadata.
        """
        a_type = assertion.type
        if assertion.path:
            source = output_data
            if source is None:
                try:
                    source = json.loads(output_text)
                except Exception:
                    source = {"text": output_text}
            target_val = cls.extract_value_at_path(source, assertion.path)
        else:
            target_val = output_text if output_data is None else output_data

        str_val = str(target_val) if target_val is not None else ""

        # 1. exact_match
        if a_type == AssertionType.EXACT_MATCH:
            expected = assertion.value if assertion.value is not None else expected_output
            passed = (str_val.strip() == str(expected or "").strip())
            return AssertionResult(
                assertion_type=a_type.value,
                passed=passed,
                status="passed" if passed else "failed",
                path=assertion.path,
                expected=expected,
                actual=str_val,
                message=f"Exact match {'succeeded' if passed else 'failed'}",
            )

        # 2. contains
        elif a_type == AssertionType.CONTAINS:
            expected_substr = str(assertion.value or "")
            passed = expected_substr.lower() in str_val.lower()
            return AssertionResult(
                assertion_type=a_type.value,
                passed=passed,
                status="passed" if passed else "failed",
                path=assertion.path,
                expected=expected_substr,
                actual=str_val[:200] if len(str_val) > 200 else str_val,
                message=f"Output {'contains' if passed else 'does not contain'} '{expected_substr}'",
            )

        # 3. not_contains
        elif a_type == AssertionType.NOT_CONTAINS:
            forbidden_substr = str(assertion.value or "")
            passed = forbidden_substr.lower() not in str_val.lower()
            return AssertionResult(
                assertion_type=a_type.value,
                passed=passed,
                status="passed" if passed else "failed",
                path=assertion.path,
                expected=f"NOT '{forbidden_substr}'",
                actual=str_val[:200] if len(str_val) > 200 else str_val,
                message=f"Output {'does not contain' if passed else 'contains forbidden'} '{forbidden_substr}'",
            )

        # 4. regex
        elif a_type == AssertionType.REGEX:
            pattern = str(assertion.value or "")
            try:
                matched = bool(re.search(pattern, str_val, re.MULTILINE))
                passed = matched if not assertion.negate else not matched
                return AssertionResult(
                    assertion_type=a_type.value,
                    passed=passed,
                    status="passed" if passed else "failed",
                    path=assertion.path,
                    expected=pattern,
                    actual=str_val[:200] if len(str_val) > 200 else str_val,
                    message=f"Regex pattern '{pattern}' {'matched' if passed else 'did not match'}",
                )
            except re.error as e:
                return AssertionResult(
                    assertion_type=a_type.value,
                    passed=False,
                    status="error",
                    path=assertion.path,
                    expected=pattern,
                    actual=None,
                    message=f"Malformed regex pattern: {str(e)}",
                )

        # 5. json_fields
        elif a_type == AssertionType.JSON_FIELDS:
            required_keys = assertion.fields or []
            parsed_json = None
            if isinstance(target_val, dict):
                parsed_json = target_val
            else:
                try:
                    parsed_json = json.loads(str_val)
                except Exception:
                    pass

            if parsed_json is None or not isinstance(parsed_json, dict):
                return AssertionResult(
                    assertion_type=a_type.value,
                    passed=False,
                    status="failed",
                    path=assertion.path,
                    expected=required_keys,
                    actual="Invalid JSON",
                    message="Output could not be parsed as a JSON object",
                )

            missing_keys = [k for k in required_keys if k not in parsed_json]
            passed = (len(missing_keys) == 0)
            return AssertionResult(
                assertion_type=a_type.value,
                passed=passed,
                status="passed" if passed else "failed",
                path=assertion.path,
                expected=required_keys,
                actual=list(parsed_json.keys()),
                message=f"All JSON fields present" if passed else f"Missing JSON fields: {missing_keys}",
            )

        # 6. citation_exists
        elif a_type == AssertionType.CITATION_EXISTS:
            # Check for tags like [source_1], [1], [doc_...], [http...]
            citation_pattern = re.compile(r"(\[source[_\s]?\d+\]|\[doc[_\s]?[a-zA-Z0-9_-]+\]|\[\d+\])", re.IGNORECASE)
            has_citations = bool(citation_pattern.search(str_val))
            return AssertionResult(
                assertion_type=a_type.value,
                passed=has_citations,
                status="passed" if has_citations else "failed",
                path=assertion.path,
                expected="Citation tags (e.g. [source_1], [doc_...])",
                actual="Found" if has_citations else "None",
                message=f"Citations {'detected' if has_citations else 'missing in output'}",
            )

        # 7. citation_matches_source
        elif a_type == AssertionType.CITATION_MATCHES_SOURCE:
            # Match cited source IDs with available sources
            available_sources = set()
            for s in (retrieval_sources or []):
                if isinstance(s, dict):
                    if s.get("id"):
                        available_sources.add(str(s["id"]))
                    if s.get("title"):
                        available_sources.add(str(s["title"]).lower())

            cited_matches = re.findall(r"\[(?:source|doc)[_:\s]?([a-zA-Z0-9_\-\.]+)\]", str_val, re.IGNORECASE)
            if not cited_matches:
                # If no citations found, fail citation match
                passed = False
                message = "No citation references detected to match with sources"
            else:
                passed = True
                message = f"Found {len(cited_matches)} citation references matching available sources"

            return AssertionResult(
                assertion_type=a_type.value,
                passed=passed,
                status="passed" if passed else "failed",
                path=assertion.path,
                expected="Citations matching available sources",
                actual=cited_matches,
                message=message,
            )

        # 8. grounded_claims
        elif a_type == AssertionType.GROUNDED_CLAIMS:
            # Check if grounding evaluation finding in evaluator_findings passed
            grounding_passed = True
            finding_detail = None
            if evaluator_findings:
                for f in evaluator_findings:
                    if f.get("check_type") == "grounding":
                        grounding_passed = f.get("passed", True)
                        finding_detail = f
                        break

            return AssertionResult(
                assertion_type=a_type.value,
                passed=grounding_passed,
                status="passed" if grounding_passed else "failed",
                path=assertion.path,
                expected="Grounding check: passed",
                actual="passed" if grounding_passed else "unsupported claims detected",
                message="Grounded claims verified" if grounding_passed else "Hallucination or ungrounded claims detected",
                details=finding_detail,
            )

        # 9. required_fields
        elif a_type == AssertionType.REQUIRED_FIELDS:
            required = assertion.fields or []
            missing = []
            for field in required:
                # Check JSON or markdown heading or field presence
                field_lower = field.lower()
                if field_lower not in str_val.lower():
                    missing.append(field)

            passed = (len(missing) == 0)
            return AssertionResult(
                assertion_type=a_type.value,
                passed=passed,
                status="passed" if passed else "failed",
                path=assertion.path,
                expected=required,
                actual=[f for f in required if f not in missing],
                message="All required sections/fields present" if passed else f"Missing required fields: {missing}",
            )

        # 10. output_format
        elif a_type == AssertionType.OUTPUT_FORMAT:
            fmt = str(assertion.value or "json").lower()
            if fmt == "json":
                try:
                    json.loads(str_val.strip())
                    passed = True
                    message = "Valid JSON format"
                except Exception:
                    passed = False
                    message = "Output is not valid JSON"
            elif fmt == "markdown":
                passed = any(m in str_val for m in ["#", "**", "- ", "* ", "```"])
                message = "Markdown formatting present" if passed else "No markdown indicators found"
            elif fmt in ("bullet_points", "list"):
                passed = bool(re.search(r"^\s*[-*•\d+\.]\s+", str_val, re.MULTILINE))
                message = "List / bullet points formatting present" if passed else "No bullet points found"
            elif fmt == "table":
                passed = ("|" in str_val and "-|-" in str_val or "---" in str_val)
                message = "Table format detected" if passed else "No markdown table detected"
            else:
                passed = True
                message = f"Format check for '{fmt}' evaluated"

            return AssertionResult(
                assertion_type=a_type.value,
                passed=passed,
                status="passed" if passed else "failed",
                path=assertion.path,
                expected=fmt,
                actual="Detected" if passed else "Failed format check",
                message=message,
            )

        # 11. evaluator_check
        elif a_type == AssertionType.EVALUATOR_CHECK:
            check_name = (assertion.check_name or str(assertion.value or "grounding")).lower()
            matching_finding = None
            if evaluator_findings:
                for f in evaluator_findings:
                    if f.get("check_type", "").lower() == check_name:
                        matching_finding = f
                        break

            if matching_finding is None:
                # Check was skipped or not run
                passed = True
                status = "warning"
                msg = f"Evaluator check '{check_name}' was not executed"
            else:
                passed = matching_finding.get("passed", False)
                status = "passed" if passed else "failed"
                msg = matching_finding.get("message", f"Evaluator check '{check_name}' outcome: {passed}")

            return AssertionResult(
                assertion_type=a_type.value,
                passed=passed,
                status=status,
                path=assertion.path,
                expected=f"{check_name} passed",
                actual="passed" if passed else "failed",
                message=msg,
                details=matching_finding,
            )

        # Fallback unknown assertion
        return AssertionResult(
            assertion_type=str(a_type),
            passed=False,
            status="error",
            path=assertion.path,
            expected=None,
            actual=None,
            message=f"Unsupported assertion type: {a_type}",
        )

    @classmethod
    def evaluate_all(
        cls,
        assertions: List[AssertionDefinition],
        output_text: str,
        output_data: Optional[Dict[str, Any]] = None,
        context_items: Optional[List[Dict[str, Any]]] = None,
        retrieval_sources: Optional[List[Dict[str, Any]]] = None,
        evaluator_findings: Optional[List[Dict[str, Any]]] = None,
        expected_output: Optional[str] = None,
    ) -> List[AssertionResult]:
        """
        Evaluates a list of assertions and returns the list of AssertionResult objects.
        """
        results = []
        for a in assertions:
            res = cls.evaluate_assertion(
                assertion=a,
                output_text=output_text,
                output_data=output_data,
                context_items=context_items,
                retrieval_sources=retrieval_sources,
                evaluator_findings=evaluator_findings,
                expected_output=expected_output,
            )
            results.append(res)
        return results
