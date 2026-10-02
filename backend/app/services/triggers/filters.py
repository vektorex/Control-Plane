"""
Deterministic event filtering engine with AND/OR multi-condition evaluation.
"""
from typing import Any, Dict, List, Optional, Tuple, Union
from backend.app.services.triggers.schemas import FilterConfiguration, FilterLogic, FilterOperator, FilterRule


class TriggerFilterEngine:
    """
    Evaluates filter rules deterministically without code execution or dynamic eval.
    """

    @classmethod
    def evaluate(
        cls,
        filter_config: Optional[Union[FilterConfiguration, Dict[str, Any]]],
        data: Dict[str, Any],
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Evaluates a FilterConfiguration or dict against data (e.g. TriggerEvent dict or payload).
        Returns (matched: bool, details: dict).
        """
        if not filter_config:
            return True, {"logic": "AND", "rules_evaluated": 0, "rule_results": [], "matched": True}

        if isinstance(filter_config, dict):
            logic_str = filter_config.get("logic", "AND").upper()
            raw_rules = filter_config.get("rules", [])
        else:
            logic_str = filter_config.logic.value.upper()
            raw_rules = [r.model_dump() for r in filter_config.rules]

        if not raw_rules:
            return True, {"logic": logic_str, "rules_evaluated": 0, "rule_results": [], "matched": True}

        rule_results: List[Dict[str, Any]] = []
        is_or = logic_str == "OR"

        for r in raw_rules:
            field_path = r.get("field") or r.get("path", "")
            operator = r.get("operator", "equals")
            expected_val = r.get("value")

            actual_val = cls._resolve_path(data, field_path)
            passed = cls._evaluate_rule(actual_val, operator, expected_val)

            rule_results.append({
                "field": field_path,
                "operator": operator,
                "expected": expected_val,
                "actual": actual_val,
                "passed": passed,
            })

        if is_or:
            overall_match = any(res["passed"] for res in rule_results)
        else:
            overall_match = all(res["passed"] for res in rule_results)

        return overall_match, {
            "logic": logic_str,
            "rules_evaluated": len(rule_results),
            "rule_results": rule_results,
            "matched": overall_match,
        }

    @classmethod
    def _resolve_path(cls, data: Dict[str, Any], path: str) -> Any:
        """
        Safely navigates nested dict keys and list indices.
        Accepts paths like 'payload.repository.full_name', 'repository.full_name', or 'payload.issue.labels'.
        """
        if not path or not isinstance(data, dict):
            return None

        parts = path.strip().split(".")
        current: Any = data

        # If data has a top-level 'payload' key and path starts with 'payload', or doesn't start with 'payload'
        if parts[0] == "payload" and "payload" not in data:
            parts = parts[1:]

        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                # Try integer index if specified
                try:
                    idx = int(part)
                    if 0 <= idx < len(current):
                        current = current[idx]
                    else:
                        return None
                except ValueError:
                    return None
            else:
                return None

            if current is None:
                return None

        return current

    @classmethod
    def _evaluate_rule(cls, actual: Any, operator: str, expected: Any) -> bool:
        """
        Deterministic operator evaluation.
        """
        op = operator.lower() if isinstance(operator, str) else operator.value

        if op == "exists":
            # If expected is False or None, check non-existence; otherwise check existence
            should_exist = expected is True if expected is not None else True
            exists = actual is not None
            return exists if should_exist else not exists

        if actual is None:
            # For non-exists operators, if actual is None and we're not checking not_equals None, return False
            if op == "not_equals":
                return expected is not None
            return False

        if op == "equals":
            # Exact or type-coerced equality
            if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
                return actual == expected
            return str(actual).strip() == str(expected).strip()

        elif op == "not_equals":
            if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
                return actual != expected
            return str(actual).strip() != str(expected).strip()

        elif op == "contains":
            if isinstance(actual, list):
                # Check item in list
                return any(str(item).strip() == str(expected).strip() or str(expected).strip() in str(item) for item in actual)
            elif isinstance(actual, dict):
                return str(expected) in actual
            elif isinstance(actual, str):
                return str(expected).lower() in str(actual).lower()
            return False

        elif op == "starts_with":
            return str(actual).startswith(str(expected))

        elif op == "ends_with":
            return str(actual).endswith(str(expected))

        elif op in ("greater_than", "less_than", "greater_or_equal", "less_or_equal"):
            try:
                num_actual = float(actual)
                num_expected = float(expected)
                if op == "greater_than":
                    return num_actual > num_expected
                elif op == "less_than":
                    return num_actual < num_expected
                elif op == "greater_or_equal":
                    return num_actual >= num_expected
                elif op == "less_or_equal":
                    return num_actual <= num_expected
            except (ValueError, TypeError):
                return False

        return False
