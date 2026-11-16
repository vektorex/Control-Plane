from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from .enums import PortfolioStatus, TrainStatus

class PortfolioCreate(BaseModel):
    name: str
    description: Optional[str] = None

class PortfolioResponse(PortfolioCreate):
    id: str
    status: PortfolioStatus
    model_config = ConfigDict(from_attributes=True)

class TrainCreate(BaseModel):
    name: str
    description: Optional[str] = None
    portfolio_id: str

class TrainResponse(TrainCreate):
    id: str
    status: TrainStatus
    model_config = ConfigDict(from_attributes=True)
