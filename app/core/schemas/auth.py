from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Мінімум 6 символів")
    full_name: str | None = None
    company_name: str = Field(..., description="Назва першої компанії (Workspace)")


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"