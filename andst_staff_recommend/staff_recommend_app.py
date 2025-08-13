import streamlit as st
import pandas as pd
from datetime import date
import matplotlib.pyplot as plt

# --- 強制載入專案內的日文字型（避免標題/括號/年 亂碼） ---
import os
from matplotlib import font_manager, rcParams

JP_FONT_READY = False
try:
    # 依你的專案結構放置字型：andst_staff_recommend/fonts/NotoSansJP-Regular.otf
    font_path = os.path.join(os.path.dirname(__file__), "fonts", "NotoSansJP-Regular.otf")
    font_manager.fontManager.addfont(font_path)
    _prop = font_manager.FontProperties(fname=font_path)
    rcParams["font.family"] = _prop.get_name()
    JP_FONT_READY = True
except Exception:
    JP_FONT_READY = False  # 找不到字型檔就維持 False，再 fallback 到英文標題

# 若專案沒放字型，再嘗試系統已裝字型（雲端環境常常沒有）
if not JP_FONT_READY:
    _JP_FONT_CANDIDATES = [
        "Noto Sans CJK JP", "Noto Sans JP", "IPAGothic", "IPAexGothic",
        "TakaoGothic", "Yu Gothic", "Hiragino Sans", "Meiryo", "MS Gothic",
        "PingFang TC", "PingFang SC", "Heiti TC", "Heiti SC"
    ]
    available = {f.name for f in font_manager.fontManager.ttflist}
    for _name in _JP_FONT_CANDIDATES:
        if _name in available:
            rcParams["font.family"] = _name
            JP_FONT_READY = True
            break

rcParams["axes.unicode_minus"] = False  # 避免負號亂碼

# ✅ Google Sheets 後端
from db_gsheets import (
    init_db,
    init_target_table,
    load_all_records,
    insert_or_update_record,
    get_target,
    set_target,
)

# ✅ 資料管理頁
from data_management import show_data_management


# -----------------------------
# Cache / 初始化（避免每次互動都狂打 API）
# -----------------------------
@st.cache_resource
def _init_once():
    """只在第一次執行時做表單初始化與檢查。"""
    init_db()
    init_target_table()
    return True


@st.cache_data(ttl=60)
def load_all_records_cached():
    """快取 60 秒，降低 API 次數。"""
    return load_all_records()


@st.cache_data(ttl=60)
def get_target_safe(month: str, category: str) -> int:
    """讀取目標值（失敗回 0，不讓整個 app 掛掉）。"""
    try:
        return get_target(month, category)
    except Exception:
        return 0


# -----------------------------
# 共用工具
# -----------------------------
def ymd(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def current_year_month() -> str:
    return date.today().strftime("%Y-%m")


def ensure_dataframe(records) -> pd.DataFrame:
    df = pd.DataFrame(records or [])
    for col in ["date", "name", "type", "count"]:
        if col not in df.columns:
            df[col] = None
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["count"] = pd.to_numeric(df["count"], errors="coerce").fillna(0).astype(int)
    return df


def month_filter(df: pd.DataFrame, ym: str) -> pd.DataFrame:
    if "date" not in df.columns:
        return df.iloc[0:0]
    return df[(df["date"].dt.strftime("%Y-%m") == ym)]


def names_from_records(records) -> list[str]:
    """從歷史紀錄萃取名字（持久、跨重啟仍在）。"""
    return sorted({(r.get("name") or "").strip() for r in (records or []) if r.get("name")})


# ---- 年份 / 週處理 ----
def year_options(df: pd.DataFrame) -> list[int]:
    if "date" not in df.columns or df["date"].isna().all():
        return [date.today().year]
    years = sorted(set(df["date"].dropna().dt.year.astype(int).tolist()))
    if not years:
        years = [date.today().year]
    return years

def _week_num_to_label(w: int) -> str:
    """把 ISO 週轉為顯示標籤（最多 w52；53 映成 w1）。"""
    w = int(w)
    w_display = ((w - 1) % 52) + 1
    return f"w{w_display}"

def _labels_for_weeks(weeks: list[int]) -> list[str]:
    return sorted({ _week_num_to_label(w) for w in weeks }, key=lambda s: int(s[1:]))

def _actual_weeks_for_label(df_year: pd.DataFrame, label: str) -> list[int]:
    """在指定年份內，把顯示標籤（例如 w1）對應回實際可能的 ISO 週集合（例如 {1,53}）。"""
    if "date" not in df_year.columns or df_year.empty:
        return []
    iso_weeks = sorted(set(df_year["date"].dt.isocalendar().week.astype(int).tolist()))
    want = int(label.lower().lstrip("w"))
    return [w for w in iso_weeks if int(_week_num_to_label(w)[1:]) == want]

# ---- 期間選項 / 過濾 ----
def _period_options(df: pd.DataFrame, mode: str, selected_year: int):
    """
    取得週/月/年的選項與預設值（依 selected_year 限定）。
    週：回傳 w1..w52（以該年實際有資料的週為準，w53 顯示為 w1）
    月：只回傳該年的 YYYY-MM
    年：回傳所有年
    """
    if "date" not in df.columns or df["date"].isna().all():
        today = date.today()
        if mode == "週（単週）":
            return [f"w{today.isocalendar().week if today.isocalendar().week <= 52 else 1}"], f"w{today.isocalendar().week if today.isocalendar().week <= 52 else 1}"
        elif mode == "月（単月）":
            dft = today.strftime("%Y-%m")
            return [dft], dft
        else:
            return [today.year], today.year

    dfx = df.dropna(subset=["date"]).copy()
    if mode == "週（単週）":
        dyear = dfx[dfx["date"].dt.year == int(selected_year)]
        weeks = sorted(set(dyear["date"].dt.isocalendar().week.astype(int).tolist()))
        labels = _labels_for_weeks(weeks) or ["w1"]
        today_w = date.today().isocalendar().week
        default = f"w{today_w if today_w <= 52 else 1}"
        if default not in labels:
            default = labels[0]
        return labels, default

    elif mode == "月（単月）":
        dyear = dfx[dfx["date"].dt.year == int(selected_year)]
        months = sorted
