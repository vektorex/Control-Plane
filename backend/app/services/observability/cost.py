from typing import Any, Dict, List, Optional, Union
from backend.app.services.models.registry import ModelRegistry, default_model_registry


class CostCalculator:
    """
    Production-grade token pricing and cost intelligence calculator.
    Calculates costs strictly from configured ModelRegistry pricing metadata.
    Returns None if pricing metadata is unavailable (never guesses or invents pricing).
    """

    def __init__(self, registry: Optional[ModelRegistry] = None) -> None:
        self.registry = registry or default_model_registry

    def calculate_generation_cost(
        self,
        model_id: Optional[str],
        provider: Optional[str] = None,
        input_tokens: Optional[int] = 0,
        output_tokens: Optional[int] = 0,
        cached_input_tokens: Optional[int] = 0,
    ) -> Optional[float]:
        """
        Calculates generation cost based on exact 1M token formulas.
        Formula:
          input_cost = (input_tokens / 1_000_000) * input_price
          output_cost = (output_tokens / 1_000_000) * output_price
          cached_cost = (cached_input_tokens / 1_000_000) * cached_input_price
        """
        if not model_id or (input_tokens is None and output_tokens is None):
            return None

        model_def = self.registry.get_model(model_id, provider=provider)
        if not model_def or not model_def.cost_metadata:
            return None

        cost_meta = model_def.cost_metadata
        in_price_1m = cost_meta.effective_input_cost_per_1m
        out_price_1m = cost_meta.effective_output_cost_per_1m
        cached_price_1m = cost_meta.effective_cached_input_cost_per_1m or in_price_1m

        if in_price_1m is None and out_price_1m is None:
            return None

        in_tok = max(0, input_tokens or 0)
        out_tok = max(0, output_tokens or 0)
        cached_tok = max(0, cached_input_tokens or 0)

        # Subtract cached tokens from standard input if cached is distinct
        standard_in_tok = max(0, in_tok - cached_tok) if (cost_meta.effective_cached_input_cost_per_1m is not None) else in_tok

        in_cost = (standard_in_tok / 1_000_000.0) * (in_price_1m or 0.0)
        out_cost = (out_tok / 1_000_000.0) * (out_price_1m or 0.0)
        cached_cost = (cached_tok / 1_000_000.0) * (cached_price_1m or 0.0) if cached_tok > 0 and cost_meta.effective_cached_input_cost_per_1m is not None else 0.0

        total = in_cost + out_cost + cached_cost
        return round(total, 6)

    def calculate_usage_cost(
        self,
        model_id: Optional[str],
        provider: Optional[str] = None,
        input_tokens: Optional[int] = 0,
        output_tokens: Optional[int] = 0,
    ) -> Optional[float]:
        """
        Calculates operational usage cost for a single operation record.
        """
        return self.calculate_generation_cost(
            model_id=model_id,
            provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    def calculate_total_run_cost(
        self,
        usage_records: List[Dict[str, Any]],
    ) -> Optional[float]:
        """
        Aggregates estimated cost across multiple operational usage records.
        If all records have no pricing, returns None.
        """
        if not usage_records:
            return None

        total_cost = 0.0
        has_any_cost = False

        for rec in usage_records:
            cost = rec.get("estimated_cost")
            if cost is None:
                # Attempt recalculation
                cost = self.calculate_usage_cost(
                    model_id=rec.get("model"),
                    provider=rec.get("provider"),
                    input_tokens=rec.get("input_tokens", 0),
                    output_tokens=rec.get("output_tokens", 0),
                )
            if cost is not None:
                total_cost += cost
                has_any_cost = True

        return round(total_cost, 6) if has_any_cost else None


default_cost_calculator = CostCalculator()
