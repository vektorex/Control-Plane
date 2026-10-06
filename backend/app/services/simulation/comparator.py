"""
Factual Simulation Comparator for Step 41: AI Agent Simulation.
Generates objective, factual diffs between two simulation runs, agent versions, or team compositions.
Strictly avoids subjective scores or winner rankings.
"""
from typing import Any, Dict, List, Optional


class SimulationComparator:
    """
    Performs factual diffing between baseline and comparison simulation runs.
    """

    @classmethod
    def compare_runs(
        cls,
        baseline_run: Dict[str, Any],
        comparison_run: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Computes factual differences across execution path, assertions, resource usage, and tools.
        """
        diffs: Dict[str, Any] = {
            "metadata": {
                "baseline_run_id": baseline_run.get("id"),
                "comparison_run_id": comparison_run.get("id"),
                "baseline_target_version": baseline_run.get("target_version_id"),
                "comparison_target_version": comparison_run.get("target_version_id"),
                "baseline_seed": baseline_run.get("seed"),
                "comparison_seed": comparison_run.get("seed"),
            },
            "factual_differences": [],
            "metrics_diff": {},
            "tool_differences": [],
            "connector_differences": [],
            "assertion_differences": [],
            "side_effect_differences": [],
        }

        # Status comparison
        b_status = baseline_run.get("status")
        c_status = comparison_run.get("status")
        if b_status != c_status:
            diffs["factual_differences"].append(
                f"Baseline status was '{b_status}', whereas comparison status was '{c_status}'."
            )

        # Cost and tokens comparison
        b_cost = float(baseline_run.get("cost", 0.0))
        c_cost = float(comparison_run.get("cost", 0.0))
        b_lat = float(baseline_run.get("latency", 0.0))
        c_lat = float(comparison_run.get("latency", 0.0))
        b_tokens = baseline_run.get("tokens", {}).get("total_tokens", 0)
        c_tokens = comparison_run.get("tokens", {}).get("total_tokens", 0)

        diffs["metrics_diff"] = {
            "baseline": {"cost": b_cost, "latency": b_lat, "total_tokens": b_tokens},
            "comparison": {"cost": c_cost, "latency": c_lat, "total_tokens": c_tokens},
            "delta": {
                "cost_diff": round(c_cost - b_cost, 6),
                "latency_diff_sec": round(c_lat - b_lat, 4),
                "tokens_diff": c_tokens - b_tokens,
            },
        }

        # Tool calls comparison
        b_tools = baseline_run.get("tool_calls", [])
        c_tools = comparison_run.get("tool_calls", [])
        diffs["factual_diffs"] = {
            "tool_calls": {
                "run_a_count": len(b_tools),
                "run_b_count": len(c_tools),
            },
            "cost": {
                "diff": round(c_cost - b_cost, 6),
            },
            "latency": {
                "diff": round(c_lat - b_lat, 4),
            },
        }
        b_tool_counts = cls._count_items(b_tools, "tool_name")
        c_tool_counts = cls._count_items(c_tools, "tool_name")
        all_tools = set(b_tool_counts.keys()).union(set(c_tool_counts.keys()))
        for t in all_tools:
            bc = b_tool_counts.get(t, 0)
            cc = c_tool_counts.get(t, 0)
            if bc != cc:
                diff_msg = f"Baseline called tool '{t}' {bc} time(s); comparison called it {cc} time(s)."
                diffs["tool_differences"].append({"tool": t, "baseline_count": bc, "comparison_count": cc, "note": diff_msg})
                diffs["factual_differences"].append(diff_msg)

        # Connector calls comparison
        b_conns = baseline_run.get("connector_calls", [])
        c_conns = comparison_run.get("connector_calls", [])
        b_conn_counts = cls._count_items(b_conns, "connector_name")
        c_conn_counts = cls._count_items(c_conns, "connector_name")
        all_conns = set(b_conn_counts.keys()).union(set(c_conn_counts.keys()))
        for c in all_conns:
            bc = b_conn_counts.get(c, 0)
            cc = c_conn_counts.get(c, 0)
            if bc != cc:
                diff_msg = f"Baseline executed connector '{c}' {bc} time(s); comparison executed it {cc} time(s)."
                diffs["connector_differences"].append({"connector": c, "baseline_count": bc, "comparison_count": cc, "note": diff_msg})
                diffs["factual_differences"].append(diff_msg)

        # Side effects comparison
        b_se = baseline_run.get("side_effects", [])
        c_se = comparison_run.get("side_effects", [])
        if len(b_se) != len(c_se):
            diff_msg = f"Baseline intercepted {len(b_se)} side effect(s); comparison intercepted {len(c_se)} side effect(s)."
            diffs["side_effect_differences"].append({"baseline_count": len(b_se), "comparison_count": len(c_se), "note": diff_msg})
            diffs["factual_differences"].append(diff_msg)

        # Assertions comparison
        b_asserts = baseline_run.get("assertion_results", [])
        c_asserts = comparison_run.get("assertion_results", [])
        b_pass_count = sum(1 for a in b_asserts if a.get("passed"))
        c_pass_count = sum(1 for a in c_asserts if a.get("passed"))
        if b_pass_count != c_pass_count:
            diff_msg = f"Baseline passed {b_pass_count}/{len(b_asserts)} assertions; comparison passed {c_pass_count}/{len(c_asserts)} assertions."
            diffs["assertion_differences"].append({"baseline_passed": b_pass_count, "comparison_passed": c_pass_count, "note": diff_msg})
            diffs["factual_differences"].append(diff_msg)

        return diffs

    @staticmethod
    def _count_items(items: List[Any], key: str) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for it in items:
            k = it if isinstance(it, str) else it.get(key)
            if k:
                counts[k] = counts.get(k, 0) + 1
        return counts

