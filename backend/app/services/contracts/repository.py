from typing import List, Optional, Dict, Any
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.db.models.contracts import (
    WorkContract,
    WorkContractVersion,
    ContractParty,
    ContractScope,
    ContractDeliverable,
    ContractAcceptanceCriterion,
    ServiceLevelAgreement,
    SLAMeasurement,
    ContractBreach,
)
from .schemas import (
    WorkContractCreate,
    ContractDeliverableCreate,
    ServiceLevelAgreementCreate,
    ContractAcceptanceCriterionCreate,
)

class ContractRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_contract(self, contract_in: WorkContractCreate, created_by: str) -> WorkContract:
        contract_id = str(uuid.uuid4())
        contract = WorkContract(
            id=contract_id,
            **contract_in.model_dump(),
            created_by=created_by
        )
        self.session.add(contract)
        await self.session.flush()
        await self.session.refresh(contract)
        return contract

    async def get_contract(self, contract_id: str) -> Optional[WorkContract]:
        result = await self.session.execute(
            select(WorkContract).where(WorkContract.id == contract_id)
        )
        return result.scalar_one_or_none()

    async def list_contracts(self, workspace_id: Optional[str] = None) -> List[WorkContract]:
        query = select(WorkContract)
        if workspace_id:
            query = query.where(WorkContract.workspace_id == workspace_id)
        query = query.order_by(desc(WorkContract.created_at))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_contract_status(self, contract_id: str, status: str) -> Optional[WorkContract]:
        contract = await self.get_contract(contract_id)
        if contract:
            contract.status = status
            await self.session.flush()
            await self.session.refresh(contract)
        return contract

    async def create_version(self, contract_id: str, created_by: str, version: int = 1) -> WorkContractVersion:
        cv = WorkContractVersion(
            id=str(uuid.uuid4()),
            contract_id=contract_id,
            version=version,
            scope_snapshot={},
            deliverables_snapshot={},
            acceptance_snapshot={},
            sla_snapshot={},
            resource_snapshot={},
            policy_snapshot={},
            created_by=created_by
        )
        self.session.add(cv)
        await self.session.flush()
        return cv

    async def add_deliverable(self, version_id: str, deliverable_in: ContractDeliverableCreate) -> ContractDeliverable:
        d = ContractDeliverable(
            id=str(uuid.uuid4()),
            contract_version_id=version_id,
            **deliverable_in.model_dump()
        )
        self.session.add(d)
        await self.session.flush()
        return d
        
    async def add_sla(self, version_id: str, sla_in: ServiceLevelAgreementCreate) -> ServiceLevelAgreement:
        sla = ServiceLevelAgreement(
            id=str(uuid.uuid4()),
            contract_version_id=version_id,
            **sla_in.model_dump()
        )
        self.session.add(sla)
        await self.session.flush()
        return sla

    async def get_deliverables(self, version_id: str) -> List[ContractDeliverable]:
        result = await self.session.execute(
            select(ContractDeliverable).where(ContractDeliverable.contract_version_id == version_id)
        )
        return list(result.scalars().all())

    async def get_slas(self, version_id: str) -> List[ServiceLevelAgreement]:
        result = await self.session.execute(
            select(ServiceLevelAgreement).where(ServiceLevelAgreement.contract_version_id == version_id)
        )
        return list(result.scalars().all())

    async def get_measurements(self, contract_id: str) -> List[SLAMeasurement]:
        result = await self.session.execute(
            select(SLAMeasurement).where(SLAMeasurement.contract_id == contract_id).order_by(desc(SLAMeasurement.measured_at))
        )
        return list(result.scalars().all())
