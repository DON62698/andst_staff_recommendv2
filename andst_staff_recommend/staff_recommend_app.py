import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar
import matplotlib.pyplot as plt
from collections import defaultdict
from db import init_db, insert_or_update_record, load_all_records, get_target, set_target, init_target_table

# 初始化 session state
def init_db()
init_target_table()
init_session():
    init_db()
    if "data" not in st.session_state:
        st.session_state.data = load_all_records()
    if "names" not in st.session_state:
        st.session_state.names = set([r["name"] for r in st.session_state.data])
    if "app_target" not in st.session_state:
        st.session_state.app_target = 0
    if "survey_target" not in st.session_state:
        st.session_state.survey_target = 0

init_db()
init_target_table()
init_session()

st.title("and st統計記録")

from data_management import show_data_management

tab1, tab2, tab3 = st.tabs(["APP推薦紀錄", "アンケート紀錄", "データ管理"])

def get_week_str(input_date):
    return f"{input_date.isocalendar().week}w"

def record_form(label, category):
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
            name = name_input
            st.session_state.names.add(name_input)

        if category == "app":
            new = st.number_input("新規", 0, 100, 0, key=f"{category}_new")
            exist = st.number_input("既存", 0, 100, 0, key=f"{category}_exist")
            line = st.number_input("LINE", 0, 100, 0, key=f"{category}_line")
        else:
            survey = st.number_input("アンケート件数", 0, 100, 0, key=f"{category}_survey")

        submitted = st.form_submit_button("保存")
        if submitted:
            record = {
                "date": selected_date.strftime("%Y-%m-%d"),
                "week": get_week_str(selected_date),
                "name": name,
                "type": category,
            }
            if category == "app":
                record.update({"新規": new, "既存": exist, "LINE": line})
            else:
                record.update({"アンケート": survey})

            # 更新記憶體並寫入資料庫
            st.session_state.data = [r for r in st.session_state.data if not (r["date"] == record["date"] and r["name"] == name and r["type"] == category)]
            st.session_state.data.append(record)
            insert_or_update_record(record)

            st.success("保存しました")

with tab1:
    record_form("APP推薦紀錄", "app")
    st.divider()
    st.subheader("APP月目標設定")
    
current_month = date.today().strftime("%Y-%m")
app_target = get_target(current_month, "app")
new_app_target = st.number_input("APP 月目標件数", 0, 1000, app_target)
if new_app_target != app_target:
    set_target(current_month, "app", int(new_app_target))
    st.experimental_rerun()


with tab2:
    record_form("アンケート紀錄", "survey")
    st.divider()
    st.subheader("アンケート月目標設定")
    
survey_target = get_target(current_month, "survey")
new_survey_target = st.number_input("アンケート 月目標件数", 0, 1000, survey_target)
if new_survey_target != survey_target:
    set_target(current_month, "survey", int(new_survey_target))
    st.experimental_rerun()


def show_statistics(category, label):
    st.header(f"{label} 統計")

    df = pd.DataFrame([r for r in st.session_state.data if r["type"] == category])
    if df.empty:
        st.info("まだデータがありません")
        return

    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.strftime("%Y-%m")
    current_month = date.today().strftime("%Y-%m")
    df = df[df["month"] == current_month]

    if category == "app":
        total = df[["新規", "既存", "LINE"]].sum().sum()
        target = st.session_state.app_target
    else:
        total = df["アンケート"].sum()
        target = st.session_state.survey_target

    st.metric("今月累計件数", int(total))
    if target:
        st.metric("達成率", f"{(total / target * 100):.1f}%")

    st.subheader("週別件数")
    week_data = df.groupby("week").sum(numeric_only=True)
    st.bar_chart(week_data)

    st.subheader("スタッフ別合計")
    staff_data = df.groupby("name").sum(numeric_only=True)
    st.bar_chart(staff_data)

    if category == "app":
        st.subheader("構成比 (App vs LINE)")
        app_total = df[["新規", "既存"]].sum().sum()
        line_total = df["LINE"].sum()
        if app_total + line_total > 0:
            plt.figure()
            plt.pie([app_total, line_total], labels=["App", "LINE"], autopct="%1.1f%%", startangle=90)
            st.pyplot(plt.gcf())

show_statistics("app", "APP")
show_statistics("survey", "アンケート")

with tab3:
    show_data_management()
