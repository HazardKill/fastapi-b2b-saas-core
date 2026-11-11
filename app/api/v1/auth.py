import re
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Company, CompanyMember, RoleEnum, User
from app.schemas.auth import TokenResponse, UserLogin, UserRegister
from app.core.security import create_access_token, get_password_hash, verify_password
from app.api.v1.deps import AllowAnyMember, TenantContext

router = APIRouter(prefix="/auth", tags=["Auth"])


def generate_slug(name: str) -> str:
    # Залишаємо лише латиницю, цифри та дефіси, а якщо назва кирилицею — додаємо хеш
    base_slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not base_slug:
        base_slug = "workspace"
    return f"{base_slug}-{uuid.uuid4().hex[:6]}"


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    # 1. Перевіряємо, чи існує користувач із таким email
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Користувач із таким email вже зареєстрований.",
        )

    # 2. Створюємо користувача
    new_user = User(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name,
    )
    db.add(new_user)
    await db.flush()

    # 3. Створюємо компанію (Workspace) з гарантовано унікальним slug
    new_company = Company(
        name=data.company_name,
        slug=generate_slug(data.company_name),
        plan_tier="free",
    )
    db.add(new_company)
    await db.flush()

    # 4. Прив'язуємо користувача до компанії з роллю OWNER
    membership = CompanyMember(
        user_id=new_user.id,
        company_id=new_company.id,
        role=RoleEnum.OWNER,
    )
    db.add(membership)
    await db.commit()

    # 5. Випускаємо JWT-токен (одразу зашиваємо туди ID юзера та активну компанію)
    access_token = create_access_token(
        data={"sub": str(new_user.id), "company_id": str(new_company.id), "role": RoleEnum.OWNER.value}
    )
    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalars().first()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невірний email або пароль.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Дістаємо першу компанію користувача для токена
    member_res = await db.execute(
        select(CompanyMember).where(CompanyMember.user_id == user.id)
    )
    membership = member_res.scalars().first()

    token_data = {"sub": str(user.id)}
    if membership:
        token_data["company_id"] = str(membership.company_id)
        token_data["role"] = membership.role.value

    access_token = create_access_token(data=token_data)
    return TokenResponse(access_token=access_token)

@router.get("/me")
async def get_my_profile(ctx: TenantContext = Depends(AllowAnyMember)):
    """Повертає профіль поточного користувача та контекст його активної компанії."""
    return {
        "user_id": ctx.user.id,
        "email": ctx.user.email,
        "full_name": ctx.user.full_name,
        "active_company_id": ctx.company_id,
        "role": ctx.role,
    }