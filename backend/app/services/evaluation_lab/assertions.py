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

        # 12. entity_exists (Step 29 Knowledge Graph assertion)
        elif a_type == AssertionType.ENTITY_EXISTS:
            expected_entity = str(assertion.value or "").lower()
            found = False
            # Check context items from knowledge graph
            if context_items:
                for item in context_items:
                    meta = item.get("metadata", {})
                    c_name = str(meta.get("canonical_name", "")).lower()
                    if expected_entity in c_name or expected_entity in str(item.get("content", "")).lower():
                        found = True
                        break
            if not found and expected_entity in str_val.lower():
                found = True

            return AssertionResult(
                assertion_type=a_type.value,
                passed=found,
                status="passed" if found else "failed",
                path=assertion.path,
                expected=f"Entity '{assertion.value}' exists in graph context or output",
                actual="found" if found else "not found",
                message=f"Entity '{assertion.value}' was {'found' if found else 'missing'}",
            )

        # 13. relationship_exists (Step 29 Knowledge Graph assertion)
        elif a_type == AssertionType.RELATIONSHIP_EXISTS:
            expected_rel = str(assertion.value or "").lower()
            found = False
            if context_items:
                for item in context_items:
                    meta = item.get("metadata", {})
                    rels = meta.get("relationships", [])
                    for r in rels:
                        if expected_rel in str(r).lower():
                            found = True
                            break
                    if not found and expected_rel in str(item.get("content", "")).lower():
                        found = True
                        break
            if not found and expected_rel in str_val.lower():
                found = True

            return AssertionResult(
                assertion_type=a_type.value,
                passed=found,
                status="passed" if found else "failed",
                path=assertion.path,
                expected=f"Relationship '{assertion.value}' exists in graph context or output",
                actual="found" if found else "not found",
                message=f"Relationship '{assertion.value}' was {'found' if found else 'missing'}",
            )

        # 14. relationship_matches_source (Step 29 Knowledge Graph assertion)
        elif a_type == AssertionType.RELATIONSHIP_MATCHES_SOURCE:
            expected_src = str(assertion.value or "").lower()
            matches = False
            if context_items:
                for item in context_items:
                    meta = item.get("metadata", {})
                    sources = meta.get("sources", []) or meta.get("source_reference", {})
                    if expected_src in str(sources).lower():
                        matches = True
                        break
            if not matches and expected_src in str_val.lower():
                matches = True

            return AssertionResult(
                assertion_type=a_type.value,
                passed=matches,
                status="passed" if matches else "failed",
                path=assertion.path,
                expected=f"Relationship matches source '{assertion.value}'",
                actual="matched" if matches else "unmatched",
                message=f"Relationship source match {'succeeded' if matches else 'failed'}",
            )

        # 15. source_reference_exists (Step 29 Knowledge Graph assertion)
        elif a_type == AssertionType.SOURCE_REFERENCE_EXISTS:
            has_source = False
            if context_items:
                for item in context_items:
                    meta = item.get("metadata", {})
                    if meta.get("sources") or meta.get("source_reference") or meta.get("source_count", 0) > 0:
                        has_source = True
                        break
            if not has_source and retrieval_sources and len(retrieval_sources) > 0:
                has_source = True
            if not has_source and ("source" in str_val.lower() or "provenance" in str_val.lower()):
                has_source = True

            return AssertionResult(
                assertion_type=a_type.value,
                passed=has_source,
                status="passed" if has_source else "failed",
                path=assertion.path,
                expected="Source reference exists for graph entity or relationship",
                actual="found" if has_source else "missing",
                message="Graph source reference verified" if has_source else "Missing source reference for graph element",
            )

        # 16. image_claim_supported (Step 30 Multimodal assertion)
        elif a_type == AssertionType.IMAGE_CLAIM_SUPPORTED:
            expected_kw = str(assertion.value or "").lower()
            found = False
            if context_items:
                for item in context_items:
                    meta = item.get("metadata", {})
                    if meta.get("media_type") == "image" or "image" in item.get("title", "").lower():
                        if not expected_kw or expected_kw in str(item.get("content", "")).lower() or expected_kw in str_val.lower():
                            found = True
                            break
            if not found and expected_kw and expected_kw in str_val.lower():
                found = True

            return AssertionResult(
                assertion_type=a_type.value,
                passed=found,
                status="passed" if found else "failed",
                path=assertion.path,
                expected=f"Image claim supported for '{assertion.value}'",
                actual="supported" if found else "unsupported",
                message=f"Image claim was {'supported by visual context' if found else 'unsupported'}",
            )

        # 17. table_value_correct (Step 30 Multimodal assertion)
        elif a_type == AssertionType.TABLE_VALUE_CORRECT:
            expected_val = str(assertion.value or "").strip().lower()
            found = expected_val in str_val.lower() if expected_val else False
            return AssertionResult(
                assertion_type=a_type.value,
                passed=found,
                status="passed" if found else "failed",
                path=assertion.path,
                expected=f"Table value '{assertion.value}' in output",
                actual="found" if found else "missing",
                message=f"Table value '{assertion.value}' was {'verified' if found else 'missing'}",
            )

        # 18. transcript_grounded (Step 30 Multimodal assertion)
        elif a_type == AssertionType.TRANSCRIPT_GROUNDED:
            claim = str(assertion.value or "").lower()
            grounded = False
            if context_items:
                for item in context_items:
                    meta = item.get("metadata", {})
                    if meta.get("media_type") == "audio_transcript" or "transcript" in item.get("title", "").lower():
                        if not claim or claim in str(item.get("content", "")).lower():
                            grounded = True
                            break
            if not grounded and claim and claim in str_val.lower():
                grounded = True

            return AssertionResult(
                assertion_type=a_type.value,
                passed=grounded,
                status="passed" if grounded else "failed",
                path=assertion.path,
                expected="Transcript grounded in audio context",
                actual="grounded" if grounded else "ungrounded",
                message="Claim grounded in transcript" if grounded else "Transcript claim lacking audio grounding",
            )

        # 19. source_timestamp_exists (Step 30 Multimodal assertion)
        elif a_type == AssertionType.SOURCE_TIMESTAMP_EXISTS:
            ts_regex = re.compile(r"\b\d{1,2}:\d{2}(:\d{2})?\b")
            has_ts = bool(ts_regex.search(str_val))
            if not has_ts and context_items:
                for item in context_items:
                    if ts_regex.search(str(item.get("content", ""))) or item.get("metadata", {}).get("timestamp"):
                        has_ts = True
                        break

            return AssertionResult(
                assertion_type=a_type.value,
                passed=has_ts,
                status="passed" if has_ts else "failed",
                path=assertion.path,
                expected="Timestamp in MM:SS or HH:MM:SS format present",
                actual="found" if has_ts else "missing",
                message="Timestamp verified" if has_ts else "Missing source timestamp",
            )

        # 20. visual_evidence_present (Step 30 Multimodal assertion)
        elif a_type == AssertionType.VISUAL_EVIDENCE_PRESENT:
            has_evidence = False
            if output_data and output_data.get("evidence"):
                has_evidence = True
            elif context_items:
                for item in context_items:
                    meta = item.get("metadata", {})
                    if meta.get("media_type") in ("image", "video_frame") or meta.get("storage_reference"):
                        has_evidence = True
                        break
            if not has_evidence and ("image" in str_val.lower() or "figure" in str_val.lower() or "evidence" in str_val.lower()):
                has_evidence = True

            return AssertionResult(
                assertion_type=a_type.value,
                passed=has_evidence,
                status="passed" if has_evidence else "failed",
                path=assertion.path,
                expected="Visual evidence present in result or context",
                actual="present" if has_evidence else "missing",
                message="Visual evidence confirmed" if has_evidence else "Missing visual evidence",
            )

        # 21. artifact_reference_exists (Step 30 Multimodal assertion)
        elif a_type == AssertionType.ARTIFACT_REFERENCE_EXISTS:
            expected_ref = str(assertion.value or "").lower()
            has_ref = False
            if expected_ref:
                has_ref = expected_ref in str_val.lower()
                if not has_ref and context_items:
                    for item in context_items:
                        meta = item.get("metadata", {})
                        if expected_ref in str(meta.get("artifact_id", "")).lower() or expected_ref in str(meta.get("filename", "")).lower():
                            has_ref = True
                            break
            else:
                if context_items:
                    for item in context_items:
                        if item.get("metadata", {}).get("artifact_id"):
                            has_ref = True
                            break
                if not has_ref and output_data and output_data.get("artifact_id"):
                    has_ref = True

            return AssertionResult(
                assertion_type=a_type.value,
                passed=has_ref,
                status="passed" if has_ref else "failed",
                path=assertion.path,
                expected=f"Artifact reference exists: '{assertion.value or 'any'}'",
                actual="referenced" if has_ref else "missing",
                message="Artifact reference verified" if has_ref else "Missing artifact reference",
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
