import hashlib
from typing import List, Set
from backend.app.db.models.task import Task
from backend.app.schemas.llm import ChatMessage
from backend.app.services.context.models import ContextBudget, ContextItem, ContextPackage
from backend.app.services.context.token_estimator import (
    estimate_context_item_tokens,
    estimate_tokens,
)


class ContextBuilder:
    """
    Assembles, deduplicates, prioritizes, budget-enforces, and formats
    heterogeneous context items into a normalized ContextPackage and LLM messages.
    """

    @staticmethod
    def _compute_content_hash(item: ContextItem) -> str:
        """Computes a normalized SHA-256 fingerprint for duplicate detection."""
        normalized = f"{item.title.strip().lower()}:::{item.content.strip()}"
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def deduplicate(self, items: List[ContextItem]) -> List[ContextItem]:
        """
        Removes duplicate context items based on content hash.
        When duplicates are encountered, preserves the one with the higher priority.
        """
        seen_hashes: Set[str] = set()
        deduped: List[ContextItem] = []

        # Sort temporarily by priority descending so the highest priority instance is preserved
        sorted_for_dedup = sorted(
            items,
            key=lambda x: (x.priority, x.relevance_score or 0.0),
            reverse=True,
        )

        for item in sorted_for_dedup:
            content_hash = self._compute_content_hash(item)
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                deduped.append(item)

        return deduped

    def prioritize(self, items: List[ContextItem]) -> List[ContextItem]:
        """
        Orders context items based on:
        1. Priority integer (higher first)
        2. Relevance score (if present, higher first)
        3. Recency (created_at timestamp, newest first)
        """
        return sorted(
            items,
            key=lambda x: (
                x.priority,
                x.relevance_score or 0.0,
                x.created_at.timestamp() if x.created_at else 0.0,
            ),
            reverse=True,
        )

    def build(
        self,
        raw_items: List[ContextItem],
        budget: ContextBudget,
    ) -> ContextPackage:
        """
        Executes complete packaging pipeline:
        1. Deduplication
        2. Priority sorting
        3. Token estimation
        4. Budget enforcement and truncation
        5. Structured ContextPackage assembly
        """
        if not raw_items:
            return ContextPackage(
                items=[],
                total_items=0,
                estimated_tokens=0,
                truncated=False,
                sources=[],
                dropped_items_count=0,
            )

        # 1. Deduplicate
        deduped_items = self.deduplicate(raw_items)
        initial_dropped = len(raw_items) - len(deduped_items)

        # 2. Prioritize
        prioritized_items = self.prioritize(deduped_items)

        # 3. Budget enforcement & assembly
        accepted_items: List[ContextItem] = []
        accumulated_tokens = 0
        truncated = False
        dropped_count = initial_dropped
        sources_seen: Set[str] = set()

        for item in prioritized_items:
            # Ensure token estimate is populated
            if not item.token_estimate or item.token_estimate <= 0:
                item.token_estimate = estimate_context_item_tokens(item)

            item_cost = item.token_estimate

            if accumulated_tokens + item_cost <= budget.max_context_tokens:
                accepted_items.append(item)
                accumulated_tokens += item_cost
                sources_seen.add(item.source_type)
            else:
                # Exceeds budget: truncate/drop
                truncated = True
                dropped_count += 1

        return ContextPackage(
            items=accepted_items,
            total_items=len(accepted_items),
            estimated_tokens=accumulated_tokens,
            truncated=truncated,
            sources=sorted(list(sources_seen)),
            dropped_items_count=dropped_count,
        )

    def format_as_context_text(self, package: ContextPackage) -> str:
        """
        Renders the context package into a structured text block suitable for inclusion in prompts.
        """
        if not package.items:
            return ""

        sections: List[str] = []
        for idx, item in enumerate(package.items, 1):
            source_tag = item.source_type.upper()
            section = f"[{idx}] Source: {source_tag} | Title: {item.title}\n{item.content.strip()}"
            sections.append(section)

        formatted_block = "\n\n---\n\n".join(sections)
        return f"=== CONTEXT INGESTION ===\n{formatted_block}\n========================="

    def format_as_messages(
        self,
        package: ContextPackage,
        task: Task,
    ) -> List[ChatMessage]:
        """
        Constructs standardized ChatMessage list for LLM invocation
        separately from the ContextEngine retrieval logic.
        """
        # 1. Base system prompt
        system_content = "You are an AI assistant helping the user complete a task accurately."

        # 2. Context injection into system message
        context_block = self.format_as_context_text(package)
        if context_block:
            system_content = f"{system_content}\n\n{context_block}"

        # 3. User instructions / prompt
        prompt = (task.instructions or "").strip()
        if not prompt:
            prompt = (task.description or "").strip()
        if not prompt:
            prompt = (task.title or "").strip()

        if not prompt:
            prompt = "Execute the task as defined."

        return [
            ChatMessage(role="system", content=system_content),
            ChatMessage(role="user", content=prompt),
        ]
