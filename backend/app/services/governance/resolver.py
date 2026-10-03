"""
PolicyResolver: resolves applicable policies for a given execution scope.
Enforces precedence: system > organization > workspace > project > user preferences.
Step 32.
"""
from typing import List, Optional, Tuple
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.services.governance.constants import (
    POLICY_PRECEDENCE,
    PolicyScope,
    PolicyStatus,
    PolicyVersionStatus,
)
from backend.app.services.governance.errors import GovernanceStateUnknownError
from backend.app.services.governance.models import (
    GovernancePolicy,
    GovernancePolicyVersion,
)
from backend.app.services.governance.policy_registry import PolicyRegistry, policy_registry
from backend.app.services.governance.repository import GovernancePolicyRepository
from backend.app.services.governance.schemas import GovernanceEvaluationRequest, PolicyRule


class PolicyResolver:
    """
    Resolves the set of applicable policy rules for a given execution context.
    Precedence enforced: system → organization → workspace → project.
    User preferences may never weaken security policies.
    """

    def __init__(self, repo: GovernancePolicyRepository, registry: PolicyRegistry):
        self.repo = repo
        self.registry = registry

    async def resolve_rules(
        self, request: GovernanceEvaluationRequest
    ) -> Tuple[List[PolicyRule], List[str]]:
        """
        Returns (all_applicable_rules, matched_policy_ids) ordered by precedence.
        System rules come first; workspace/project rules come last.
        """
        all_rules: List[PolicyRule] = []
        policy_ids: List[str] = []

        # 1. System security rules (always first, immutable)
        system_rules = self.registry.get_system_rules()
        all_rules.extend(system_rules)
        if system_rules:
            policy_ids.append("system_security")

        # 2. Organization-scope policies
        org_policies = await self._load_policies(
            organization_id=request.organization_id,
            workspace_id=None,
            project_id=None,
            scope=PolicyScope.ORGANIZATION.value,
        )
        for policy, version in org_policies:
            rules = self._parse_rules(version)
            all_rules.extend(rules)
            policy_ids.append(str(policy.id))

        # 3. Workspace-scope policies
        if request.workspace_id:
            ws_policies = await self._load_policies(
                organization_id=request.organization_id,
                workspace_id=request.workspace_id,
                project_id=None,
                scope=PolicyScope.WORKSPACE.value,
            )
            for policy, version in ws_policies:
                rules = self._parse_rules(version)
                all_rules.extend(rules)
                policy_ids.append(str(policy.id))

        # 4. Project-scope policies (lowest precedence among managed policies)
        if request.project_id:
            proj_policies = await self._load_policies(
                organization_id=request.organization_id,
                workspace_id=request.workspace_id,
                project_id=request.project_id,
                scope=PolicyScope.PROJECT.value,
            )
            for policy, version in proj_policies:
                rules = self._parse_rules(version)
                all_rules.extend(rules)
                policy_ids.append(str(policy.id))

        return all_rules, policy_ids

    async def _load_policies(
        self,
        organization_id: uuid.UUID,
        workspace_id: Optional[uuid.UUID],
        project_id: Optional[uuid.UUID],
        scope: str,
    ) -> List[Tuple[GovernancePolicy, GovernancePolicyVersion]]:
        """Load active policies and their active versions for a given scope."""
        try:
            policies = await self.repo.list_policies(
                organization_id=organization_id,
                workspace_id=workspace_id,
                project_id=project_id,
                scope=scope,
                status=PolicyStatus.ACTIVE.value,
            )
        except Exception as exc:
            logger.warning("Governance: failed to load policies for scope %s: %s", scope, exc)
            return []

        result = []
        for policy in policies:
            if not policy.active_version_id:
                continue
            try:
                version = await self.repo.get_version(policy.active_version_id)
                if version and version.status == PolicyVersionStatus.ACTIVE.value:
                    result.append((policy, version))
            except Exception as exc:
                logger.warning("Governance: failed to load version for policy %s: %s", policy.id, exc)

        return result

    @staticmethod
    def _parse_rules(version: GovernancePolicyVersion) -> List[PolicyRule]:
        """Parse JSONB rules from a policy version into PolicyRule objects."""
        parsed = []
        for raw in (version.rules or []):
            try:
                parsed.append(PolicyRule.model_validate(raw))
            except Exception as exc:
                logger.warning("Governance: skipping malformed rule in version %s: %s", version.id, exc)
        return parsed
