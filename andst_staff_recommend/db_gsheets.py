# db_gsheets.py
import os
from typing import List, Dict, Any, Optional
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date

RECORDS_SHEET = "records"   # 欄位: date, week, name, type, count
TARGETS_SHEET = "targets"   # 欄位: month, type, target

# -----------------------
# 基礎：取得 URL 與憑證
# -----------------------
def _get_sheet_url() -> str:
    url = getattr(st, "secrets", {}).get("GSHEET_URL") if hasattr(st, "secrets") else None
    if not url:
        url = os.environ.get("GSHEET_URL")
    if not url:
        raise RuntimeError("GSHEET_URL 未設定（請在 secrets 或環境變數設定）")
    return url

def _get_credentials() -> Credentials:
    if hasattr(st, "secrets") and "gcp_service_account" in st.secrets:
        info = dict(st.secrets["gcp_service_account"])
        return Credentials.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"]
        )
    # 也支援從環境變數載入整段 JSON
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if raw:
        import json
        info = json.loads(raw)
        return Credentials.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"]
        )
    raise RuntimeError("找不到 service account 憑證（secrets['gcp_service_account'] 或 GOOGLE_SERVICE_ACCOUNT_JSON）")

def _client() -> gspread.Client:
    creds = _get_credentials()
    return gspread.authorize(creds)

def _open_workbook():
    client = _client()
    return client.open_by_url(_get_sheet_url())

def _ensure_worksheet(sh: gspread.Spreadsheet, title: str, headers: List[str]) -> gspread.Worksheet:
    try:
        ws = sh.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=title, rows=1000, cols=max(10, len(headers)))
        ws.append_row(headers)
        return ws

    # 若第一列不是預期標頭，則補齊（不覆蓋既有資料）
    first_row = ws.row_values(1)
    if first_row != headers:
        # 只在空表或標頭明顯不同時修正
        if len(ws.col_values(1)) <= 1 and len(ws.row_values(2)) == 0:
            ws.clear()
            ws.append_row(headers)
        else:
            # 補上缺的欄位（尾端）
            if len(first_row) < len(headers):
                for i, h in enumerate(headers, start=1):
                    if i > len(first_row):
                        ws.update_cell(1, i, h)
    return ws

# -----------------------
# 初始化
# -----------------------
def init_db():
    sh = _open_workbook()
    _ensure_worksheet(sh, RECORDS_SHEET, ["date", "week", "name", "type", "count"])
    _ensure_worksheet(sh, TARGETS_SHEET, ["month", "type", "target"])
    return sh

def init_target_table():
    # 兼容舊呼叫；實際工作在 init_db 完成
    init_db()

# -----------------------
# 工具
# -----------------------
def _week_label_from_ymd(ymd: str) -> str:
    # week 以 ISO 週為準（和你前端一致：顯示 w1..w53）
    dt = datetime.strptime(ymd, "%Y-%m-%d").date()
    w = dt.isocalendar().week
    # 以實際顯示週數（跨年 53 -> w1）
    w_display = ((w - 1) % 52) + 1
    return f"w{w_display}"

def _read_all(ws: gspread.Worksheet) -> List[Dict[str, Any]]:
    rows = ws.get_all_records(expected_headers=["date", "week", "name", "type", "count"])
    # 正規化
    out: List[Dict[str, Any]] = []
    for r in rows:
        if not r.get("date") or not r.get("name") or not r.get("type"):
            continue
        try:
            c = int(r.get("count", 0))
        except Exception:
            c = 0
        out.append({
            "date": r["date"],
            "week": r.get("week") or _week_label_from_ymd(r["date"]),
            "name": str(r["name"]).strip(),
            "type": str(r["type"]).strip(),
            "count": c,
        })
    return out

# -----------------------
# 讀/寫 records
# -----------------------
def load_all_records() -> List[Dict[str, Any]]:
    sh = init_db()
    ws = sh.worksheet(RECORDS_SHEET)
    return _read_all(ws)

def insert_or_update_record(date_str: str, name: str, type_str: str, count: int) -> bool:
    """若 (date, name, type) 存在則更新 count；否則新增一列。"""
    sh = init_db()
    ws = sh.worksheet(RECORDS_SHEET)
    headers = ws.row_values(1)
    records = ws.get_all_values()
    # 建立索引：欄位位置
    col_idx = {h: i for i, h in enumerate(headers, start=1)}
    if not {"date", "name", "type", "count"}.issubset(col_idx.keys()):
        raise RuntimeError("records 標頭不完整，請確定有 date, name, type, count")

    # 尋找是否已有同一筆
    target_row = None
    for i in range(2, len(records) + 1):
        row = ws.row_values(i)
        # 取值時注意越界
        def _v(key):
            j = col_idx[key]
            return row[j-1] if j-1 < len(row) else ""
        if _v("date") == date_str and _v("name") == name and _v("type") == type_str:
            target_row = i
            break

    w = _week_label_from_ymd(date_str)
    if target_row:
        ws.update_cell(target_row, col_idx["count"], int(count))
        if "week" in col_idx:
            ws.update_cell(target_row, col_idx["week"], w)
    else:
        values = ["", "", "", "", ""]
        values[col_idx["date"]-1] = date_str
        if "week" in col_idx:
            values[col_idx["week"]-1] = w
        values[col_idx["name"]-1] = name
        values[col_idx["type"]-1] = type_str
        values[col_idx["count"]-1] = int(count)
        ws.append_row(values)
    return True

def delete_record(date_str: str, name: str, type_str: str) -> bool:
    """刪除第一筆符合 (date, name, type) 的資料。"""
    sh = init_db()
    ws = sh.worksheet(RECORDS_SHEET)
    headers = ws.row_values(1)
    col_idx = {h: i for i, h in enumerate(headers, start=1)}
    last_row = len(ws.get_all_values())
    for i in range(2, last_row + 1):
        row = ws.row_values(i)
        def _v(key):
            j = col_idx.get(key, 0)
            return row[j-1] if j and j-1 < len(row) else ""
        if _v("date") == date_str and _v("name") == name and _v("type") == type_str:
            ws.delete_rows(i)
            return True
    return False

# -----------------------
# 目標值 targets
# -----------------------
def get_target(month_str: str, type_str: str) -> int:
    """讀取某個月份 & 類型的目標值，沒有則回傳 0。month 例如 '2025-08'"""
    sh = init_db()
    ws = sh.worksheet(TARGETS_SHEET)
    rows = ws.get_all_records(expected_headers=["month", "type", "target"])
    for r in rows:
        if str(r.get("month")) == month_str and str(r.get("type")) == type_str:
            try:
                return int(r.get("target", 0))
            except Exception:
                return 0
    return 0

def set_target(month_str: str, type_str: str, target: int) -> bool:
    """設定（upsert）某月某類型的目標值。"""
    sh = init_db()
    ws = sh.worksheet(TARGETS_SHEET)
    headers = ws.row_values(1)
    col_idx = {h: i for i, h in enumerate(headers, start=1)}
    rows = ws.get_all_values()
    # 先找舊的
    for i in range(2, len(rows) + 1):
        row = ws.row_values(i)
        def _v(key):
            j = col_idx.get(key, 0)
            return row[j-1] if j and j-1 < len(row) else ""
        if _v("month") == month_str and _v("type") == type_str:
            ws.update_cell(i, col_idx["target"], int(target))
            return True
    # 沒有就新增
    values = ["", "", ""]
    values[col_idx["month"]-1] = month_str
    values[col_idx["type"]-1] = type_str
    values[col_idx["target"]-1] = int(target)
    ws.append_row(values)
    return True

