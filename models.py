import enum
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RoleEnum(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class ExecutionStatusEnum(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    memberships: Mapped[list["CompanyMember"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    plan_tier: Mapped[str] = mapped_column(String(50), default="free")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    members: Mapped[list["CompanyMember"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    pipelines: Mapped[list["Pipeline"]] = relationship(back_populates="company", cascade="all, delete-orphan")


class CompanyMember(Base):
    __tablename__ = "company_members"
    __table_args__ = (UniqueConstraint("user_id", "company_id", name="uq_user_company"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), default=RoleEnum.MEMBER, nullable=False)

    user: Mapped["User"] = relationship(back_populates="memberships")
    company: Mapped["Company"] = relationship(back_populates="members")


class Pipeline(Base):
    __tablename__ = "pipelines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    company: Mapped["Company"] = relationship(back_populates="pipelines")
    executions: Mapped[list["Execution"]] = relationship(back_populates="pipeline", cascade="all, delete-orphan")


class Execution(Base):
    __tablename__ = "executions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pipeline_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[ExecutionStatusEnum] = mapped_column(Enum(ExecutionStatusEnum), default=ExecutionStatusEnum.PENDING)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)

    pipeline: Mapped["Pipeline"] = relationship(back_populates="executions")