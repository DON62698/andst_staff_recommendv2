import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

# streamlit 僅用來讀 secrets，沒有也不影響
try:
    import streamlit as st  # type: ignore
except Exception:
    st = None  # type: ignore

import gspread
from google.oauth2.service_account import Credentials


# ====== 設定 ======
# 你的 Sheet（可被 secrets 覆蓋）
SHEET_URL_DEFAULT = "https://docs.google.com/spreadsheets/d/1dRMaH6G1bLzv-Bt1q5wEnZPC4ZylMCE7Dzcj1KAwURE/edit?usp=sharing"

RECORDS_SHEET = "records"
TARGETS_SHEET = "targets"
# records 欄位：date(YYYY-MM-DD), week(如 32w), name, type(new|exist|line|survey), count(int)
RECORDS_HEADER = ["date", "week", "name", "type", "count"]
# targets 欄位：month(YYYY-MM), type(app|survey), target(int)
TARGETS_HEADER = ["month", "type", "target"]


# ====== 憑證 & 連線 ======
def _get_creds_dict() -> Dict[str, Any]:
    """
    讀取 Service Account JSON：
    1) st.secrets：google_service_account / gcp_service_account / service_account
       - 可是 dict 或 JSON 字串
    2) 環境變數 GOOGLE_SERVICE_ACCOUNT_JSON（JSON 字串）
    3) GOOGLE_APPLICATION_CREDENTIALS（檔案路徑）
    """
    if st is not None:
        for key in ("google_service_account", "gcp_service_account", "service_account"):
            try:
                val = st.secrets.get(key, None)  # type: ignore
            except Exception:
                val = None
            if val:
                if isinstance(val, dict):
                    return val
                if isinstance(val, str):
                    return json.loads(val)

    env_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if env_json:
        return json.loads(env_json)

    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if cred_path and os.path.exists(cred_path):
        with open(cred_path, "r", encoding="utf-8") as f:
            return json.load(f)

    raise RuntimeError("找不到 Google Service Account 憑證：請在 secrets 或環境變數提供。")


def _get_sheet_url() -> str:
    if st is not None:
        try:
            val = st.secrets.get("sheet_url", None)  # type: ignore
            if val:
                return str(val)
        except Exception:
            pass
    return os.getenv("SHEET_URL", SHEET_URL_DEFAULT)


def _get_client() -> gspread.Client:
    creds_dict = _get_creds_dict()
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)


def _open_workbook():
    client = _get_client()
    url = _get_sheet_url()
    try:
        return client.open_by_url(url)
    except Exception as e:
        try:
            return client.open_by_key(url)  # 若傳的是 key
        except Exception:
            raise RuntimeError(f"無法開啟 Google Sheet，請檢查分享權限與網址。原始錯誤：{e}")


def _ensure_worksheet(sh, name: str, header: List[str]):
    """若工作表不存在就建立；並確保第一列是 header。"""
    try:
        try:
            ws = sh.worksheet(name)
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet(title=name, rows=1000, cols=max(10, len(header)))
            ws.update("A1", [header])
            try:
                ws.freeze(rows=1)
            except Exception:
                pass

        # 確認表頭一致
        try:
            first_row = ws.row_values(1)
        except Exception:
            first_row = []
        normalized = [str(c).strip() for c in (first_row or [])]
        if normalized != header:
            end_col = chr(64 + len(header))  # 1->A, 2->B...
            ws.update(f"A1:{end_col}1", [header])
        return ws
    except Exception as e:
        raise RuntimeError(f"_ensure_worksheet('{name}') 失敗：{e}")


# ====== 公開 API（主程式會呼叫） ======
def init_db():
    sh = _open_workbook()
    _ensure_worksheet(sh, RECORDS_SHEET, RECORDS_HEADER)
    _ensure_worksheet(sh, TARGETS_SHEET, TARGETS_HEADER)


def init_target_table():
    # 舊相容：直接沿用 init_db
    init_db()


def _iso_week_str(d: datetime) -> str:
    return f"{d.isocalendar().week}w"


def insert_or_update_record(date_str: str, name: str, rtype: str, count: int) -> None:
    """
    以 (date, name, type) 做 upsert。
    type: new | exist | line | survey
    """
    if not date_str or not name or not rtype:
        raise ValueError("date, name, type 必填")
    rtype = str(rtype).lower().strip()
    if rtype not in {"new", "exist", "line", "survey"}:
        raise ValueError("type 必須為 new|exist|line|survey")
    count = int(count)

    sh = _open_workbook()
    ws = _ensure_worksheet(sh, RECORDS_SHEET, RECORDS_HEADER)

    rows = ws.get_all_records()
    target_idx: Optional[int] = None
    for idx, r in enumerate(rows, start=2):  # 資料從第 2 列開始
        if str(r.get("date")) == date_str and str(r.get("name")) == name and str(r.get("type")) == rtype:
            target_idx = idx
            break

    # 轉週字串
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        week_str = _iso_week_str(d)
    except Exception:
        week_str = ""

    values = [date_str, week_str, name, rtype, count]
    if target_idx:
        ws.update(f"A{target_idx}:E{target_idx}", [values])
    else:
        ws.append_row(values)


def load_all_records() -> List[Dict[str, Any]]:
    """回傳所有紀錄，並做基本正規化。"""
    sh = _open_workbook()
    ws = _ensure_worksheet(sh, RECORDS_SHEET, RECORDS_HEADER)
    rows = ws.get_all_records()
    out: List[Dict[str, Any]] = []
    for r in rows:
        try:
            d = str(r.get("date") or "")
            # 正規化 YYYY-MM-DD
            try:
                d_parsed = datetime.strptime(d.replace("/", "-"), "%Y-%m-%d")
                date_str = d_parsed.strftime("%Y-%m-%d")
            except Exception:
                date_str = d

            name = str(r.get("name") or "").strip()
            rtype = str(r.get("type") or "").strip().lower()
            if rtype not in {"new", "exist", "line", "survey"}:
                continue
            cnt = int(float(r.get("count") or 0))

            wk = str(r.get("week") or "")
            if not wk and date_str:
                try:
                    d2 = datetime.strptime(date_str, "%Y-%m-%d")
                    wk = _iso_week_str(d2)
                except Exception:
                    wk = ""

            out.append({"date": date_str, "week": wk, "name": name, "type": rtype, "count": cnt})
        except Exception:
            # 單列壞掉就跳過
            pass
    return out


def set_target(month: str, category: str, value: int) -> None:
    """
    設定月目標（upsert），category: app | survey
    """
    month = str(month)
    category = str(category)
    value = int(value)

    sh = _open_workbook()
    ws = _ensure_worksheet(sh, TARGETS_SHEET, TARGETS_HEADER)

    rows = ws.get_all_records()
    target_idx: Optional[int] = None
    for idx, r in enumerate(rows, start=2):
        if str(r.get("month")) == month and str(r.get("type")) == category:
            target_idx = idx
            break

    values = [month, category, value]
    if target_idx:
        ws.update(f"A{target_idx}:C{target_idx}", [values])
    else:
        ws.append_row(values)


def get_target(month: str, category: str) -> int:
    """
    取得月目標，找不到則回 0。
    """
    sh = _open_workbook()
    ws = _ensure_worksheet(sh, TARGETS_SHEET, TARGETS_HEADER)
    rows = ws.get_all_records()
    for r in rows:
        if str(r.get("month")) == month and str(r.get("type")) == category:
            try:
                return int(float(r.get("target") or 0))
            except Exception:
                return 0
    return 0
