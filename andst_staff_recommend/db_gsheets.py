import os
from typing import List, Dict, Any, Optional
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ===== 設定 =====
RECORDS_SHEET = "records"   # 欄位: date, week, name, type, count
TARGETS_SHEET = "targets"   # 欄位: month, type, target

# 允許從 st.secrets 或環境變數讀取設定
def _get_sheet_url() -> str:
    # 你可以在 .streamlit/secrets.toml 放 GSHEET_URL
    # 或者使用環境變數 GSHEET_URL
    url = st.secrets.get("GSHEET_URL", None) if hasattr(st, "secrets") else None
    if not url:
        url = os.getenv("GSHEET_URL")
    if not url:
        raise RuntimeError("GSHEET_URL not found in st.secrets or env")
    return url

def _get_credentials() -> Credentials:
    # 建議在 st.secrets 放 GCP 的 service_account 內容
    if hasattr(st, "secrets") and "gcp_service_account" in st.secrets:
        info = dict(st.secrets["gcp_service_account"])
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        return Credentials.from_service_account_info(info, scopes=scopes)
    # 退而求其次：用 JSON 路徑
    json_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    if json_path and os.path.exists(json_path):
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        return Credentials.from_service_account_file(json_path, scopes=scopes)
    raise RuntimeError("No Google credentials found. Set st.secrets['gcp_service_account'] or GOOGLE_APPLICATION_CREDENTIALS.")

def _client() -> gspread.Client:
    creds = _get_credentials()
    return gspread.authorize(creds)

def _open_workbook():
    url = _get_sheet_url()
    client = _client()
    return client.open_by_url(url)

def _ensure_worksheet(sh: gspread.Spreadsheet, title: str, headers: List[str]) -> gspread.Worksheet:
    try:
        ws = sh.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=title, rows=1000, cols=max(10, len(headers)))
        ws.append_row(headers)
        return ws

    # 確認標題列
    vals = ws.row_values(1)
    if [v.strip().lower() for v in vals] != [h.strip().lower() for h in headers]:
        # 重新設定第 1 列為正確 headers（保留舊資料）
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
    sh = _open_workbook()
    ws = _ensure_worksheet(sh, RECORDS_SHEET, ["date", "week", "name", "type", "count"])
    rows = ws.get_all_records()
    # 正規化：補 week 欄位（以 ISO 週為準）
    out = []
    for r in rows:
        dstr = str(r.get("date") or "").strip()
        nm   = (r.get("name") or "").strip()
        tp   = (r.get("type") or "").strip()
        cnt  = r.get("count")
        wk   = r.get("week")

        # 日期轉換 & 週
        try:
            dt = datetime.strptime(dstr, "%Y-%m-%d")
        except Exception:
            # 允許 2025/08/12 這種
            try:
                dt = datetime.strptime(dstr, "%Y/%m/%d")
                dstr = dt.strftime("%Y-%m-%d")
            except Exception:
                dt = None
        if dt and not wk:
            wk = dt.isocalendar().week

        # 數值
        try:
            cnt = int(cnt)
        except Exception:
            cnt = 0

        out.append(dict(date=dstr, week=wk, name=nm, type=tp, count=cnt))
    return out

# ===== 新增/更新（upsert） =====
def insert_or_update_record(date_str: str, name: str, tp: str, add_count: int):
    """
    若同 (date, name, type) 已存在，將 count += add_count；
    否則新增一列。
    """
    sh = _open_workbook()
    ws = _ensure_worksheet(sh, RECORDS_SHEET, ["date", "week", "name", "type", "count"])

    # 讀整張表來找是否有同鍵
    data = ws.get_all_values()
    headers = [h.strip().lower() for h in data[0]] if data else ["date", "week", "name", "type", "count"]
    col_map = {h: i for i, h in enumerate(headers)}  # 0-based

    # 嘗試尋找既有列
    target_row_idx = None  # 1-based for gspread
    for i in range(1, len(data)):  # 跳過 header
        row = data[i]
        d0  = (row[col_map.get("date", 0)] if col_map.get("date") is not None and col_map.get("date") < len(row) else "").strip()
        n0  = (row[col_map.get("name", 2)] if col_map.get("name") is not None and col_map.get("name") < len(row) else "").strip()
        t0  = (row[col_map.get("type", 3)] if col_map.get("type") is not None and col_map.get("type") < len(row) else "").strip()
        if d0 == date_str and n0 == name and t0 == tp:
            target_row_idx = i + 1  # gspread 是 1-based
            break

    # 計算 week
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        dt = None
    week = dt.isocalendar().week if dt else ""

    if target_row_idx:
        # 更新：原 count + add_count
        try:
            old_count_cell = ws.cell(target_row_idx, col_map.get("count", 5) + 1).value
            old_count = int(old_count_cell or 0)
        except Exception:
            old_count = 0
        new_count = int(old_count) + int(add_count)
        ws.update_cell(target_row_idx, col_map.get("count", 5) + 1, new_count)
        # 同時把 week/date/name/type 正規化回寫一次（以免有舊格式）
        ws.update_cell(target_row_idx, col_map.get("week", 2) + 1, week)
        ws.update_cell(target_row_idx, col_map.get("date", 1) + 1, date_str)
        ws.update_cell(target_row_idx, col_map.get("name", 3) + 1, name)
        ws.update_cell(target_row_idx, col_map.get("type", 4) + 1, tp)
    else:
        # 新增
        ws.append_row([date_str, week, name, tp, int(add_count)])

# ===== 目標值 =====
def get_target(month_ym: str, tp: str) -> int:
    """
    month_ym: 'YYYY-MM'
    tp: 'app' 或 'survey'
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
        t0 = (row[col_map.get("type", 1)] if col_map.get("type") is not None and col_map.get("type") < len(row) else "").strip()
        if m0 == month_ym and t0 == tp:
            target_row_idx = i + 1
            break

    if target_row_idx:
        ws.update_cell(target_row_idx, col_map.get("target", 2) + 1, int(target_val))
        # 正規化回寫（避免大小寫或多餘空白）
        ws.update_cell(target_row_idx, col_map.get("month", 0) + 1, month_ym)
        ws.update_cell(target_row_idx, col_map.get("type", 1) + 1, tp)
    else:
        ws.append_row([month_ym, tp, int(target_val)])



