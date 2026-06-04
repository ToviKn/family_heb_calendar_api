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
    family_name: str | None = None
    role: str
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FamilyListResponse(BaseModel):
    families: list[FamilyResponse]
    total: int


class FamilyJoinRequestResponse(BaseModel):
    status: str
    message: str


class FamilyJoinRequestUserResponse(BaseModel):
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class FamilyJoinRequestDetailResponse(BaseModel):
    id: int
    user_id: int
    family_id: int
    family_name: str | None = None
    requested_by: int
    status: str
    created_at: datetime
    user: FamilyJoinRequestUserResponse
    requested_by_user: FamilyJoinRequestUserResponse


class FamilyJoinRequestListResponse(BaseModel):
    requests: list[FamilyJoinRequestDetailResponse]
    total: int
