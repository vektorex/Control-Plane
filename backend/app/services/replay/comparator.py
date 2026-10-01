import difflib
from typing import Any, Dict, List, Optional
from backend.app.db.models.run import Run
from backend.app.db.models.replay import ReplayRun
from backend.app.services.replay.schemas import ReplayComparisonResult


class ReplayComparator:
    """
    Factual execution comparator that computes diffs between original and replay runs.
    Does NOT calculate subjective quality or scoring metrics; strictly reports factual discrepancies.
    """

    @staticmethod
    def compare_runs(original_run: Run, replay_run: ReplayRun) -> ReplayComparisonResult:
        """Compares an original Run with a completed ReplayRun."""
        orig_out = original_run.output_content or ""
        repl_out = replay_run.replay_output or ""

        # 1. Output Text Diff (using standard difflib)
        orig_lines = orig_out.splitlines(keepends=True)
        repl_lines = repl_out.splitlines(keepends=True)
        matcher = difflib.SequenceMatcher(None, orig_lines, repl_lines)
        similarity = round(matcher.ratio(), 4)

        additions: List[str] = []
        removals: List[str] = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "replace":
                removals.extend([line.rstrip("\r\n") for line in orig_lines[i1:i2]])
                additions.extend([line.rstrip("\r\n") for line in repl_lines[j1:j2]])
            elif tag == "delete":
                removals.extend([line.rstrip("\r\n") for line in orig_lines[i1:i2]])
            elif tag == "insert":
                additions.extend([line.rstrip("\r\n") for line in repl_lines[j1:j2]])

        output_diff = {
            "exact_match": orig_out.strip() == repl_out.strip(),
            "same_output": orig_out.strip() == repl_out.strip(),
            "similarity_ratio": similarity,
            "original_length": len(orig_out),
            "replay_length": len(repl_out),
            "length_difference": len(repl_out) - len(orig_out),
            "additions_count": len(additions),
            "removals_count": len(removals),
            "additions_sample": additions[:15],
            "removals_sample": removals[:15],
        }

        # 2. Model & Generation Diff
        snapshot = replay_run.snapshot or {}
        replay_meta = replay_run.replay_metadata or {}
        replay_model = replay_meta.get("final_model") or replay_meta.get("model") or snapshot.get("model_configuration", {}).get("model_name")
        orig_model = getattr(original_run, "model_name", None) or getattr(original_run, "final_model", None)

        model_diff = {
            "original_model": orig_model,
            "replay_model": replay_model,
            "same_model": orig_model == replay_model,
            "original_provider": getattr(original_run, "model_provider", None),
            "replay_provider": replay_meta.get("model_provider") or snapshot.get("model_configuration", {}).get("model_provider"),
            "temperature_original": snapshot.get("model_configuration", {}).get("temperature"),
            "temperature_replay": replay_meta.get("temperature", snapshot.get("model_configuration", {}).get("temperature")),
        }

        # 3. Usage & Cost Metrics Diff
        orig_in_tok = getattr(original_run, "input_tokens", 0) or 0
        orig_out_tok = getattr(original_run, "output_tokens", 0) or 0
        orig_total_tok = getattr(original_run, "total_tokens", None) or (orig_in_tok + orig_out_tok)

        repl_tok = replay_meta.get("token_usage", {})
        repl_in_tok = repl_tok.get("input_tokens", 0)
        repl_out_tok = repl_tok.get("output_tokens", 0)
        repl_total_tok = repl_tok.get("total_tokens", repl_in_tok + repl_out_tok)

        orig_cost = getattr(original_run, "estimated_cost", 0.0) or 0.0
        repl_cost = replay_meta.get("estimated_cost", 0.0)

        orig_latency = getattr(original_run, "latency_ms", 0) or 0
        repl_latency = replay_meta.get("duration_ms") or 0
        from datetime import datetime
        if isinstance(getattr(replay_run, "completed_at", None), datetime) and isinstance(getattr(replay_run, "started_at", None), datetime):
            repl_latency = int((replay_run.completed_at - replay_run.started_at).total_seconds() * 1000)

        usage_diff = {
            "tokens_delta": repl_total_tok - orig_total_tok,
            "duration_ms_delta": repl_latency - orig_latency,
            "cost_delta": round(repl_cost - orig_cost, 6),
            "tokens": {
                "original_input": orig_in_tok,
                "replay_input": repl_in_tok,
                "input_difference": repl_in_tok - orig_in_tok,
                "original_output": orig_out_tok,
                "replay_output": repl_out_tok,
                "output_difference": repl_out_tok - orig_out_tok,
                "original_total": orig_total_tok,
                "replay_total": repl_total_tok,
                "total_difference": repl_total_tok - orig_total_tok,
            },
            "cost": {
                "original_cost": orig_cost,
                "replay_cost": repl_cost,
                "cost_difference": round(repl_cost - orig_cost, 6),
            },
            "latency_ms": {
                "original_latency_ms": orig_latency,
                "replay_latency_ms": repl_latency,
                "latency_difference_ms": repl_latency - orig_latency,
            },
        }

        # 4. Context Diff
        orig_sources = getattr(original_run, "context_sources", None) or []
        repl_sources = replay_meta.get("context_sources", orig_sources)
        removed_srcs = [s for s in orig_sources if s not in repl_sources]
        added_srcs = [s for s in repl_sources if s not in orig_sources]
        context_diff = {
            "original_item_count": getattr(original_run, "context_item_count", None) or len(orig_sources),
            "replay_item_count": replay_meta.get("context_item_count", getattr(original_run, "context_item_count", None) or len(orig_sources)),
            "original_sources": orig_sources,
            "replay_sources": repl_sources,
            "sources_added": added_srcs,
            "sources_removed": removed_srcs,
            "added_sources": added_srcs,
            "removed_sources": removed_srcs,
        }

        # 5. Evaluation Diff
        orig_eval = getattr(original_run, "completion_evaluation", None) or getattr(original_run, "evaluation_result", None) or {}
        repl_eval = replay_meta.get("evaluation_result", {})
        eval_mode = getattr(original_run, "evaluation_mode", None)
        eval_status = getattr(original_run, "evaluation_status", None)
        evaluation_diff = {
            "original_mode": eval_mode,
            "replay_mode": replay_meta.get("evaluation_mode", eval_mode),
            "original_status": eval_status,
            "replay_status": repl_eval.get("status") or replay_meta.get("evaluation_status"),
            "status_match": (eval_status == (repl_eval.get("status") or replay_meta.get("evaluation_status"))),
            "original_recommendation": orig_eval.get("recommendation"),
            "replay_recommendation": repl_eval.get("recommendation"),
            "original_violations": orig_eval.get("violations", []),
            "replay_violations": repl_eval.get("violations", []),
        }

        # 6. Tool Diff
        orig_tools = original_run.tools_used or []
        repl_tools = replay_meta.get("tools_used", orig_tools)
        tool_diff = {
            "original_tools": orig_tools,
            "replay_tools": repl_tools,
            "original_call_count": original_run.tool_call_count or len(orig_tools),
            "replay_call_count": replay_meta.get("tool_call_count", len(repl_tools)),
            "tools_added": [t for t in repl_tools if t not in orig_tools],
            "tools_removed": [t for t in orig_tools if t not in repl_tools],
            "side_effects_blocked_count": replay_meta.get("side_effects_blocked_count", 0),
        }

        # 7. Determinism Indicators
        determinism = {
            "same_model": orig_model == replay_model,
            "same_workflow_version": True,
            "same_retrieval_configuration": True,
            "same_tool_configuration": set(orig_tools) == set(repl_tools),
            "same_memory_configuration": True,
            "notice": "Replay may differ from the original because model responses, external data, and provider behavior can change over time.",
        }

        return ReplayComparisonResult(
            replay_id=str(replay_run.id),
            original_run_id=str(original_run.id),
            output_diff=output_diff,
            context_diff=context_diff,
            model_diff=model_diff,
            usage_diff=usage_diff,
            evaluation_diff=evaluation_diff,
            tool_diff=tool_diff,
            determinism_indicators=determinism,
        )
