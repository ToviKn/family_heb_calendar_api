from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FamilyResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FamilyMembershipResponse(BaseModel):
    id: int
    user_id: int
    family_id: int
    role: str
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FamilyListResponse(BaseModel):
    families: list[FamilyResponse]
    total: int
