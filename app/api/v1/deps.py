import uuid
from dataclasses import dataclass
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, settings
from models import Company, CompanyMember, RoleEnum, User

# HTTPBearer додає зручну кнопку "Authorize" (замочок) у Swagger UI (/docs),
# куди можна просто вставити наш JWT-токен.
security_scheme = HTTPBearer()


@dataclass
class TenantContext:
    """Контекст авторизованого запиту: хто робить запит, у якій компанії та з якою роллю."""
    user: User
    company_id: uuid.UUID
    role: RoleEnum


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> tuple[User, dict]:
    """Розшифровує JWT-токен та дістає активного користувача з БД."""
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не вдалося підтвердити облікові дані або токен прострочений.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id_str: str | None = payload.get("sub")
        if not user_id_str:
            raise credentials_exception
        user_uuid = uuid.UUID(user_id_str)
    except (jwt.PyJWTError, ValueError):
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalars().first()

    if not user or not user.is_active:
        raise credentials_exception

    return user, payload


class RequireRole:
    """
    Dependency для перевірки ролі та жорсткої ізоляції по company_id.
    Використання: ctx: TenantContext = Depends(RequireRole([RoleEnum.OWNER, RoleEnum.ADMIN]))
    """
    def __init__(self, allowed_roles: list[RoleEnum]):
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        user_and_payload: tuple[User, dict] = Depends(get_current_user),
        x_company_id: uuid.UUID | None = Header(default=None, alias="X-Company-ID"),
        db: AsyncSession = Depends(get_db),
    ) -> TenantContext:
        user, payload = user_and_payload

        # 1. Визначаємо цільовий company_id (пріоритет у заголовка X-Company-ID, інакше беремо з токена)
        target_company_id = x_company_id
        if not target_company_id and payload.get("company_id"):
            try:
                target_company_id = uuid.UUID(payload["company_id"])
            except ValueError:
                pass

        if not target_company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не вказано ID компанії (Workspace). Передайте заголовок X-Company-ID.",
            )

        # 2. Перевіряємо в БД реальне членство користувача в цій компанії
        result = await db.execute(
            select(CompanyMember).where(
                CompanyMember.user_id == user.id,
                CompanyMember.company_id == target_company_id,
            )
        )
        membership = result.scalars().first()

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас немає доступу до цієї компанії (Workspace).",
            )

        # 3. Перевіряємо, чи дозволена його роль для цього ендпоінта
        if membership.role not in self.allowed_roles:
            allowed_names = ", ".join([r.value for r in self.allowed_roles])
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостатньо прав. Необхідна одна з ролей: {allowed_names}. Ваша роль: {membership.role.value}.",
            )

        return TenantContext(
            user=user,
            company_id=target_company_id,
            role=membership.role,
        )


# Готові шорткати для зручного використання у роутерах:
AllowAnyMember = RequireRole([RoleEnum.OWNER, RoleEnum.ADMIN, RoleEnum.MEMBER])
AllowAdminOrOwner = RequireRole([RoleEnum.OWNER, RoleEnum.ADMIN])
AllowOwnerOnly = RequireRole([RoleEnum.OWNER])