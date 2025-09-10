from typing import Dict, List, Optional


class AppState:
    def __init__(self) -> None:
        self.faculty_sheets: Dict[str, Dict[str, str]] = {}
        self.participants: Dict[str, List[dict]] = {}
        self.invites: Dict[str, dict] = {}
        self.bot_username: Optional[str] = None
        # user_id -> {"type": str, "ctx": dict}
        self.pending: Dict[int, dict] = {}


