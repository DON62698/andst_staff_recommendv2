import streamlit as st
import pandas as pd
from datetime import date, datetime
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
# Session 初始化
# -----------------------------
def init_session():
    if "data" not in st.session_state:
        st.session_state.data = load_all_records_cached()
    if "names" not in st.session_state:
        st.session_state.names = set(
            [r.get("name", "") for r in st.session_state.data if r.get("name")]
        )
    if "app_target" not in st.session_state:
        st.session_state.app_target = 0
    if "survey_target" not in st.session_state:
        st.session_state.survey_target = 0


# ✅ 只做一次外部初始化
_init_once()
# ✅ 每次 rerun 都整理好 UI 狀態
init_session()


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


# -----------------------------
# 版頭
# -----------------------------
st.title("and st 統計記録")

tab1, tab2, tab3 = st.tabs(["APP推薦紀錄", "アンケート紀錄", "データ管理"])


# -----------------------------
# 統計區塊
# -----------------------------
def show_statistics(category: str, label: str):
    """
    category: "app" 或 "survey"
    label: 顯示標題
    """
    df_all = ensure_dataframe(st.session_state.data)
    ym = current_year_month()

    # 目標值（有 cache）
    if category == "app":
        target = get_target_safe(ym, "app")
    else:
        target = get_target_safe(ym, "survey")

    # 本月資料
    df_m = month_filter(df_all, ym).copy()

    # 類型切分
    if category == "app":
        df_m_app = df_m[df_m["type"].isin(["new", "exist"])]
        df_m_line = df_m[df_m["type"] == "line"]
        total_app = int(df_m_app["count"].sum())
        total_line = int(df_m_line["count"].sum())
        total_for_target = total_app + total_line  # 你的需求若只算 App，可改成 total_app
    else:
        df_m_survey = df_m[df_m["type"] == "survey"]
        total_for_target = int(df_m_survey["count"].sum())

    st.subheader(f"{label}（{ym}）")

    # 目標設定/顯示
    colA, colB = st.columns([2, 1])
    with colA:
        current_total = total_for_target
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
                    st.success("保存しました。")
                except Exception as e:
                    st.error(f"保存失敗: {e}")

    # 週別統計
    if not df_m.empty:
        df_m["week"] = df_m["date"].dt.isocalendar().week
        if category == "app":
            df_w = df_m[df_m["type"].isin(["new", "exist", "line"])]
        else:
            df_w = df_m[df_m["type"] == "survey"]
        weekly = df_w.groupby("week")["count"].sum().reset_index().sort_values("week")
        st.write("**週別合計**（w）：")
        st.dataframe(weekly.rename(columns={"week": "w"}), use_container_width=True)

        # 構成比（App vs LINE）
        if category == "app":
            app_total = int(df_m[df_m["type"].isin(["new", "exist"])]["count"].sum())
            line_total = int(df_m[df_m["type"] == "line"]["count"].sum())
            if app_total + line_total > 0:
                st.subheader("構成比 (App vs LINE)")
                plt.figure()
                plt.pie([app_total, line_total], labels=["App", "LINE"], autopct="%1.1f%%", startangle=90)
                st.pyplot(plt.gcf())

        # 員工別合計
        st.write("**スタッフ別 合計**：")
        if category == "app":
            df_staff = df_w
        else:
            df_staff = df_w
        staff_sum = (
            df_staff.groupby("name")["count"].sum().reset_index().sort_values("count", ascending=False)
        )
        st.dataframe(staff_sum, use_container_width=True)
    else:
        st.info("今月のデータがありません。")


# -----------------------------
# 表單：APP 推薦紀錄
# -----------------------------
with tab1:
    st.subheader("入力（App 推薦）")
    with st.form("app_form", border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            d = st.date_input("日付", value=date.today())
        with c2:
            name = st.text_input("スタッフ名")
        with c3:
            # 下次可改成 selectbox 使用 st.session_state.names
            add_to_names = st.checkbox("入力した名前を記憶", value=True)

        coln1, coln2, coln3 = st.columns(3)
        with coln1:
            new_cnt = st.number_input("新規（件）", min_value=0, step=1, value=0)
        with coln2:
            exist_cnt = st.number_input("既存（件）", min_value=0, step=1, value=0)
        with coln3:
            line_cnt = st.number_input("LINE（件）", min_value=0, step=1, value=0)

        submitted = st.form_submit_button("保存")
        if submitted:
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
                    if add_to_names and name:
                        st.session_state.names.add(name)
                    # 重新讀取快取資料（不 rerun，減少 API）
                    st.session_state.data = load_all_records_cached()
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
    with st.form("survey_form", border=True):
        c1, c2 = st.columns(2)
        with c1:
            d2 = st.date_input("日付", value=date.today(), key="survey_date")
        with c2:
            name2 = st.text_input("スタッフ名", key="survey_name")

        cnt = st.number_input("アンケート（件）", min_value=0, step=1, value=0)
        submitted2 = st.form_submit_button("保存")
        if submitted2:
            if not name2:
                st.warning("名前を入力してください。")
            else:
                try:
                    if cnt > 0:
                        insert_or_update_record(ymd(d2), name2, "survey", int(cnt))
                    st.session_state.data = load_all_records_cached()
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
