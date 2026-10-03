"""
Public API Authentication & API Principal Resolution.
Step 37: Public API, Developer Platform & SDK Layer.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set
import uuid
from fastapi import Header, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.services.developer_platform.api_keys import APIKeyManager
from backend.app.services.developer_platform.errors import (
    ApplicationSuspendedError,
    AuthenticationFailedError,
    CredentialExpiredError,
    CredentialRevokedError,
)
from backend.app.services.developer_platform.models import (
    APICredential,
    APIResourceScope,
    APIScopeAssignment,
    DeveloperApplication,
)


@dataclass
class APIPrincipal:
    """Represents the authenticated external API client during request lifecycle."""
    application_id: str
    organization_id: str
    environment: str
    credential_id: str
    scopes: Set[str] = field(default_factory=set)
    resource_scope_type: str = "organization"  # organization, workspace, project
    workspace_id: Optional[str] = None
    project_id: Optional[str] = None
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))


class PublicAPIAuthenticator:
    """Authenticates incoming public API requests and derives the APIPrincipal."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def authenticate(
        self,
        request: Request,
        authorization: Optional[str] = Header(None),
        x_api_key: Optional[str] = Header(None),
        request_id: Optional[str] = Header(None, alias="X-Request-ID"),
    ) -> APIPrincipal:
        """
        Extracts key, hashes it, verifies status/expiration, loads application & scopes,
        and constructs the verified APIPrincipal.
        """
        req_id = request_id or str(uuid.uuid4())
        raw_key = ""

        # 1. Extract key from Authorization Bearer or X-API-Key
        if authorization and authorization.lower().startswith("bearer "):
            raw_key = authorization[7:].strip()
        elif x_api_key:
            raw_key = x_api_key.strip()

        if not raw_key:
            raise AuthenticationFailedError("Missing API key. Provide via 'Authorization: Bearer <key>' or 'X-API-Key'.")

        # 2. Extract prefix and hash
        key_hash = APIKeyManager.hash_key(raw_key)

        # 3. Query DB for credential with preloaded scopes and resource scopes
        query = (
            select(APICredential)
            .where(APICredential.key_hash == key_hash)
            .options(
                selectinload(APICredential.application),
                selectinload(APICredential.scopes),
                selectinload(APICredential.resource_scopes),
            )
        )
        result = await self.session.execute(query)
        cred: Optional[APICredential] = result.scalars().first()

        if not cred:
            # Emit security telemetry for invalid credential
            await self._record_security_signal(
                signal_type="invalid_credential_probe",
                severity="medium",
                details={"prefix": raw_key[:12] if len(raw_key) >= 12 else "unknown"},
            )
            raise AuthenticationFailedError("Invalid API key.")

        # 4. Check credential status
        if cred.status == "revoked":
            await self._record_security_signal(
                signal_type="revoked_credential_usage",
                severity="high",
                credential_id=cred.id,
                organization_id=cred.application.organization_id if cred.application else None,
            )
            raise CredentialRevokedError("This API credential has been revoked.")

        now = datetime.now(timezone.utc)
        if cred.expires_at and cred.expires_at < now:
            cred.status = "expired"
            await self.session.commit()
            raise CredentialExpiredError("This API credential has expired.")

        # 5. Check application status
        app: DeveloperApplication = cred.application
        if not app or app.status != "active":
            raise ApplicationSuspendedError(f"Application is currently {app.status if app else 'inactive'}.")

        # 6. Update last_used_at
        cred.last_used_at = now
        await self.session.commit()

        # 7. Extract scopes & resource constraints
        scopes: Set[str] = {s.scope for s in cred.scopes}
        res_scope_type = "organization"
        workspace_id = None
        project_id = None

        if cred.resource_scopes:
            rs: APIResourceScope = cred.resource_scopes[0]
            res_scope_type = rs.resource_scope_type
            workspace_id = rs.workspace_id
            project_id = rs.project_id

        return APIPrincipal(
            application_id=app.id,
            organization_id=app.organization_id,
            environment=cred.environment,
            credential_id=cred.id,
            scopes=scopes,
            resource_scope_type=res_scope_type,
            workspace_id=workspace_id,
            project_id=project_id,
            request_id=req_id,
        )

    async def _record_security_signal(
        self,
        signal_type: str,
        severity: str = "medium",
        credential_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Best-effort security signal dispatch using Step 34."""
        try:
            from backend.app.services.security.service import SecurityService
            from backend.app.services.security.schemas import SecurityEventNormalized

            sec_svc = SecurityService(self.session)
            norm_event = SecurityEventNormalized(
                event_type="api_security_anomaly",
                actor_type="api_client",
                actor_id=credential_id,
                organization_id=organization_id,
                severity=severity,
                title=f"Public API Security Signal: {signal_type}",
                description=f"Detected {signal_type} during public API authentication.",
                metadata=details or {},
            )
            await sec_svc.ingest_event(norm_event)
        except Exception:
            pass  # Do not block request flow on security telemetry recording
