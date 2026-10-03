"""
API Credential Lifecycle Management (Creation, Rotation, Revocation).
Step 37: Public API, Developer Platform & SDK Layer.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Set, Tuple
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.services.developer_platform.api_keys import APIKeyManager
from backend.app.services.developer_platform.errors import (
    PublicAPIException,
    ResourceNotFoundError,
    ScopeDeniedError,
)
from backend.app.services.developer_platform.models import (
    APICredential,
    APIResourceScope,
    APIScopeAssignment,
    DeveloperApplication,
)
from backend.app.services.developer_platform.schemas import (
    APICredentialCreate,
    APICredentialRotateRequest,
    ResourceScopeCreate,
)
from backend.app.services.developer_platform.scopes import ScopeRegistry


class CredentialService:
    """Manages API keys, rotation, revocation, and scope boundaries."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_credential(
        self,
        application_id: str,
        organization_id: str,
        user_id: Optional[str],
        data: APICredentialCreate,
        creator_permissions: Optional[Set[str]] = None,
        is_org_admin: bool = False,
    ) -> Tuple[APICredential, str]:
        """
        Creates a new API credential for an application.
        Returns (APICredential, plaintext_secret_key).
        The plaintext key is returned ONLY here and must never be stored.
        """
        # 1. Fetch application and verify org ownership
        app_q = select(DeveloperApplication).where(
            DeveloperApplication.id == application_id,
            DeveloperApplication.organization_id == organization_id,
        )
        app_res = await self.session.execute(app_q)
        app: Optional[DeveloperApplication] = app_res.scalars().first()
        if not app:
            raise ResourceNotFoundError("Developer application", application_id)

        # 2. Validate requested scopes
        invalid_scopes = ScopeRegistry.validate_scopes(data.scopes)
        if invalid_scopes:
            raise PublicAPIException(
                f"Invalid scopes requested: {', '.join(invalid_scopes)}",
                status_code=400,
            )

        # 3. Prevent privilege escalation
        if creator_permissions is not None:
            disallowed = ScopeRegistry.check_privilege_escalation(
                requested_scopes=data.scopes,
                creator_permissions=creator_permissions,
                is_org_admin=is_org_admin,
            )
            if disallowed:
                raise ScopeDeniedError(
                    required_scope=disallowed[0],
                    message=f"Privilege escalation prevented: cannot grant {', '.join(disallowed)}",
                )

        # 4. Generate key
        plaintext_key, key_prefix, key_hash = APIKeyManager.generate_key(app.environment)

        now = datetime.now(timezone.utc)
        expires_at = None
        if data.expires_in_days:
            expires_at = now + timedelta(days=data.expires_in_days)

        cred_id = str(uuid.uuid4())
        cred = APICredential(
            id=cred_id,
            application_id=application_id,
            name=data.name,
            key_prefix=key_prefix,
            key_hash=key_hash,
            credential_type="api_key",
            environment=app.environment,
            status="active",
            created_at=now,
            expires_at=expires_at,
            created_by=user_id,
        )
        self.session.add(cred)

        # 5. Add scope assignments
        for sc in data.scopes:
            assignment = APIScopeAssignment(
                id=str(uuid.uuid4()),
                credential_id=cred_id,
                scope=sc,
                created_at=now,
            )
            self.session.add(assignment)

        # 6. Add resource scope constraint if provided
        if data.resource_scope:
            rs = APIResourceScope(
                id=str(uuid.uuid4()),
                credential_id=cred_id,
                resource_scope_type=data.resource_scope.resource_scope_type,
                workspace_id=data.resource_scope.workspace_id,
                project_id=data.resource_scope.project_id,
                created_at=now,
            )
            self.session.add(rs)

        await self.session.commit()

        # Emit compliance evidence (Step 33)
        await self._record_compliance_evidence(
            action="credential_created",
            credential_id=cred_id,
            application_id=application_id,
            organization_id=organization_id,
            actor_id=user_id,
        )

        return cred, plaintext_key

    async def rotate_credential(
        self,
        credential_id: str,
        organization_id: str,
        user_id: Optional[str],
        data: APICredentialRotateRequest,
    ) -> Tuple[APICredential, str]:
        """
        Rotates an existing credential: creates a new key with identical scopes and constraints.
        Old key is marked 'rotated' but remains temporarily functional until explicitly revoked.
        Returns (new_APICredential, plaintext_new_key).
        """
        old_cred = await self.get_credential(credential_id, organization_id)
        app: DeveloperApplication = old_cred.application

        # Generate new key
        plaintext_key, key_prefix, key_hash = APIKeyManager.generate_key(old_cred.environment)

        now = datetime.now(timezone.utc)
        expires_at = None
        if data.expires_in_days:
            expires_at = now + timedelta(days=data.expires_in_days)

        new_cred_id = str(uuid.uuid4())
        new_cred = APICredential(
            id=new_cred_id,
            application_id=old_cred.application_id,
            name=f"{old_cred.name} (Rotated)",
            key_prefix=key_prefix,
            key_hash=key_hash,
            credential_type=old_cred.credential_type,
            environment=old_cred.environment,
            status="active",
            created_at=now,
            expires_at=expires_at,
            created_by=user_id,
        )
        self.session.add(new_cred)

        # Copy scopes
        for sc in old_cred.scopes:
            assignment = APIScopeAssignment(
                id=str(uuid.uuid4()),
                credential_id=new_cred_id,
                scope=sc.scope,
                created_at=now,
            )
            self.session.add(assignment)

        # Copy resource scopes
        for rs in old_cred.resource_scopes:
            new_rs = APIResourceScope(
                id=str(uuid.uuid4()),
                credential_id=new_cred_id,
                resource_scope_type=rs.resource_scope_type,
                workspace_id=rs.workspace_id,
                project_id=rs.project_id,
                created_at=now,
            )
            self.session.add(new_rs)

        # Mark old credential as rotated
        old_cred.status = "rotated"

        await self.session.commit()

        await self._record_compliance_evidence(
            action="credential_rotated",
            credential_id=new_cred_id,
            application_id=old_cred.application_id,
            organization_id=organization_id,
            actor_id=user_id,
        )

        return new_cred, plaintext_key

    async def revoke_credential(
        self,
        credential_id: str,
        organization_id: str,
        user_id: Optional[str],
    ) -> APICredential:
        """Revokes an active or rotated credential."""
        cred = await self.get_credential(credential_id, organization_id)
        cred.status = "revoked"
        cred.revoked_at = datetime.now(timezone.utc)
        await self.session.commit()

        await self._record_compliance_evidence(
            action="credential_revoked",
            credential_id=cred.id,
            application_id=cred.application_id,
            organization_id=organization_id,
            actor_id=user_id,
        )
        return cred

    async def get_credential(self, credential_id: str, organization_id: str) -> APICredential:
        """Loads credential with scopes ensuring organization ownership."""
        query = (
            select(APICredential)
            .join(DeveloperApplication, APICredential.application_id == DeveloperApplication.id)
            .where(
                APICredential.id == credential_id,
                DeveloperApplication.organization_id == organization_id,
            )
            .options(
                selectinload(APICredential.application),
                selectinload(APICredential.scopes),
                selectinload(APICredential.resource_scopes),
            )
        )
        res = await self.session.execute(query)
        cred = res.scalars().first()
        if not cred:
            raise ResourceNotFoundError("API credential", credential_id)
        return cred

    async def list_credentials(self, application_id: str, organization_id: str) -> List[APICredential]:
        """Lists credentials belonging to an application."""
        query = (
            select(APICredential)
            .join(DeveloperApplication, APICredential.application_id == DeveloperApplication.id)
            .where(
                APICredential.application_id == application_id,
                DeveloperApplication.organization_id == organization_id,
            )
            .options(
                selectinload(APICredential.scopes),
                selectinload(APICredential.resource_scopes),
            )
            .order_by(APICredential.created_at.desc())
        )
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def _record_compliance_evidence(
        self,
        action: str,
        credential_id: str,
        application_id: str,
        organization_id: str,
        actor_id: Optional[str],
    ) -> None:
        """Best-effort logging into Step 33 ComplianceEvidence."""
        try:
            from backend.app.services.data_governance.service import DataGovernanceService
            from backend.app.services.data_governance.schemas import ComplianceEvidenceCreate
            import uuid

            dg_svc = DataGovernanceService(self.session)
            req = ComplianceEvidenceCreate(
                evidence_type="api_credential_audit",
                framework="soc2_type_ii",
                control_id="cc6.1_credential_management",
                collected_by=uuid.UUID(actor_id) if actor_id else uuid.uuid4(),
                description=f"Public API credential event: {action}",
                details={
                    "action": action,
                    "credential_id": credential_id,
                    "application_id": application_id,
                    "organization_id": organization_id,
                },
            )
            await dg_svc.create_compliance_evidence(uuid.UUID(organization_id), req)
        except Exception:
            pass
