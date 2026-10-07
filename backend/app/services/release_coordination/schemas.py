from pydantic import BaseModel
from typing import List, Optional
from .enums import PortfolioStatus, TrainStatus

class PortfolioCreate(BaseModel):
    name: str
    description: Optional[str] = None

class PortfolioResponse(PortfolioCreate):
    id: str
    status: PortfolioStatus

class TrainCreate(BaseModel):
    name: str
    description: Optional[str] = None
    portfolio_id: str

class TrainResponse(TrainCreate):
    id: str
    status: TrainStatus
