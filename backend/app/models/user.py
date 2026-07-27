from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: str
    language: str

    model_config = ConfigDict(from_attributes=True)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ChangePasswordResponse(BaseModel):
    status: str
    message: str


class UserLanguageUpdate(BaseModel):
    language: str


class AuthLoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
