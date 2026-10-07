from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
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
    def __init__(self, session: Session):
        self.session = session

    def create_contract(self, contract_in: WorkContractCreate, created_by: str) -> WorkContract:
        import uuid
        contract_id = str(uuid.uuid4())
        contract = WorkContract(
            id=contract_id,
            **contract_in.model_dump(),
            created_by=created_by
        )
        self.session.add(contract)
        self.session.flush()
        return contract

    def get_contract(self, contract_id: str) -> Optional[WorkContract]:
        return self.session.execute(
            select(WorkContract).where(WorkContract.id == contract_id)
        ).scalar_one_or_none()

    def update_contract_status(self, contract_id: str, status: str) -> Optional[WorkContract]:
        contract = self.get_contract(contract_id)
        if contract:
            contract.status = status
            self.session.flush()
        return contract

    def create_version(self, contract_id: str, created_by: str, version: int = 1) -> WorkContractVersion:
        import uuid
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
        self.session.flush()
        return cv

    def add_deliverable(self, version_id: str, deliverable_in: ContractDeliverableCreate) -> ContractDeliverable:
        import uuid
        d = ContractDeliverable(
            id=str(uuid.uuid4()),
            contract_version_id=version_id,
            **deliverable_in.model_dump()
        )
        self.session.add(d)
        self.session.flush()
        return d
        
    def add_sla(self, version_id: str, sla_in: ServiceLevelAgreementCreate) -> ServiceLevelAgreement:
        import uuid
        sla = ServiceLevelAgreement(
            id=str(uuid.uuid4()),
            contract_version_id=version_id,
            **sla_in.model_dump()
        )
        self.session.add(sla)
        self.session.flush()
        return sla

    def get_deliverables(self, version_id: str) -> List[ContractDeliverable]:
        return list(self.session.execute(
            select(ContractDeliverable).where(ContractDeliverable.contract_version_id == version_id)
        ).scalars().all())

    def get_slas(self, version_id: str) -> List[ServiceLevelAgreement]:
        return list(self.session.execute(
            select(ServiceLevelAgreement).where(ServiceLevelAgreement.contract_version_id == version_id)
        ).scalars().all())

    def get_measurements(self, contract_id: str) -> List[SLAMeasurement]:
        return list(self.session.execute(
            select(SLAMeasurement).where(SLAMeasurement.contract_id == contract_id).order_by(desc(SLAMeasurement.measured_at))
        ).scalars().all())
