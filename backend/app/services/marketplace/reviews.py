"""
Marketplace Reviews and Moderation.
Step 38: AI Workflow Marketplace, Versioned Templates & Extension Ecosystem.
"""
from datetime import datetime, timezone
import re
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.marketplace.exceptions import PackageNotFoundError, MarketplaceException
from backend.app.services.marketplace.models import MarketplaceReview
from backend.app.services.marketplace.repository import MarketplaceRepository
from backend.app.services.marketplace.schemas import MarketplaceReviewCreate

SPAM_PATTERNS = [
    re.compile(r"https?://(?:bit\.ly|tinyurl\.com|t\.co)", re.IGNORECASE),
    re.compile(r"(?:buy now|free crypto|click here|casino)", re.IGNORECASE),
]


class MarketplaceReviewService:
    """Manages creation, retrieval, and automated content moderation for user reviews."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = MarketplaceRepository(session)

    async def add_review(
        self,
        package_id: str,
        organization_id: str,
        user_id: str,
        data: MarketplaceReviewCreate,
    ) -> MarketplaceReview:
        """Submits a user review with factual 1-5 rating and automated moderation check."""
        pkg = await self.repo.get_package_by_id(package_id)
        if not pkg:
            raise PackageNotFoundError(package_id)

        # Check moderation
        status = "published"
        if data.review:
            for pat in SPAM_PATTERNS:
                if pat.search(data.review):
                    status = "flagged"
                    break

        now = datetime.now(timezone.utc)
        review = MarketplaceReview(
            package_id=package_id,
            package_version_id=pkg.current_version_id,
            organization_id=organization_id,
            user_id=user_id,
            rating=data.rating,
            review=data.review,
            status=status,
            created_at=now,
            updated_at=now,
        )
        return await self.repo.create_review(review)

    async def list_reviews(self, package_id: str, limit: int = 50, offset: int = 0) -> List[MarketplaceReview]:
        return await self.repo.list_reviews(package_id, limit=limit, offset=offset)

    @classmethod
    def moderate_review_content(cls, text: str) -> tuple[bool, Optional[str]]:
        """Static moderation of review text for credentials, spam, and abusive patterns."""
        if not text:
            return False, None
        from backend.app.services.marketplace.security_scanner import SECRET_PATTERNS
        for pat in SECRET_PATTERNS:
            if pat.search(text):
                return True, "Credential leakage detected in review"
        for pat in SPAM_PATTERNS:
            if pat.search(text):
                return True, "Spam pattern detected in review"
        return False, None
