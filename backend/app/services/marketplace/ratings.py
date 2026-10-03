"""
Marketplace Factual Ratings Calculator.
Step 38: AI Workflow Marketplace, Versioned Templates & Extension Ecosystem.
"""
from typing import Any, Dict, List, Optional
from backend.app.services.marketplace.models import MarketplaceReview


class MarketplaceRatingCalculator:
    """Calculates factual average ratings without generating subjective quality scores."""

    @staticmethod
    def calculate_average(reviews: List[Any]) -> Optional[float]:
        ratings = []
        for r in reviews:
            val = r.rating if hasattr(r, "rating") else r.get("rating") if isinstance(r, dict) else None
            if val is not None and 1 <= val <= 5:
                ratings.append(val)
        if not ratings:
            return None
        return round(sum(ratings) / len(ratings), 2)

    @classmethod
    def calculate_summary(cls, reviews: List[Any]) -> Dict[str, Any]:
        dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        ratings = []
        for r in reviews:
            val = r.rating if hasattr(r, "rating") else r.get("rating") if isinstance(r, dict) else None
            if val is not None and 1 <= val <= 5:
                ratings.append(val)
                dist[val] += 1
        avg = round(sum(ratings) / len(ratings), 2) if ratings else None
        return {
            "average_rating": avg,
            "total_reviews": len(ratings),
            "rating_distribution": dist,
        }
