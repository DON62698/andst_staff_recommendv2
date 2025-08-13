import os
from typing import List, Dict, Any
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

RECORDS_SHEET = "records"   # date, week, name, type, count
TARGETS_SHEET = "targets"   # month, type, target

def _get_sheet_url() -> str:
    url = st.secrets.get("GSHEET_URL", None) if hasattr(st, "secrets") else None
    if not url:
        url = os.getenv("GSHEET_URL")
    if not url:
        raise RuntimeError("GSHEET_URL not found in st.secrets or env")
    return url

def _get_credentials() -> Credentials:
    if hasattr(st, "secrets") and "gcp_service_account" in st.secrets:
        info = dict(st.secrets["gcp_service_account"])
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        return Credentials.from_service_account_info(info, scopes=scopes)
    json_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    if json_path and os.path.exists(json_path):
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        return Credentials.from_service_account_file(json_path, scopes=scopes)
    raise RuntimeError("No Google credentials found. Set st.secrets['gcp_service_account'] or GOOGLE_APPLICATION_CREDENTIALS.")

def _client() -> gspread.Client:
    return gspread.authorize(_get_credentials())

def _open_workbook():
    return _client().open_by_url(_get_sheet_url())

def _ensure_worksheet(sh: gspread.Spreadsheet, title: str, headers: List[str]) -> gspread.Worksheet:
    try:
        ws = sh.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=title, rows=2000, cols=max(10, len(headers)))
        ws.append_row(headers)
        return ws
    vals = ws.row_values(1)
    if [v.strip().lower() for v in vals] != [h.strip().lower() for h in headers]:
        ws.delete_rows(1)
        ws.insert_row(headers, index=1)
    return ws

# --------------------------------
# init
# --------------------------------
def init_db():
    sh = _open_workbook()
    _ensure_worksheet(sh, RECORDS_SHEET, ["date", "week", "name", "type", "count"])

def init_target_table():
    sh = _open_workbook()
    _ensure_worksheet(sh, TARGETS_SHEET, ["month", "type", "target"])

# --------------------------------
# load
# --------------------------------
def load_all_records() -> List[Dict[str, Any]]:
    sh = _open_workbook()
    ws = _ensure_worksheet(sh, RECORDS_SHEET, ["date", "week", "name", "type", "count"])
    rows = ws.get_all_records()
    out: List[Dict[str, Any]] = []
    for r in rows:
        dstr = str(r.get("date") or "").strip()
        nm   = (r.get("name") or "").strip()
        tp   = (r.get("type") or "").strip()
        cnt  = r.get("count")
        wk   = r.get("week")

        # date normalize
        dt = None
        for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
            try:
                dt = datetime.strptime(dstr, fmt)
                dstr = dt.strftime("%Y-%m-%d")
                break
            except Exception:
                pass
        if dt and not wk:
            wk = dt.isocalendar().week

        try:
            cnt = int(cnt)
        except Exception:
            cnt = 0

        out.append(dict(date=dstr, week=wk, name=nm, type=tp, count=cnt))
    return out

# --------------------------------
# upsert
# --------------------------------
def insert_or_update_record(date_str: str, name: str, tp: str, add_count: int):
    sh = _open_workbook()
    ws = _ensure_worksheet(sh, RECORDS_SHEET, ["date", "week", "name", "type", "count"])

    data = ws.get_all_values()
    headers = [h.strip().lower() for h in data[0]] if data else ["date", "week", "name", "type", "count"]
    col = {h: i for i, h in enumerate(headers)}  # 0-based

    target_row = None  # 1-based index for gspread
    for i in range(1, len(data)):  # skip header
        row = data[i]
        d0 = (row[col.get("date", 0)] if col.get("date") is not None and col.get("date") < len(row) else "").strip()
        n0 = (row[col.get("name", 2)] if col.get("name") is not None and col.get("name") < len(row) else "").strip()
        t0 = (row[col.get("type", 3)] if col.get("type") is not None and col.get("type") < len(row) else "").strip()
        if d0 == date_str and n0 == name and t0 == tp:
            target_row = i + 1
            break

    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        week = dt.isocalendar().week
    except Exception:
        week = ""

    if target_row:
        try:
            old_val = ws.cell(target_row, col.get("count", 4) + 1).value
            old_count = int(old_val or 0)
        except Exception:
            old_count = 0
        ws.update_cell(target_row, col.get("count", 4) + 1, int(old_count) + int(add_count))
        ws.update_cell(target_row, col.get("date", 0) + 1, date_str)
        ws.update_cell(target_row, col.get("week", 1) + 1, week)
        ws.update_cell(target_row, col.get("name", 2) + 1, name)
        ws.update_cell(target_row, col.get("type", 3) + 1, tp)
    else:
        ws.append_row([date_str, week, name, tp, int(add_count)])

# --------------------------------
# delete  ✅ 這就是 data_management 要用的函式
# --------------------------------
def delete_record(date_str: str, name: str, category: str) -> bool:
    """
    刪除第一筆符合 (date, name, type) 的列；回傳 True=刪除成功 / False=找不到。
    category: 'new'|'exist'|'line'|'survey'
    """
    sh = _open_workbook()
    ws = _ensure_worksheet(sh, RECORDS_SHEET, ["date", "week", "name", "type", "count"])

    data = ws.get_all_values()
    if not data:
        return False

    headers = [h.strip().lower() for h in data[0]]
    col = {h: i for i, h in enumerate(headers)}

    def _val(row, key):
        idx = col.get(key)
        return (row[idx].strip() if idx is not None and idx < len(row) else "")

    for idx, row in enumerate(data[1:], start=2):  # from row 2 (1-based)
        d = _val(row, "date"); n = _val(row, "name"); t = _val(row, "type")
        if d == date_str and n == name and t == category:
            ws.delete_rows(idx)
            return True
    return False

# --------------------------------
# targets
# --------------------------------
def get_target(month_ym: str, tp: str) -> int:
    sh = _open_workbook()
    ws = _ensure_worksheet(sh, TARGETS_SHEET, ["month", "type", "target"])
    rows = ws.get_all_records()
    for r in rows:
        m = str(r.get("month") or "").strip()
        t = str(r.get("type") or "").strip()
        if m == month_ym and t == tp:
            try:
                return int(r.get("target") or 0)
            except Exception:
                return 0
    return 0

def set_target(month_ym: str, tp: str, target_val: int):
    sh = _open_workbook()
    ws = _ensure_worksheet(sh, TARGETS_SHEET, ["month", "type", "target"])

    data = ws.get_all_values()
    headers = [h.strip().lower() for h in data[0]] if data else ["month", "type", "target"]
    col = {h: i for i, h in enumerate(headers)}

    target_row = None
    for i in range(1, len(data)):
        row = data[i]
        m0 = (row[col.get("month", 0)] if col.get("month") is not None and col.get("month") < len(row) else "").strip()
        t0 = (row[col.get("type", 1)]  if col.get("type")  is not None and col.get("type")  < len(row) else "").strip()
        if m0 == month_ym and t0 == tp:
            target_row = i + 1
            break

    if target_row:
        ws.update_cell(target_row, col.get("target", 2) + 1, int(target_val))
        ws.update_cell(target_row, col.get("month", 0) + 1, month_ym)
        ws.update_cell(target_row, col.get("type", 1) + 1, tp)
    else:
        ws.append_row([month_ym, tp, int(target_val)])


