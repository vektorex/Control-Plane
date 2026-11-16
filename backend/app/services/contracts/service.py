from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from .repository import ContractRepository
from .schemas import (
    WorkContractCreate,
    ContractDeliverableCreate,
    ServiceLevelAgreementCreate,
    ContractAcceptanceCriterionCreate,
)
from backend.app.db.models.contracts import (
    WorkContract,
    WorkContractVersion,
)
from backend.app.services.events.service import EventBus

class ContractService:
    def __init__(self, session: AsyncSession, event_bus: EventBus):
        self.session = session
        self.repository = ContractRepository(session)
        self.event_bus = event_bus

    async def create_draft(self, contract_in: WorkContractCreate, current_user_id: str) -> WorkContract:
        contract = await self.repository.create_contract(contract_in, current_user_id)
        # Create initial version
        await self.repository.create_version(contract.id, current_user_id, version=1)
        
        self.event_bus.publish(
            "contract.created",
            {
                "contract_id": contract.id,
                "workspace_id": contract.workspace_id,
                "created_by": current_user_id
            }
        )
        return contract
        
    async def get_contract(self, contract_id: str) -> Optional[WorkContract]:
        return await self.repository.get_contract(contract_id)

    async def list_contracts(self, workspace_id: Optional[str] = None) -> List[WorkContract]:
        return await self.repository.list_contracts(workspace_id)

    async def propose_contract(self, contract_id: str, current_user_id: str) -> Optional[WorkContract]:
        contract = await self.repository.update_contract_status(contract_id, "proposed")
        if contract:
            self.event_bus.publish(
                "contract.proposed",
                {
                    "contract_id": contract.id,
                    "workspace_id": contract.workspace_id,
                    "proposed_by": current_user_id
                }
            )
        return contract

    async def approve_contract(self, contract_id: str, approver_id: str) -> Optional[WorkContract]:
        contract = await self.repository.update_contract_status(contract_id, "approved")
        if contract:
            self.event_bus.publish(
                "contract.approved",
                {
                    "contract_id": contract.id,
                    "workspace_id": contract.workspace_id,
                    "approved_by": approver_id
                }
            )
        return contract

    async def activate_contract(self, contract_id: str, actor_id: str) -> Optional[WorkContract]:
        contract = await self.repository.get_contract(contract_id)
        if not contract or contract.status != "approved":
            return None # Must be approved first
            
        contract = await self.repository.update_contract_status(contract_id, "active")
        if contract:
            self.event_bus.publish(
                "contract.activated",
                {
                    "contract_id": contract.id,
                    "workspace_id": contract.workspace_id,
                    "actor_id": actor_id
                }
            )
        return contract
