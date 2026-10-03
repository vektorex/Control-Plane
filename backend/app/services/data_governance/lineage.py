"""
Data Lineage Service for Step 33.
Tracks transformation provenance across platform subsystems with bounded graph traversal.
Never stores content; stores identifiers and metadata only.
"""
from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.data_governance.exceptions import DataAssetNotFoundError, InvalidLineageError
from backend.app.services.data_governance.models import DataAsset, DataLineageEdge
from backend.app.services.data_governance.schemas import (
    LineageEdgeCreate,
    LineageEdgeResponse,
    LineageGraphNode,
    LineageGraphResponse,
)


class DataLineageService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_edge(
        self,
        organization_id: str,
        data: LineageEdgeCreate,
        created_by: Optional[str] = None,
    ) -> DataLineageEdge:
        """
        Creates a directed lineage edge from source_asset_id to target_asset_id.
        """
        if data.source_asset_id == data.target_asset_id:
            raise InvalidLineageError("Source and target asset cannot be the same (self-loop forbidden).")

        # Verify source and target exist and belong to organization
        q = select(DataAsset.id).where(
            DataAsset.organization_id == organization_id,
            DataAsset.id.in_([data.source_asset_id, data.target_asset_id]),
        )
        res = await self.session.execute(q)
        found_ids = set(res.scalars().all())

        if data.source_asset_id not in found_ids:
            raise DataAssetNotFoundError(f"Source asset '{data.source_asset_id}' not found.")
        if data.target_asset_id not in found_ids:
            raise DataAssetNotFoundError(f"Target asset '{data.target_asset_id}' not found.")

        edge = DataLineageEdge(
            organization_id=organization_id,
            source_asset_id=data.source_asset_id,
            target_asset_id=data.target_asset_id,
            relationship_type=data.relationship_type,
            transformation_type=data.transformation_type,
            created_at=datetime.now(timezone.utc),
            created_by=created_by,
            edge_metadata=data.metadata,
        )
        self.session.add(edge)
        await self.session.flush()
        await self.session.refresh(edge)
        return edge

    async def get_lineage_graph(
        self,
        root_asset_id: str,
        organization_id: str,
        max_depth: int = 5,
    ) -> LineageGraphResponse:
        """
        Performs bounded BFS traversal up and downstream from the root asset.
        Returns graph nodes and edges for visual exploration without content exposure.
        """
        # Verify root asset
        q_root = select(DataAsset).where(
            DataAsset.id == root_asset_id,
            DataAsset.organization_id == organization_id,
        )
        res_root = await self.session.execute(q_root)
        root = res_root.scalar_one_or_none()
        if not root:
            raise DataAssetNotFoundError(f"Root asset '{root_asset_id}' not found.")

        visited_assets: Set[str] = {root_asset_id}
        collected_edges: List[DataLineageEdge] = []
        queue = deque([(root_asset_id, 0)])

        while queue:
            current_id, depth = queue.popleft()
            if depth >= max_depth:
                continue

            # Query upstream and downstream edges
            q_edges = select(DataLineageEdge).where(
                DataLineageEdge.organization_id == organization_id,
                (DataLineageEdge.source_asset_id == current_id) | (DataLineageEdge.target_asset_id == current_id),
            )
            edges_res = await self.session.execute(q_edges)
            edges = edges_res.scalars().all()

            for edge in edges:
                if edge not in collected_edges:
                    collected_edges.append(edge)

                next_id = edge.target_asset_id if edge.source_asset_id == current_id else edge.source_asset_id
                if next_id not in visited_assets:
                    visited_assets.add(next_id)
                    queue.append((next_id, depth + 1))

        # Query all node details
        q_nodes = select(DataAsset).where(
            DataAsset.organization_id == organization_id,
            DataAsset.id.in_(visited_assets),
        )
        nodes_res = await self.session.execute(q_nodes)
        node_records = nodes_res.scalars().all()

        nodes = [
            LineageGraphNode(
                id=n.id,
                name=n.name,
                asset_type=n.asset_type,
                resource_type=n.resource_type,
                classification=n.data_classification,
                status=n.status,
            )
            for n in node_records
        ]

        edge_responses = [
            LineageEdgeResponse(
                id=e.id,
                organization_id=e.organization_id,
                source_asset_id=e.source_asset_id,
                target_asset_id=e.target_asset_id,
                relationship_type=e.relationship_type,
                transformation_type=e.transformation_type,
                created_at=e.created_at,
                created_by=e.created_by,
                metadata=e.edge_metadata,
            )
            for e in collected_edges
        ]

        return LineageGraphResponse(
            root_asset_id=root_asset_id,
            nodes=nodes,
            edges=edge_responses,
        )
