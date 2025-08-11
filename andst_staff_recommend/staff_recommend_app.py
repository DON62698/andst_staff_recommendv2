import streamlit as st
import pandas as pd
from datetime import date
import matplotlib.pyplot as plt

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


def _period_options(df: pd.DataFrame, mode: str):
    """回傳指定模式(週/月/年)的可選清單與預設值。週以『目前年份』為範圍。"""
    today = date.today()
    if mode == "週（単週）":
        if "date" not in df.columns or df["date"].isna().all():
            weeks = []
        else:
            cur_year = today.year
            weeks = sorted(
                set(df[df["date"].dt.year == cur_year]["date"].dt.isocalendar().week.astype(int).tolist())
            )
        opts = [f"w{int(w)}" for w in weeks] or [f"w{today.isocalendar().week}"]
        default = f"w{today.isocalendar().week}"
        return opts, default
    elif mode == "月（単月）":
        if "date" not in df.columns or df["date"].isna().all():
            opts = []
        else:
            opts = sorted(set(df["date"].dt.strftime("%Y-%m").dropna().tolist()))
        default = today.strftime("%Y-%m")
        return opts or [default], default
    else:  # 年（単年）
        if "date" not in df.columns or df["date"].isna().all():
            years = []
        else:
            years = sorted(set(df["date"].dt.year.dropna().astype(int).tolist()))
        default = str(today.year)
        opts = [str(y) for y in years] or [default]
        return opts, default


def _filter_by_period(df: pd.DataFrame, mode: str, value: str) -> pd.DataFrame:
    """依選擇的週/月/年回傳過濾後的資料。週以『目前年份』為範圍。"""
    if "date" not in df.columns or df["date"].isna().all():
        return df.iloc[0:0]
    if mode == "週（単週）":
        try:
            w = int(value.lower().lstrip("w"))
        except Exception:
            return df.iloc[0:0]
        cur_year = date.today().year
        return df[(df["date"].dt.year == cur_year) & (df["date"].dt.isocalendar().week == w)]
    elif mode == "月（単月）":
        return df[df["date"].dt.strftime("%Y-%m") == value]
    else:  # 年（単年）
        return df[df["date"].dt.year.astype(str) == value]


# -----------------------------
# Session 初始化
# -----------------------------
def init_session():
    if "data" not in st.session_state:
        st.session_state.data = load_all_records_cached()
    if "names" not in st.session_state:
        st.session_state.names = names_from_records(st.session_state.data)
    if "app_target" not in st.session_state:
        st.session_state.app_target = 0
    if "survey_target" not in st.session_state:
        st.session_state.survey_target = 0


# ✅ 只做一次外部初始化
_init_once()
# ✅ 每次 rerun 都整理好 UI 狀態
init_session()


# -----------------------------
# 版頭
# -----------------------------
st.title("and st 統計記録")

tab1, tab2, tab3 = st.tabs(["APP推薦紀錄", "アンケート紀錄", "データ管理"])


# -----------------------------
# 統計區塊（含 構成比 + スタッフ別 合計 的新控制）
# -----------------------------
def show_statistics(category: str, label: str):
    """
    category: "app" 或 "survey"
    label: 顯示標題
    """
    df_all = ensure_dataframe(st.session_state.data)
    ym = current_year_month()

    # 目標值（有 cache）
    target = get_target_safe(ym, "app" if category == "app" else "survey")

    # === 目標區塊（沿用月度目標） ===
    if category == "app":
        df_m_app = month_filter(df_all, ym)
        current_total = int(df_m_app[df_m_app["type"].isin(["new", "exist", "line"])]["count"].sum())
    else:
        df_m = month_filter(df_all, ym)
        current_total = int(df_m[df_m["type"] == "survey"]["count"].sum())

    st.subheader(f"{label}（{ym}）")
    colA, colB = st.columns([2, 1])
    with colA:
        st.write(f"今月累計：**{current_total}** 件")
        if target > 0:
            ratio = min(1.0, current_total / max(1, target))
            st.progress(ratio, text=f"目標 {target} 件・達成率 {ratio*100:.1f}%")
        else:
            st.info("目標未設定")
    with colB:
        with st.popover("🎯 目標を設定/更新"):
            new_target = st.number_input("今月目標", min_value=0, step=1, value=int(target))
            if st.button(f"保存（{label}）"):
                try:
                    set_target(ym, "app" if category == "app" else "survey", int(new_target))
                    # 目標值快取刷新
                    get_target_safe.clear()
                    st.success("保存しました。")
                except Exception as e:
                    st.error(f"保存失敗: {e}")

    # === 週別合計（保留月內的週統計表） ===
    df_m_all = month_filter(df_all, ym).copy()
    if not df_m_all.empty:
        df_m_all["week"] = df_m_all["date"].dt.isocalendar().week
        if category == "app":
            df_w = df_m_all[df_m_all["type"].isin(["new", "exist", "line"])]
        else:
            df_w = df_m_all[df_m_all["type"] == "survey"]
        weekly = df_w.groupby("week")["count"].sum().reset_index().sort_values("week")
        st.write("**週別合計**（w）：")
        st.dataframe(weekly.rename(columns={"week": "w"}), use_container_width=True)
    else:
        st.info("今月のデータがありません。")

    # === 構成比（新規・既存・LINE）— 可選：單週/單月/單年 ===
    if category == "app":
        st.subheader("構成比（新規・既存・LINE）")
        colp1, colp2 = st.columns(2)
        with colp1:
            ptype = st.selectbox(
                "対象期間",
                ["週（単週）", "月（単月）", "年（単年）"],
                key=f"comp_period_type_{category}",
            )
        with colp2:
            opts, default = _period_options(df_all, ptype)
            idx = opts.index(default) if default in opts else 0
            sel = st.selectbox(
                "表示する期間",
                options=opts,
                index=idx if len(opts) > 0 else 0,
                key=f"comp_period_value_{category}",
            )

        df_comp_base = df_all[df_all["type"].isin(["new", "exist", "line"])].copy()
        df_comp = _filter_by_period(df_comp_base, ptype, sel)

        new_sum = int(df_comp[df_comp["type"] == "new"]["count"].sum())
        exist_sum = int(df_comp[df_comp["type"] == "exist"]["count"].sum())
        line_sum = int(df_comp[df_comp["type"] == "line"]["count"].sum())
        total = new_sum + exist_sum + line_sum

        if total > 0:
            st.caption(f"表示中：{sel}")
            plt.figure()
            plt.pie(
                [new_sum, exist_sum, line_sum],
                labels=["新規", "既存", "LINE"],
                autopct="%1.1f%%",
                startangle=90,
            )
            st.pyplot(plt.gcf())
        else:
            st.info("対象データがありません。")

    # === スタッフ別 合計 — 預設『當週』，同樣可選 週/月/年 ===
    st.subheader("スタッフ別 合計")
    cols = st.columns(2)
    with cols[0]:
        ptype2 = st.selectbox(
            "対象期間",
            ["週（単週）", "月（単月）", "年（単年）"],
            key=f"staff_period_type_{category}",
            index=0,  # 預設顯示當週
        )
    with cols[1]:
        opts2, default2 = _period_options(df_all, ptype2)
        idx2 = opts2.index(default2) if default2 in opts2 else 0
        sel2 = st.selectbox(
            "表示する期間",
            options=opts2,
            index=idx2 if len(opts2) > 0 else 0,
            key=f"staff_period_value_{category}",
        )
    st.caption(f"（{sel2}）")  # 顯示副標，例如 w32

    if category == "app":
        df_staff_base = df_all[df_all["type"].isin(["new", "exist", "line"])].copy()
    else:
        df_staff_base = df_all[df_all["type"] == "survey"].copy()

    df_staff = _filter_by_period(df_staff_base, ptype2, sel2)
    if df_staff.empty:
        st.info("対象データがありません。")
    else:
        staff_sum = (
            df_staff.groupby("name")["count"].sum()
            .reset_index()
            .sort_values("count", ascending=False)
        )
        st.dataframe(staff_sum, use_container_width=True)


# -----------------------------
# 表單：APP 推薦紀錄
# -----------------------------
with tab1:
    st.subheader("入力（App 推薦）")
    with st.form("app_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            d = st.date_input("日付", value=date.today())
        with c2:
            # 名字輸入：選擇 / 新規輸入
            existing_names = st.session_state.names
            default_mode = "選択" if existing_names else "新規入力"
            name_mode = st.radio(
                "名前の入力方法", ["選択", "新規入力"],
                horizontal=True, key="app_name_mode",
                index=(0 if default_mode == "選択" else 1)
            )
            if name_mode == "選択" and existing_names:
                name = st.selectbox(
                    "スタッフ名（選択）",
                    options=existing_names,
                    index=0,
                    key="app_name_select"
                )
            else:
                name = st.text_input("スタッフ名（新規入力）", key="app_name_text")
        with c3:
            pass

        coln1, coln2, coln3 = st.columns(3)
        with coln1:
            new_cnt = st.number_input("新規（件）", min_value=0, step=1, value=0)
        with coln2:
            exist_cnt = st.number_input("既存（件）", min_value=0, step=1, value=0)
        with coln3:
            line_cnt = st.number_input("LINE（件）", min_value=0, step=1, value=0)

        submitted = st.form_submit_button("保存")
        if submitted:
            name = (name or "").strip()
            if not name:
                st.warning("名前を入力してください。")
            else:
                try:
                    if new_cnt > 0:
                        insert_or_update_record(ymd(d), name, "new", int(new_cnt))
                    if exist_cnt > 0:
                        insert_or_update_record(ymd(d), name, "exist", int(exist_cnt))
                    if line_cnt > 0:
                        insert_or_update_record(ymd(d), name, "line", int(line_cnt))
                    # 重新抓資料並更新名字清單（清 cache 再讀，避免舊資料）
                    load_all_records_cached.clear()
                    st.session_state.data = load_all_records_cached()
                    st.session_state.names = names_from_records(st.session_state.data)
                    st.success("保存しました。")
                except Exception as e:
                    st.error(f"保存失敗: {e}")

    # 本月統計
    show_statistics("app", "APP")


# -----------------------------
# 表單：アンケート（問卷取得件數）
# -----------------------------
with tab2:
    st.subheader("入力（アンケート）")
    with st.form("survey_form"):
        c1, c2 = st.columns(2)
        with c1:
            d2 = st.date_input("日付", value=date.today(), key="survey_date")
        with c2:
            # 名字輸入：選擇 / 新規輸入
            existing_names2 = st.session_state.names
            default_mode2 = "選択" if existing_names2 else "新規入力"
            name_mode2 = st.radio(
                "名前の入力方法", ["選択", "新規入力"],
                horizontal=True, key="survey_name_mode",
                index=(0 if default_mode2 == "選択" else 1)
            )
            if name_mode2 == "選択" and existing_names2:
                name2 = st.selectbox(
                    "スタッフ名（選択）",
                    options=existing_names2,
                    index=0,
                    key="survey_name_select"
                )
            else:
                name2 = st.text_input("スタッフ名（新規入力）", key="survey_name_text")

        cnt = st.number_input("アンケート（件）", min_value=0, step=1, value=0)
        submitted2 = st.form_submit_button("保存")
        if submitted2:
            name2 = (name2 or "").strip()
            if not name2:
                st.warning("名前を入力してください。")
            else:
                try:
                    if cnt > 0:
                        insert_or_update_record(ymd(d2), name2, "survey", int(cnt))
                    # 重新抓資料並更新名字清單（清 cache 再讀，避免舊資料）
                    load_all_records_cached.clear()
                    st.session_state.data = load_all_records_cached()
                    st.session_state.names = names_from_records(st.session_state.data)
                    st.success("保存しました。")
                except Exception as e:
                    st.error(f"保存失敗: {e}")

    # 本月統計
    show_statistics("survey", "アンケート")


# -----------------------------
# データ管理
# -----------------------------
with tab3:
    show_data_management()
