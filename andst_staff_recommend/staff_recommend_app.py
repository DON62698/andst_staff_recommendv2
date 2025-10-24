# -*- coding: utf-8 -*-
import os
from datetime import date
import uuid
import calendar

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# -----------------------------
# Page config & title (no icon/emojis)
# -----------------------------
try:
    st.set_page_config(page_title="and st 統計 Team Men's", layout="centered")
except Exception:
    pass

st.title("and st Men's")

# -----------------------------
# Japanese font (best-effort; avoid mojibake in UI texts)
# (Charts use EN labels so mojibake won't appear there)
# -----------------------------
from matplotlib import font_manager, rcParams

JP_FONT_READY = False
try_candidates = [
    os.path.join(os.path.dirname(__file__), "fonts", "NotoSansJP-Regular.otf"),
    os.path.join(os.path.dirname(__file__), "NotoSansJP-Regular.otf"),
    "/mnt/data/NotoSansJP-Regular.otf",
]
try:
    for fp in try_candidates:
        if os.path.exists(fp):
            font_manager.fontManager.addfont(fp)
            _prop = font_manager.FontProperties(fname=fp)
            rcParams["font.family"] = _prop.get_name()
            JP_FONT_READY = True
            break
    if not JP_FONT_READY:
        _JP_FONT_CANDIDATES = [
            "Noto Sans CJK JP", "Noto Sans JP", "IPAGothic", "IPAexGothic",
            "TakaoGothic", "Yu Gothic", "Hiragino Sans", "Meiryo", "MS Gothic",
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
# Backend（reuse your modules）
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

@st.cache_data(ttl=60)
def get_target_safe(month: str, category: str) -> int:
    try:
        return get_target(month, category)
    except Exception:
        return 0

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

def month_filter(df: pd.DataFrame, ym: str) -> pd.DataFrame:
    if "date" not in df.columns:
        return df.iloc[0:0]
    return df[(df["date"].dt.strftime("%Y-%m") == ym)]

def names_from_records(records) -> list:
    return sorted({(r.get("name") or "").strip() for r in (records or []) if r.get("name")})

# ---- Year / Week helpers ----
def year_options(df: pd.DataFrame) -> list:
    if "date" not in df.columns or df["date"].isna().all():
        return [date.today().year]
    years = sorted(set(df["date"].dropna().dt.year.astype(int).tolist()))
    return years or [date.today().year]

def _week_label(week_number: int) -> str:
    """ISO week label like 40 -> 'w40'"""
    return f"w{int(week_number)}"

def _period_options(df: pd.DataFrame, mode: str, selected_year: int):
    """Options for (週/単週, 月/単月, 年/単年) selectors."""
    if "date" not in df.columns or df["date"].isna().all():
        today = date.today()
        if mode == "週（単週）":
            ww = today.isocalendar().week
            return [f"w{ww}"], f"w{ww}"
        elif mode == "月（単月）":
            dft = today.strftime("%Y-%m"); return [dft], dft
        else:
            return [today.year], today.year

    dfx = df.dropna(subset=["date"]).copy()
    if mode == "週（単週）":
        dyear = dfx[dfx["date"].dt.year == int(selected_year)]
        weeks = sorted(set(dyear["date"].dt.isocalendar().week.astype(int).tolist()))
        labels = [f"w{w}" for w in weeks] or [f"w{date.today().isocalendar().week}"]
        default = f"w{date.today().isocalendar().week}"
        if default not in labels: default = labels[0]
        return labels, default
    elif mode == "月（単月）":
        dyear = dfx[dfx["date"].dt.year == int(selected_year)]
        months = sorted(set(dyear["date"].dt.strftime("%Y-%m").tolist()))
        if not months: months = [f"{selected_year}-01"]
        default = date.today().strftime("%Y-%m") if date.today().year == int(selected_year) else months[-1]
        if default not in months: default = months[0]
        return months, default
    else:  # 年
        ys = year_options(dfx)
        default = date.today().year if date.today().year in ys else ys[-1]
        return ys, default

def _filter_by_period(df: pd.DataFrame, mode: str, value, selected_year: int) -> pd.DataFrame:
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
# Session init
# -----------------------------
def init_session():
    if "data" not in st.session_state:
        st.session_state.data = load_all_records_cached()
    if "names" not in st.session_state:
        st.session_state.names = names_from_records(st.session_state.data)

_init_once()
init_session()

def render_refresh_button(btn_key: str = "refresh_btn"):
    spacer, right = st.columns([12, 1])
    with right:
        if st.button("↻", key=btn_key, help="重新整理資料"):
            load_all_records_cached.clear()
            st.session_state.data = load_all_records_cached()
            st.rerun()

# -----------------------------
# Progress meter (no emojis; charts remain EN)
# -----------------------------
def render_rate_block(category: str, label: str, current_total: int, target: int, ym: str):
    """
    Progress meter + target editor (UI may be JP; charts use EN).
    category: "app" or "survey"
    """
    pct = 0 if target <= 0 else min(100.0, round(current_total * 100.0 / max(1, target), 1))
    bar_id = f"meter_{category}_{uuid.uuid4().hex[:6]}"

    st.markdown(
        f"""
<div style="font-size:14px;opacity:.85;">
  {ym} の累計：<b>{current_total}</b> 件 ／ 目標：<b>{target}</b> 件
</div>
<div id="{bar_id}" style="
  margin-top:8px;height:18px;border-radius:9px;
  background:rgba(0,0,0,.10);overflow:hidden;">
  <div style="height:100%;width:{pct}%;
    background:linear-gradient(90deg,#16a34a,#22c55e,#4ade80);
    box-shadow:0 0 12px rgba(34,197,94,.45) inset;"></div>
</div>
<div style="margin-top:6px;font-size:13px;opacity:.8;">
  達成率：<b>{pct:.1f}%</b>
</div>
""",
        unsafe_allow_html=True,
    )

    with st.popover(f"目標を設定/更新（{label}）", use_container_width=True):
        new_target = st.number_input("月目標", min_value=0, step=1, value=int(target), key=f"target_input_{category}")
        if st.button("保存", key=f"target_save_{category}"):
            try:
                set_target(ym, "app" if category == "app" else "survey", int(new_target))
                try:
                    get_target_safe.clear()  # ignore if not cached
                except Exception:
                    pass
                st.success("保存しました。")
            except Exception as e:
                st.error(f"保存失敗: {e}")

# -----------------------------
# Analysis (mirrors women's structure; chart labels in EN)
# -----------------------------
def show_statistics(category: str, label: str):
    df_all = ensure_dataframe(st.session_state.data)
    ym = current_year_month()

    # --- Weekly totals table ---
    st.subheader("週別合計")
    yearsW = year_options(df_all)
    default_yearW = date.today().year if date.today().year in yearsW else yearsW[-1]
    colY, colM = st.columns(2)
    with colY:
        yearW = st.selectbox("年（週集計）", options=yearsW, index=yearsW.index(default_yearW), key=f"weekly_year_{category}")
    months_in_year = sorted(set(
        df_all[df_all["date"].dt.year == int(yearW)]["date"].dt.strftime("%Y-%m").dropna().tolist()
    )) or [f"{yearW}-{str(date.today().month).zfill(2)}"]
    default_monthW = (
        date.today().strftime("%Y-%m")
        if (date.today().year == int(yearW) and date.today().strftime("%Y-%m") in months_in_year)
        else months_in_year[-1]
    )
    with colM:
        monthW = st.selectbox("月", options=months_in_year, index=months_in_year.index(default_monthW), key=f"weekly_month_{category}")

    df_monthW = df_all[df_all["date"].dt.strftime("%Y-%m") == monthW].copy()
    if category == "app":
        df_monthW = df_monthW[df_monthW["type"].isin(["new", "exist", "line"])]
    else:
        df_monthW = df_monthW[df_monthW["type"] == "survey"]

    if df_monthW.empty:
        st.info("この月のデータがありません。")
    else:
        df_monthW["iso_week"] = df_monthW["date"].dt.isocalendar().week.astype(int)
        weekly = df_monthW.groupby("iso_week")["count"].sum().reset_index().sort_values("iso_week")
        weekly["w"] = weekly["iso_week"].map(_week_label)
        st.caption(f"表示中：{yearW}年・{monthW}")
        st.dataframe(weekly[["w", "count"]].rename(columns={"count": "合計"}), use_container_width=True)

    # --- Weekly trend line chart (renamed & simplified selectors) ---
    st.subheader("週別推移グラフ")
    yearsD = year_options(df_all)
    default_yearD = date.today().year if date.today().year in yearsD else yearsD[-1]
    colDW, colDY = st.columns([1, 1])
    with colDW:
        # 「週（wXX）」→「週」
        # 顯示 'wXX' 避免歧義，但標籤文字改為「週」
        df_yearD_all = df_all.copy()
        if category == "app":
            df_yearD_all = df_yearD_all[df_yearD_all["type"].isin(["new", "exist", "line"])]
        else:
            df_yearD_all = df_yearD_all[df_yearD_all["type"] == "survey"]
        weeksD = sorted(set(df_yearD_all["date"].dropna().dt.isocalendar().week.astype(int).tolist()))
        week_labels = [f"w{w}" for w in weeksD] or [f"w{date.today().isocalendar().week}"]
        default_wlabel = f"w{date.today().isocalendar().week}"
        if default_wlabel not in week_labels:
            default_wlabel = week_labels[0]
        sel_week_label = st.selectbox("週", options=week_labels, index=week_labels.index(default_wlabel), key=f"daily_week_{category}")
    with colDY:
        # 「年（日別・週選択）」→「年」
        yearD = st.selectbox("年", options=yearsD, index=yearsD.index(default_yearD), key=f"daily_year_{category}")

    try:
        sel_week_num = int(sel_week_label.lstrip("w"))
    except Exception:
        sel_week_num = date.today().isocalendar().week

    df_week = df_all.copy()
    if category == "app":
        df_week = df_week[df_week["type"].isin(["new", "exist", "line"])]
    else:
        df_week = df_week[df_week["type"] == "survey"]
    df_week = df_week[df_week["date"].dt.year == int(yearD)].copy()
    df_week["iso_week"] = df_week["date"].dt.isocalendar().week.astype(int)
    df_week = df_week[df_week["iso_week"] == sel_week_num].copy()
    df_week["weekday"] = df_week["date"].dt.weekday  # 0=Mon..6=Sun

    daily = df_week.groupby("weekday")["count"].sum().reindex(range(7), fill_value=0).reset_index()
    daily["label"] = daily["weekday"].map({0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"})

    # EN-only chart labels to avoid mojibake
    fig = plt.figure()
    plt.plot(daily["label"], daily["count"], marker="o")
    # 圖裡的 Day of Week 省略：不設 xlabel
    # plt.xlabel("Day of Week")
    if category == "survey":
        # 依你的指示：把アンケート的標題改為 "survey daily"
        plt.title("survey daily")
    else:
        plt.title(f"{label} Daily Totals: {yearD} {sel_week_label}")
    plt.ylabel("Count")
    st.pyplot(fig, clear_figure=True)

    # numbers table (EN column headers)
    st.dataframe(
        daily[["label", "count"]].rename(columns={"label": "Day", "count": "Total"}),
        use_container_width=True
    )

    # --- Composition pie (App only; EN labels) ---
    if category == "app":
        st.subheader("構成比（新規・既存・LINE）")
        colYc, colp1, colp2 = st.columns([1, 1, 2])
        years = year_options(df_all)
        default_year = date.today().year if date.today().year in years else years[-1]
        with colYc:
            year_sel = st.selectbox("年", options=years, index=years.index(default_year), key=f"comp_year_{category}")
        with colp1:
            ptype = st.selectbox("対象期間", ["週（単週）", "月（単月）", "年（単年）"], key=f"comp_period_type_{category}")
        with colp2:
            opts, default = _period_options(df_all, ptype, year_sel)
            idx = opts.index(default) if default in opts else 0
            sel = st.selectbox("表示する期間", options=opts, index=idx if len(opts) > 0 else 0, key=f"comp_period_value_{category}")

        df_comp_base = df_all[df_all["type"].isin(["new", "exist", "line"])].copy()
        df_comp = _filter_by_period(df_comp_base, ptype, sel, year_sel)
        new_sum  = int(df_comp[df_comp["type"] == "new"]["count"].sum())
        exist_sum= int(df_comp[df_comp["type"] == "exist_]()
