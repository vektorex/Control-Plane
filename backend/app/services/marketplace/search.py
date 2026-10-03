"""
Marketplace Search Engine.
Step 38: AI Workflow Marketplace, Versioned Templates & Extension Ecosystem.
"""
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.marketplace.models import MarketplacePackage
from backend.app.services.marketplace.repository import MarketplaceRepository
from backend.app.services.marketplace.schemas import MarketplaceSearchQuery


class MarketplaceSearchService:
    """Provides deterministic, factual search across marketplace packages."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = MarketplaceRepository(session)

    async def search(
        self,
        query_params: MarketplaceSearchQuery,
        organization_id: Optional[str] = None,
    ) -> Tuple[List[MarketplacePackage], int]:
        """
        Executes search with exact and prefix matching.
        Does NOT use LLM to secretly rank marketplace results.
        """
        return await self.repo.list_packages(
            organization_id=organization_id,
            category=query_params.category,
            package_type=query_params.package_type.value if query_params.package_type else None,
            visibility=query_params.visibility.value if query_params.visibility else None,
            status=query_params.status.value if query_params.status else None,
            search_query=query_params.query,
            limit=query_params.limit,
            offset=query_params.offset,
        )
