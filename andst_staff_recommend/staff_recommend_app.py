import streamlit as st
import pandas as pd
from datetime import date
import calendar
import matplotlib.pyplot as plt
from collections import defaultdict
from db import init_db, init_target_table, load_all_records, save_record, delete_record, get_target, set_target
from bg_style import set_pixel_background

def init_session():
    if "data" not in st.session_state:
        st.session_state.data = load_all_records()
    if "names" not in st.session_state:
        st.session_state.names = set([r["name"] for r in st.session_state.data])
    if "app_target" not in st.session_state:
        st.session_state.app_target = get_target("app")
    if "survey_target" not in st.session_state:
        st.session_state.survey_target = get_target("survey")

init_db()
init_target_table()
init_session()
set_pixel_background()

st.title("and st 統計記録")

tab1, tab2 = st.tabs(["APP推薦紀錄", "アンケート紀錄"])

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
                "date": selected_date.isoformat(),
                "week": get_week_str(selected_date),
                "name": name,
                "type": category,
            }
            if category == "app":
                record.update({"新規": new, "既存": exist, "LINE": line})
            else:
                record.update({"アンケート": survey})
            save_record(record)
            st.session_state.data = load_all_records()
            st.success("保存しました")

    with st.expander("入力済みデータ"):
        records = [r for r in st.session_state.data if r["type"] == category]
        if not records:
            st.info("まだデータがありません")
        else:
            df = pd.DataFrame(records)
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values(by="date", ascending=False)
            st.dataframe(df)

            delete_date = st.date_input("削除対象の日付", key=f"{category}_delete_date")
            delete_name = st.selectbox("削除対象の名前", options=sorted(st.session_state.names), key=f"{category}_delete_name")
            if st.button("削除", key=f"{category}_delete_button"):
                delete_record(delete_date, delete_name, category)
                st.session_state.data = load_all_records()
                st.success("削除しました")

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

with tab1:
    record_form("APP推薦紀錄", "app")
    st.divider()
    st.subheader("APP月目標設定")
    new_target = st.number_input("APP 月目標件数", 0, 1000, st.session_state.app_target)
    if new_target != st.session_state.app_target:
        st.session_state.app_target = new_target
        set_target("app", new_target)

with tab2:
    record_form("アンケート紀錄", "survey")
    st.divider()
    st.subheader("アンケート月目標設定")
    new_target = st.number_input("アンケート 月目標件数", 0, 1000, st.session_state.survey_target)
    if new_target != st.session_state.survey_target:
        st.session_state.survey_target = new_target
        set_target("survey", new_target)

show_statistics("app", "APP")
show_statistics("survey", "アンケート")
