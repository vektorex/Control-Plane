from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from .enums import RolloutStatus, StrategyType

class RolloutCreate(BaseModel):
    name: str
    description: Optional[str] = None
    release_id: str
    strategy_type: StrategyType
    target_scope: dict
    policy: dict

class RolloutResponse(RolloutCreate):
    id: str
    status: RolloutStatus\n