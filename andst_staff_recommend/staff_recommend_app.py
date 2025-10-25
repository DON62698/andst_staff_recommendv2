# -*- coding: utf-8 -*-
import os
from datetime import date
import uuid
import calendar

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib import font_manager, rcParams

# -----------------------------
# Page config
# -----------------------------
try:
    st.set_page_config(page_title="and st 統計 Team Men's", layout="centered")
except Exception:
    pass

st.title("and st Men's")

# -----------------------------
# Font setting (防止亂碼)
# -----------------------------
JP_FONT_READY = False
try:
    try_candidates = [
        os.path.join(os.path.dirname(__file__), "fonts", "NotoSansJP-Regular.otf"),
        os.path.join(os.path.dirname(__file__), "NotoSansJP-Regular.otf"),
        "/mnt/data/NotoSansJP-Regular.otf",
    ]
    for fp in try_candidates:
        if os.path.exists(fp):
            font_manager.fontManager.addfont(fp)
            _prop = font_manager.FontProperties(fname=fp)
            rcParams["font.family"] = _prop.get_name()
            JP_FONT_READY = True
            break
    if not JP_FONT_READY:
        _JP_FONT_CANDIDATES = [
            "Noto Sans JP", "IPAGothic", "Yu Gothic", "Hiragino Sans", "Meiryo"
        ]
        available = {f.name for f in font_manager.fontManager.ttflist}
        for _name in _JP_FONT_CANDIDATES:
            if _name in available:
                rcParams["font.family"] = _name
                JP_FONT_READY = True
                break
except Exception:
    JP_FONT_READY = False

rcParams["axes.unicode_minus"] = False

# -----------------------------
# Backend imports
# -----------------------------
from db_gsheets import (
    init_db,
    init_target_table,
    load_all_records,
    insert_or_update_record,
    get_target,
    set_target,
)
from data_management import show_data_management

# -----------------------------
# Cache / Init
# -----------------------------
@st.cache_resource
def _init_once():
    init_db()
    init_target_table()
    return True

@st.cache_data(ttl=60)
def load_all_records_cached():
    return load_all_records()

# -----------------------------
# Utils
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

def names_from_records(records) -> list:
    return sorted({(r.get("name") or "").strip() for r in (records or []) if r.get("name")})

def year_options(df: pd.DataFrame) -> list:
    if "date" not in df.columns or df["date"].isna().all():
        return [date.today().year]
    years = sorted(set(df["date"].dropna().dt.year.astype(int).tolist()))
    return years or [date.today().year]

def _week_label(week_number: int) -> str:
    return f"w{int(week_number)}"

# -----------------------------
# 修正版 _filter_by_period（修正你遇到的語法錯誤）
# -----------------------------
def _filter_by_period(df: pd.DataFrame, mode: str, value, selected_year: int) -> pd.DataFrame:
    """根據選擇的期間（週 / 月 / 年）過濾資料"""
    if "date" not in df.columns or df["date"].isna().all():
        return df.iloc[0:0]

    dfx = df.dropna(subset=["date"]).copy()

    if mode == "週（単週）":
        dyear = dfx[dfx["date"].dt.year == int(selected_year)]
        try:
            want = int(str(value).lower().lstrip("w"))
        except Exception:
            return dyear.iloc[0:0]
        return dyear[dyear["date"].dt.isocalendar().week.astype(int).isin([want])]

    elif mode == "月（単月）":
        dyear = dfx[dfx["date"].dt.year == int(selected_year)]
        return dyear[dyear["date"].dt.strftime("%Y-%m") == str(value)]

    else:
        return dfx[dfx["date"].dt.year == int(selected_year)]

# -----------------------------
# Session
# -----------------------------
def init_session():
    if "data" not in st.session_state:
        st.session_state.data = load_all_records_cached()
    if "names" not in st.session_state:
        st.session_state.names = names_from_records(st.session_state.data)

_init_once()
init_session()

# -----------------------------
# Progress bar（保留函式，供註冊頁使用）
# -----------------------------
def render_rate_block(category, label, current_total, target, ym):
    pct = 0 if target <= 0 else min(100.0, round(current_total * 100.0 / max(1, target), 1))
    bar_id = f"meter_{category}_{uuid.uuid4().hex[:6]}"
    st.markdown(
        f"""
<div style="font-size:14px;opacity:.85;">
  {ym} の累計：<b>{current_total}</b> 件 ／ 目標：<b>{target}</b> 件
</div>
<div id="{bar_id}" style="margin-top:8px;height:18px;border-radius:9px;background:rgba(0,0,0,.10);overflow:hidden;">
  <div style="height:100%;width:{pct}%;background:linear-gradient(90deg,#16a34a,#22c55e,#4ade80);"></div>
</div>
<div style="margin-top:6px;font-size:13px;opacity:.8;">
  達成率：<b>{pct:.1f}%</b>
</div>
""",
        unsafe_allow_html=True,
    )

# -----------------------------
# Analysis（圖表英文，避免亂碼）
# -----------------------------
def show_statistics(category, label):
    df_all = ensure_dataframe(st.session_state.data)

    # --- 週別合計（表）---
    st.subheader("週別合計")
    years = year_options(df_all)
    year = st.selectbox("年", years, index=len(years)-1, key=f"y_{category}")
    df_y = df_all[df_all["date"].dt.year == int(year)]
    if category == "app":
        df_y = df_y[df_y["type"].isin(["new", "exist", "line"])]
    else:
        df_y = df_y[df_y["type"] == "survey"]

    if df_y.empty:
        st.info("データがありません。")
        return

    df_y["iso_week"] = df_y["date"].dt.isocalendar().week.astype(int)
    weekly = df_y.groupby("iso_week")["count"].sum().reset_index()
    weekly["週"] = weekly["iso_week"].apply(lambda w: f"w{w}")
    st.dataframe(weekly[["週", "count"]].rename(columns={"count": "合計"}), use_container_width=True)

    # --- 週別推移グラフ（你的需求：原【日別（週選択）】改名 & selector 改為 年 / 週）---
    st.subheader("週別推移グラフ")
    yearD = st.selectbox("年", years, index=len(years)-1, key=f"daily_year_{category}")
    df_yearD = df_all[df_all["date"].dt.year == int(yearD)]
    if category == "app":
        df_yearD = df_yearD[df_yearD["type"].isin(["new", "exist", "line"])]
    else:
        df_yearD = df_yearD[df_yearD["type"] == "survey"]

    weeksD = sorted(set(df_yearD["date"].dt.isocalendar().week.astype(int).tolist()))
    week_labels = [f"w{w}" for w in weeksD] if weeksD else [f"w{date.today().isocalendar().week}"]
    sel_week = st.selectbox("週", week_labels, index=len(week_labels)-1, key=f"daily_week_{category}")
    sel_week_num = int(sel_week.lstrip("w"))

    df_week = df_yearD[df_yearD["date"].dt.isocalendar().week.astype(int) == sel_week_num].copy()
    df_week["weekday"] = df_week["date"].dt.weekday  # 0..6

    daily = df_week.groupby("weekday")["count"].sum().reindex(range(7), fill_value=0).reset_index()
    daily["label"] = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    plt.figure()
    plt.plot(daily["label"], daily["count"], marker="o")
    # 不顯示 Day of Week 的 xlabel（依你的要求）
    # plt.xlabel("Day of Week")
    if category == "survey":
        plt.title("Survey daily")
    else:
        plt.title(f"{label} Daily Totals: {yearD} {sel_week}")
    plt.ylabel("Count")
    st.pyplot(plt.gcf())

    # --- 月別累計（年次）---
    st.subheader("月別累計（年次）")
    df_monthly = (
        df_y.groupby(df_y["date"].dt.strftime("%Y-%m"))["count"]
        .sum()
        .reindex([f"{year}-{str(m).zfill(2)}" for m in range(1, 13)], fill_value=0)
    )
    labels = [calendar.month_abbr[int(m.split('-')[1])] for m in df_monthly.index]
    plt.figure()
    bars = plt.bar(labels, df_monthly.values)
    plt.title(f"{label} Monthly totals ({year})")
    plt.ylabel("Count")
    for b, v in zip(bars, df_monthly.values):
        plt.text(b.get_x()+b.get_width()/2, v, f"{int(v)}", ha="center", va="bottom")
    st.pyplot(plt.gcf())

# -----------------------------
# Tabs（與女生版一致的分頁結構）
# -----------------------------
tab_reg, tab3, tab4, tab5 = st.tabs(["件数登録", "and st 分析", "アンケート分析", "データ管理"])

# 這裡保持與你現有的資料管理相容
with tab3:
    show_statistics("app", "and st")

with tab4:
    show_statistics("survey", "アンケート")

with tab5:
    try:
        show_data_management()
    except Exception as e:
        st.error(f"データ管理画面の読み込みに失敗しました: {e}")
