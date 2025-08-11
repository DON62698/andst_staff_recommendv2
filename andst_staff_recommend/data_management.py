import streamlit as st
import pandas as pd
from datetime import date
import matplotlib.pyplot as plt

# ✅ Use the Google Sheets backend
from db_gsheets import (
    init_db,
    init_target_table,
    load_all_records,
    insert_or_update_record,
    get_target,
    set_target,
)
from data_management import show_data_management

# -----------------------
# Session initialization
# -----------------------
def init_session():
    if "data" not in st.session_state:
        # db_gsheets returns rows like: {date, week, name, type, count}
        st.session_state.data = load_all_records()
    if "names" not in st.session_state:
        st.session_state.names = set([r.get("name", "") for r in st.session_state.data if r.get("name")])

init_db()
init_target_table()
init_session()

st.title("and st統計記録")

tab1, tab2, tab3 = st.tabs(["APP推薦紀錄", "アンケート紀錄", "データ管理"])

def get_week_str(d: date) -> str:
    return f"{d.isocalendar().week}w"

# -----------------------
# Record form
# -----------------------
def record_form(label: str, category: str):
    st.subheader(label)
    with st.form(f"{category}_form"):
        col1, col2 = st.columns(2)
        with col1:
            selected_date = st.date_input("日付", value=date.today(), key=f"{category}_date")
        with col2:
            if st.session_state.names:
                name = st.selectbox("名前を選択", options=sorted(st.session_state.names), key=f"{category}_name_select")
            else:
                name = ""
            name_input = st.text_input("新しい名前を入力", key=f"{category}_name_input")

        if name_input:
            name = name_input.strip()
            if name:
                st.session_state.names.add(name)

        # Inputs
        if category == "app":
            new = st.number_input("新規", 0, 100, 0, key=f"{category}_new")
            exist = st.number_input("既存", 0, 100, 0, key=f"{category}_exist")
            line = st.number_input("LINE", 0, 100, 0, key=f"{category}_line")
        else:
            survey = st.number_input("アンケート件数", 0, 100, 0, key=f"{category}_survey")

        submitted = st.form_submit_button("保存")
        if submitted:
            if not name:
                st.warning("名前を入力または選択してください。")
                return

            date_str = selected_date.strftime("%Y-%m-%d")
            week = get_week_str(selected_date)

            # Remove existing entries for the same (date, name) and affected types from session
            def remove_from_session(types):
                st.session_state.data = [
                    r for r in st.session_state.data
                    if not (r.get("date")==date_str and r.get("name")==name and r.get("type") in types)
                ]

            if category == "app":
                # Types for app mode are separated into 3 rows: new/exist/line
                affected = ["new", "exist", "line"]
                remove_from_session(affected)

                for t, cnt in [("new", new), ("exist", exist), ("line", line)]:
                    insert_or_update_record(date_str, name, t, int(cnt))
                    st.session_state.data.append({
                        "date": date_str, "week": week, "name": name, "type": t, "count": int(cnt)
                    })
            else:
                affected = ["survey"]
                remove_from_session(affected)
                insert_or_update_record(date_str, name, "survey", int(survey))
                st.session_state.data.append({
                    "date": date_str, "week": week, "name": name, "type": "survey", "count": int(survey)
                })

            st.success("保存しました")

# -----------------------
# Tabs
# -----------------------
with tab1:
    record_form("APP推薦紀錄", "app")
    st.divider()
    st.subheader("APP月目標設定")
    current_month = date.today().strftime("%Y-%m")
    app_target = get_target(current_month, "app")
    new_app_target = st.number_input("APP 月目標件数", 0, 1000, app_target)
    if new_app_target != app_target:
        set_target(current_month, "app", int(new_app_target))
        try:
            st.rerun()
        except Exception:
            st.experimental_rerun()

with tab2:
    record_form("アンケート紀錄", "survey")
    st.divider()
    st.subheader("アンケート月目標設定")
    current_month = date.today().strftime("%Y-%m")
    survey_target = get_target(current_month, "survey")
    new_survey_target = st.number_input("アンケート 月目標件数", 0, 1000, survey_target)
    if new_survey_target != survey_target:
        set_target(current_month, "survey", int(new_survey_target))
        try:
            st.rerun()
        except Exception:
            st.experimental_rerun()

# -----------------------
# Statistics
# -----------------------
def show_statistics(category: str, label: str):
    st.header(f"{label} 統計")
    df = pd.DataFrame(st.session_state.data)
    if df.empty:
        st.info("まだデータがありません")
        return

    # date & month filter
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["month"] = df["date"].dt.strftime("%Y-%m")
    current_month = date.today().strftime("%Y-%m")
    df = df[df["month"] == current_month].copy()

    if category == "app":
        df = df[df["type"].isin(["new", "exist", "line"])]
        total = int(df["count"].sum())
        target = get_target(current_month, "app")
    else:
        df = df[df["type"] == "survey"]
        total = int(df["count"].sum())
        target = get_target(current_month, "survey")

    st.metric("今月累計件数", total)
    if target:
        st.metric("達成率", f"{(total / target * 100):.1f}%")

    st.subheader("週別件数")
    week_series = df.groupby("week")["count"].sum()
    st.bar_chart(week_series)

    st.subheader("スタッフ別合計")
    staff_series = df.groupby("name")["count"].sum()
    st.bar_chart(staff_series)

    if category == "app":
        st.subheader("構成比 (App vs LINE)")
        app_total = int(df[df["type"].isin(["new", "exist"])]["count"].sum())
        line_total = int(df[df["type"] == "line"]["count"].sum())
        if app_total + line_total > 0:
            plt.figure()
            plt.pie([app_total, line_total], labels=["App", "LINE"], autopct="%1.1f%%", startangle=90)
            st.pyplot(plt.gcf())

show_statistics("app", "APP")
show_statistics("survey", "アンケート")

with tab3:
    show_data_management()

