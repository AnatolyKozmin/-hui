from __future__ import annotations

import enum
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .engine import Base


class SheetKind(enum.Enum):
    NE_OPYT = "ne_opyt"
    OPYT = "opyt"
    SVOD = "svod"


class Faculty(Base):
    __tablename__ = "faculties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(256))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    admins: Mapped[List[FacultyAdmin]] = relationship(
        back_populates="faculty", cascade="all, delete-orphan"
    )
    sheets: Mapped[List[FacultySheet]] = relationship(
        back_populates="faculty", cascade="all, delete-orphan"
    )


class FacultyAdmin(Base):
    __tablename__ = "faculty_admins"
    __table_args__ = (
        UniqueConstraint("faculty_id", "telegram_user_id", name="uq_admin_faculty_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    faculty_id: Mapped[int] = mapped_column(
        ForeignKey("faculties.id", ondelete="CASCADE"), index=True, nullable=False
    )
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    is_superadmin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    faculty: Mapped[Faculty] = relationship(back_populates="admins")


class FacultySheet(Base):
    __tablename__ = "faculty_sheets"
    __table_args__ = (
        UniqueConstraint("faculty_id", "kind", name="uq_faculty_kind"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    faculty_id: Mapped[int] = mapped_column(
        ForeignKey("faculties.id", ondelete="CASCADE"), index=True, nullable=False
    )
    kind: Mapped[SheetKind] = mapped_column(Enum(SheetKind), nullable=False)

    # Google sheet identifiers
    spreadsheet_id: Mapped[str] = mapped_column(String(128), nullable=False)
    # Optional individual sheet/tab names if needed; can be kept as the default
    sheet_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    faculty: Mapped[Faculty] = relationship(back_populates="sheets")


class Participant(Base):
    __tablename__ = "participants"
    __table_args__ = (
        UniqueConstraint("faculty_id", "vk_id", name="uq_participant_faculty_vk"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    faculty_id: Mapped[int] = mapped_column(
        ForeignKey("faculties.id", ondelete="CASCADE"), index=True, nullable=False
    )

    # VK identity and profile fields
    vk_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(128), nullable=False)
    last_name: Mapped[str] = mapped_column(String(128), nullable=False)
    is_name_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Telegram linkage set after successful registration
    tg_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)
    tg_username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Optional import provenance (e.g., parsed from svod participants sheet)
    source_sheet_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("faculty_sheets.id", ondelete="SET NULL"), nullable=True
    )

    faculty: Mapped[Faculty] = relationship()
    source_sheet: Mapped[Optional[FacultySheet]] = relationship()


class Interviewer(Base):
    __tablename__ = "interviewers"
    __table_args__ = (
        # A tab (sheet) name must be unique within a specific sheet document
        UniqueConstraint(
            "faculty_sheet_id", "tab_name", name="uq_interviewer_sheet_tab"
        ),
        # Each interviewer can only bind a single Telegram account
        UniqueConstraint("tg_id", name="uq_interviewer_tg_id"),
        # Invite tokens should be unique to be shareable links
        UniqueConstraint("invite_token", name="uq_interviewer_invite_token"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    faculty_id: Mapped[int] = mapped_column(
        ForeignKey("faculties.id", ondelete="CASCADE"), index=True, nullable=False
    )
    faculty_sheet_id: Mapped[int] = mapped_column(
        ForeignKey("faculty_sheets.id", ondelete="CASCADE"), index=True, nullable=False
    )

    # Tab name inside the Google Sheet representing this interviewer
    tab_name: Mapped[str] = mapped_column(String(128), nullable=False)

    # Experience group inferred from the sheet this interviewer belongs to
    # Duplicated for quick filtering, but source of truth is the sheet kind
    experience_kind: Mapped[SheetKind] = mapped_column(Enum(SheetKind), nullable=False)

    # Invitation and Telegram linkage
    invite_token: Mapped[str] = mapped_column(String(64), nullable=False)
    tg_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)
    tg_username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    faculty: Mapped[Faculty] = relationship()
    sheet: Mapped[FacultySheet] = relationship()


__all__ = [
    "SheetKind",
    "Faculty",
    "FacultyAdmin",
    "FacultySheet",
    "Participant",
    "Interviewer",
]
