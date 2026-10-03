"""
Marketplace Registry & Catalog.
Step 38: AI Workflow Marketplace, Versioned Templates & Extension Ecosystem.
"""
from typing import List

STANDARD_CATEGORIES: List[str] = [
    "research",
    "writing",
    "coding",
    "data_analysis",
    "document_processing",
    "customer_support",
    "project_management",
    "developer_tools",
    "security",
    "evaluation",
    "automation",
    "knowledge_management",
    "productivity",
]

STANDARD_TAGS: List[str] = [
    "AI",
    "RAG",
    "workflow",
    "research",
    "coding",
    "documents",
    "GitHub",
    "analysis",
    "automation",
    "evaluation",
    "multimodal",
    "agents",
]


class MarketplaceRegistryService:
    """Provides access to curated categories, tags, and catalog taxonomies."""

    @classmethod
    def get_categories(cls) -> List[str]:
        return list(STANDARD_CATEGORIES)

    @classmethod
    def get_tags(cls) -> List[str]:
        return list(STANDARD_TAGS)
