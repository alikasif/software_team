from typing import Literal

from pydantic import BaseModel
from pydantic import Field

SplitMethod = Literal["equal", "percentage", "exact"]


class PercentageParticipant(BaseModel):
    user_id: str
    percentage: float = Field(gt=0, le=100)


class ExactParticipant(BaseModel):
    user_id: str
    amount: float = Field(gt=0)
