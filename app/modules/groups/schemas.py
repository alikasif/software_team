from datetime import datetime

from pydantic import BaseModel
from pydantic import Field


class GroupCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class GroupResponse(BaseModel):
    id: str
    name: str
    created_by_user_id: str
    created_at: datetime


class GroupMemberAddRequest(BaseModel):
    user_id: str
    role: str = Field(default="member", pattern="^(owner|member)$")


class GroupMemberResponse(BaseModel):
    group_id: str
    user_id: str
    role: str
    joined_at: datetime
