"""
DeveloperPlatformService: Unified Facade for Developer Platform Operations.
Step 37: Public API, Developer Platform & SDK Layer.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.developer_platform.applications import ApplicationService
from backend.app.services.developer_platform.credentials import CredentialService
from backend.app.services.developer_platform.idempotency import IdempotencyService
from backend.app.services.developer_platform.quotas import QuotaService
from backend.app.services.developer_platform.repository import DeveloperPlatformRepository
from backend.app.services.developer_platform.usage import APIUsageService
from backend.app.services.developer_platform.webhook_delivery import WebhookDeliveryService
from backend.app.services.developer_platform.webhooks import WebhookService


class DeveloperPlatformService:
    """
    Unified facade coordinating applications, credentials, webhooks,
    idempotency, quotas, usage tracking, and repository queries.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = DeveloperPlatformRepository(session)
        self.applications = ApplicationService(session)
        self.credentials = CredentialService(session)
        self.webhooks = WebhookService(session)
        self.webhook_delivery = WebhookDeliveryService(session)
        self.usage = APIUsageService(session)
        self.quotas = QuotaService(session)
        self.idempotency = IdempotencyService(session)
