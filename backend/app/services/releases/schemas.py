from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from .enums import ReleaseStatus, ReleaseType

class ReleaseCreate(BaseModel):
    name: str
    description: Optional[str] = None
    change_request_id: str
    release_type: ReleaseType
    source_environment: str
    target_environment: str

class ReleaseResponse(ReleaseCreate):
    id: str
    status: ReleaseStatus
    model_config = ConfigDict(from_attributes=True)
