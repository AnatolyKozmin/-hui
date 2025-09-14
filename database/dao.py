from typing import List, Optional
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import Faculty, FacultyAdmin, FacultySheet, Interviewer, Participant, SheetKind


class BaseDAO:
    def __init__(self, session: AsyncSession):
        self.session = session


class FacultyDAO(BaseDAO):
    async def create(self, slug: str, title: str, is_active: bool = True) -> Faculty:
        faculty = Faculty(slug=slug, title=title, is_active=is_active)
        self.session.add(faculty)
        await self.session.commit()
        await self.session.refresh(faculty)
        return faculty

    async def get_by_id(self, faculty_id: int) -> Optional[Faculty]:
        result = await self.session.execute(
            select(Faculty).where(Faculty.id == faculty_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Faculty]:
        result = await self.session.execute(
            select(Faculty).where(Faculty.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> List[Faculty]:
        result = await self.session.execute(select(Faculty))
        return list(result.scalars().all())

    async def update(self, faculty_id: int, **kwargs) -> Optional[Faculty]:
        await self.session.execute(
            update(Faculty).where(Faculty.id == faculty_id).values(**kwargs)
        )
        await self.session.commit()
        return await self.get_by_id(faculty_id)

    async def delete(self, faculty_id: int) -> bool:
        result = await self.session.execute(
            delete(Faculty).where(Faculty.id == faculty_id)
        )
        await self.session.commit()
        return result.rowcount > 0


class FacultyAdminDAO(BaseDAO):
    async def create(self, faculty_id: int, telegram_user_id: int, is_superadmin: bool = False) -> FacultyAdmin:
        admin = FacultyAdmin(
            faculty_id=faculty_id,
            telegram_user_id=telegram_user_id,
            is_superadmin=is_superadmin
        )
        self.session.add(admin)
        await self.session.commit()
        await self.session.refresh(admin)
        return admin

    async def get_by_telegram_id(self, telegram_user_id: int) -> Optional[FacultyAdmin]:
        result = await self.session.execute(
            select(FacultyAdmin)
            .options(selectinload(FacultyAdmin.faculty))
            .where(FacultyAdmin.telegram_user_id == telegram_user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_faculty(self, faculty_id: int) -> List[FacultyAdmin]:
        result = await self.session.execute(
            select(FacultyAdmin)
            .options(selectinload(FacultyAdmin.faculty))
            .where(FacultyAdmin.faculty_id == faculty_id)
        )
        return list(result.scalars().all())

    async def is_superadmin(self, telegram_user_id: int) -> bool:
        result = await self.session.execute(
            select(FacultyAdmin.is_superadmin)
            .where(FacultyAdmin.telegram_user_id == telegram_user_id)
        )
        return result.scalar_one_or_none() or False

    async def delete(self, admin_id: int) -> bool:
        result = await self.session.execute(
            delete(FacultyAdmin).where(FacultyAdmin.id == admin_id)
        )
        await self.session.commit()
        return result.rowcount > 0


class FacultySheetDAO(BaseDAO):
    async def create(self, faculty_id: int, kind: SheetKind, spreadsheet_id: str, sheet_name: Optional[str] = None) -> FacultySheet:
        sheet = FacultySheet(
            faculty_id=faculty_id,
            kind=kind,
            spreadsheet_id=spreadsheet_id,
            sheet_name=sheet_name
        )
        self.session.add(sheet)
        await self.session.commit()
        await self.session.refresh(sheet)
        return sheet

    async def get_by_faculty_and_kind(self, faculty_id: int, kind: SheetKind) -> Optional[FacultySheet]:
        result = await self.session.execute(
            select(FacultySheet)
            .where(FacultySheet.faculty_id == faculty_id)
            .where(FacultySheet.kind == kind)
        )
        return result.scalar_one_or_none()

    async def get_by_faculty(self, faculty_id: int) -> List[FacultySheet]:
        result = await self.session.execute(
            select(FacultySheet)
            .where(FacultySheet.faculty_id == faculty_id)
        )
        return list(result.scalars().all())


class InterviewerDAO(BaseDAO):
    async def create(self, faculty_id: int, faculty_sheet_id: int, tab_name: str, 
                    experience_kind: SheetKind, invite_token: str) -> Interviewer:
        interviewer = Interviewer(
            faculty_id=faculty_id,
            faculty_sheet_id=faculty_sheet_id,
            tab_name=tab_name,
            experience_kind=experience_kind,
            invite_token=invite_token
        )
        self.session.add(interviewer)
        await self.session.commit()
        await self.session.refresh(interviewer)
        return interviewer

    async def get_by_invite_token(self, invite_token: str) -> Optional[Interviewer]:
        result = await self.session.execute(
            select(Interviewer)
            .options(selectinload(Interviewer.faculty))
            .where(Interviewer.invite_token == invite_token)
        )
        return result.scalar_one_or_none()

    async def get_by_telegram_id(self, telegram_user_id: int) -> Optional[Interviewer]:
        result = await self.session.execute(
            select(Interviewer)
            .options(selectinload(Interviewer.faculty))
            .where(Interviewer.tg_id == telegram_user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_faculty(self, faculty_id: int) -> List[Interviewer]:
        result = await self.session.execute(
            select(Interviewer)
            .options(selectinload(Interviewer.faculty))
            .where(Interviewer.faculty_id == faculty_id)
        )
        return list(result.scalars().all())

    async def register_telegram_user(self, invite_token: str, telegram_user_id: int, telegram_username: Optional[str] = None) -> Optional[Interviewer]:
        await self.session.execute(
            update(Interviewer)
            .where(Interviewer.invite_token == invite_token)
            .values(tg_id=telegram_user_id, tg_username=telegram_username)
        )
        await self.session.commit()
        return await self.get_by_invite_token(invite_token)

    async def get_unregistered_by_faculty(self, faculty_id: int) -> List[Interviewer]:
        result = await self.session.execute(
            select(Interviewer)
            .options(selectinload(Interviewer.faculty))
            .where(Interviewer.faculty_id == faculty_id)
            .where(Interviewer.tg_id.is_(None))
        )
        return list(result.scalars().all())

    async def get_by_faculty_and_tab_name(self, faculty_id: int, tab_name: str) -> Optional[Interviewer]:
        result = await self.session.execute(
            select(Interviewer)
            .where(Interviewer.faculty_id == faculty_id)
            .where(Interviewer.tab_name == tab_name)
        )
        return result.scalar_one_or_none()

    async def delete(self, interviewer_id: int) -> bool:
        result = await self.session.execute(
            delete(Interviewer).where(Interviewer.id == interviewer_id)
        )
        await self.session.commit()
        return result.rowcount > 0
