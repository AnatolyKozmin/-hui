import os
from typing import List, Dict

import gspread
from google.oauth2.service_account import Credentials


class GSpreadClient:
    def __init__(self) -> None:
        creds_path = os.getenv("GOOGLE_CREDENTIALS_JSON")
        if not creds_path:
            raise RuntimeError("Set GOOGLE_CREDENTIALS_JSON to path of service account JSON")
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
        ]
        credentials = Credentials.from_service_account_file(creds_path, scopes=scopes)
        self._client = gspread.authorize(credentials)

    def list_worksheet_titles(self, spreadsheet_id: str) -> List[str]:
        sh = self._client.open_by_key(spreadsheet_id)
        return [ws.title for ws in sh.worksheets()]

    def read_participants(self, spreadsheet_id: str, worksheet_title: str = "участники") -> List[Dict]:
        sh = self._client.open_by_key(spreadsheet_id)
        ws = sh.worksheet(worksheet_title)
        rows = ws.get_all_records()  # assumes first row is headers
        # Normalize keys to expected Russian headers -> fields
        normalized = []
        for r in rows:
            norm = {
                "vk_id": r.get("vk_id") or r.get("VK_ID") or r.get("vk") or r.get("vk id"),
                "first_name": r.get("first_name") or r.get("Имя") or r.get("name"),
                "last_name": r.get("last_name") or r.get("Фамилия") or r.get("surname"),
            }
            if norm["vk_id"] is None:
                continue
            normalized.append(norm)
        return normalized


