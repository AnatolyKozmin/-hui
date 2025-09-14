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

    def get_interviewer_sheets(self, spreadsheet_id: str) -> List[str]:
        """Получает список листов с собеседующими (ne_opyt и opyt)"""
        sh = self._client.open_by_key(spreadsheet_id)
        worksheets = sh.worksheets()
        
        interviewer_sheets = []
        for ws in worksheets:
            title = ws.title.lower()
            if "ne_opyt" in title or "opyt" in title:
                interviewer_sheets.append(ws.title)
        
        return interviewer_sheets

    def read_interviewers_from_sheet(self, spreadsheet_id: str, sheet_name: str) -> List[Dict]:
        """Читает собеседующих из конкретного листа"""
        sh = self._client.open_by_key(spreadsheet_id)
        ws = sh.worksheet(sheet_name)
        rows = ws.get_all_records()
        
        interviewers = []
        for r in rows:
            # Ищем имя собеседующего в различных возможных колонках
            name = (r.get("name") or r.get("Имя") or r.get("ФИО") or 
                   r.get("interviewer") or r.get("собеседующий") or
                   r.get("проверяющий") or r.get("экзаменатор"))
            
            if name and name.strip():
                interviewers.append({
                    "name": name.strip(),
                    "sheet_name": sheet_name
                })
        
        return interviewers
    
    async def test_connection(self) -> bool:
        """Тестирует подключение к Google Sheets API"""
        try:
            # Пытаемся получить список таблиц пользователя
            spreadsheets = self._client.list_spreadsheet_files()
            return True
        except Exception as e:
            print(f"❌ Ошибка тестирования подключения к Google Sheets: {e}")
            return False


