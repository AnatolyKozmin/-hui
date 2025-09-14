import os
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv()


class AuthService:
    @staticmethod
    def is_superadmin(user_id: int) -> bool:
        """Check if user is superadmin"""
        raw = os.getenv("SUPERADMIN_IDS", "")
        if not raw:
            return False
        try:
            ids = {int(x.strip()) for x in raw.split(",") if x.strip()}
        except ValueError:
            ids = set()
        return user_id in ids

    @staticmethod
    def get_superadmin_ids() -> List[int]:
        """Get list of superadmin IDs"""
        raw = os.getenv("SUPERADMIN_IDS", "")
        if not raw:
            return []
        try:
            return [int(x.strip()) for x in raw.split(",") if x.strip()]
        except ValueError:
            return []

    @staticmethod
    async def is_faculty_admin(user_id: int, faculty_id: Optional[int] = None) -> bool:
        """Check if user is admin of specific faculty or any faculty"""
        # TODO: Implement when DB is ready
        # For now, return False - only superadmins have access
        return False

    @staticmethod
    async def get_user_faculties(user_id: int) -> List[int]:
        """Get list of faculty IDs where user is admin"""
        # TODO: Implement when DB is ready
        return []
