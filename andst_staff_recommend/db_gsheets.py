import os
from typing import List, Dict, Any
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ===== 工作表名稱 =====
RECORDS_SHEET = "records"   # 欄位: date, week, name, type, count
TARGETS_SHEET = "targets"   # 欄位: month, type, target

# ===== 讀取設定 =====
def _get_sheet_url() -> str:
    # 優先 st.secrets，其次環境變數
    url = st.secrets.get("GSHEET_URL", None) if hasattr(st, "secrets") else None
    if not url:
        url = os.getenv("GSHEET_URL")
    if not url:
        raise RuntimeError("GSHEET_URL not found in st.secrets or env")
    return url

def _get_credentials() -> Credentials:
    # 建議把整份 service account JSON 放在 st.secrets["gcp_service_account"]
    if hasattr(st, "secrets") and "gcp_service_account" in st.secrets:
        info = dict(st.secrets["gcp_service_account"])
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        return Credentials.from_service_account_info(info, scopes=scopes)

    # 備用：環境變數指向 JSON 路徑
    json_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    if json_path and os.path.exists(json_path):
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        return Credentials.from_service_account_file(json_path, scopes=scopes)

    raise RuntimeError(
        "No Google credentials found. "
        "Set st.secrets['gcp_service_account'] or GOOGLE_APPLICATION_CREDENTIALS."
    )

def _client() -> gspread.Client:
    creds = _get_credentials()
    return gspread.authorize(creds)

def _open_workbook():
    url = _get_sheet_url()
    client = _client()
    return client.open_by_url(url)

def _ensure_worksheet(sh: gspread.Spreadsheet, title: str, headers: List[str]) -> gspread.Worksheet:
    """確保工作表存在，若不存在就建立；並保證第 1 列為 headers（保留舊資料）。"""
    try:
        ws = sh.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=title, rows=2000, cols=max(10, len(headers)))
        ws.append_row(headers)
        return ws

    # 確認標題列
    vals = ws.row_values(1)
    if [v.strip().lower() for v in vals] != [h.strip().lower() for h in headers]:
        # 重設第 1 列（保留內容）
        ws.delete_rows(1)
        ws.insert_row(headers, index=1)
    return ws

# ===== 初始化 =====
def init_db():
    sh = _open_workbook()
    _ensure_worksheet(sh, RECORDS_SHEET, ["date", "week", "name", "type", "count"])

def init_target_table():
    sh = _open_workbook()
    _ensure_worksheet(sh, TARGETS_SHEET, ["month", "type", "target"])

# ===== 讀資料 =====
def load_all_records() -> List[Dict[str, Any]]:
    """讀取所有 records，並正規化欄位型別。"""
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

        # 日期解析（允許 2025-08-12 / 2025/08/12）
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

# ===== 新增/更新（upsert） =====
def insert_or_update_record(date_str: str, name: str, tp: str, add_count: int):
    """
    若存在同 (date, name, type)，將 count += add_count；否則 append 新列。
    """
    sh = _open_workbook()
    ws = _ensure_worksheet(sh, RECORDS_SHEET, ["date", "week", "name", "type", "count"])

    data = ws.get_all_values()
    headers = [h.strip().lower() for h in data[0]] if data else ["date", "week", "name", "type", "count"]
    col_map = {h: i for i, h in enumerate(headers)}  # 0-based index

    # 找到既有列
    target_row_idx = None  # gspread 1-based
    for i in range(1, len(data)):  # 跳過第 1 列標題
        row = data[i]
        d0 = (row[col_map.get("date", 0)] if col_map.get("date") is not None and col_map.get("date") < len(row) else "").strip()
        n0 = (row[col_map.get("name", 2)] if col_map.get("name") is not None and col_map.get("name") < len(row) else "").strip()
        t0 = (row[col_map.get("type", 3)] if col_map.get("type") is not None and col_map.get("type") < len(row) else "").strip()
        if d0 == date_str and n0 == name and t0 == tp:
            target_row_idx = i + 1
            break

    # 計算週
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        week = dt.isocalendar().week
    except Exception:
        week = ""

    if target_row_idx:
        # 更新 count
        try:
            old_count_cell = ws.cell(target_row_idx, col_map.get("count", 4) + 1).value
            old_count = int(old_count_cell or 0)
        except Exception:
            old_count = 0
        new_count = int(old_count) + int(add_count)
        ws.update_cell(target_row_idx, col_map.get("count", 4) + 1, new_count)
        # 同步規格化欄位
        ws.update_cell(target_row_idx, col_map.get("date", 0) + 1, date_str)
        ws.update_cell(target_row_idx, col_map.get("week", 1) + 1, week)
        ws.update_cell(target_row_idx, col_map.get("name", 2) + 1, name)
        ws.update_cell(target_row_idx, col_map.get("type", 3) + 1, tp)
    else:
        # 新增
        ws.append_row([date_str, week, name, tp, int(add_count)])

# ===== 刪除 =====
def delete_record(date_str: str, name: str, category: str) -> bool:
    """
    刪除第一筆符合 (date, name, type) 的列；回傳 True=刪除成功 / False=找不到。
    category 必須是 'new'|'exist'|'line'|'survey'
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

    for idx, row in enumerate(data[1:], start=2):  # 從第2列（資料）開始
        d = _val(row, "date")
        n = _val(row, "name")
        t = _val(row, "type")
        if d == date_str and n == name and t == category:
            ws.delete_rows(idx)
            return True
    return False

# ===== 目標值 =====
def get_target(month_ym: str, tp: str) -> int:
    """
    取得目標值；month_ym: 'YYYY-MM'；tp: 'app'|'survey'
    """
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
    """設定/更新目標值；若 (month,type) 存在則覆寫，不存在則新增。"""
    sh = _open_workbook()
    ws = _ensure_worksheet(sh, TARGETS_SHEET, ["month", "type", "target"])

    data = ws.get_all_values()
    headers = [h.strip().lower() for h in data[0]] if data else ["month", "type", "target"]
    col_map = {h: i for i, h in enumerate(headers)}

    # 尋找是否已存在 (month, type)
    target_row_idx = None
    for i in range(1, len(data)):
        row = data[i]
        m0 = (row[col_map.get("month", 0)] if col_map.get("month") is not None and col_map.get("month") < len(row) else "").strip()
        t0 = (row[col_map.get("type", 1)]  if col_map.get("type") is not None  and col_map.get("type")  < len(row) else "").strip()
        if m0 == month_ym and t0 == tp:
            target_row_idx = i + 1
            break

    if target_row_idx:
        ws.update_cell(target_row_idx, col_map.get("target", 2) + 1, int(target_val))
        ws.update_cell(target_row_idx, col_map.get("month", 0) + 1, month_ym)
        ws.update_cell(target_row_idx, col_map.get("type", 1) + 1, tp)
    else:
        ws.append_row([month_ym, tp, int(target_val)])



