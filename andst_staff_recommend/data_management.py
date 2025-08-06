import streamlit as st
import pandas as pd
from db import load_all_records, insert_or_update_record, init_db
import sqlite3

def show_data_management():
    st.header("📋 データ管理")

    records = load_all_records()
    if not records:
        st.info("現在、データが登録されていません。")
        return

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df.sort_values(by=["date", "name", "type"], ascending=[False, True, True], inplace=True)

    with st.expander("🔍 データを表示・検索", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            name_filter = st.text_input("名前フィルター（空白で全件）")
        with col2:
            type_filter = st.selectbox("タイプ", options=["すべて", "app", "survey"])

        filtered_df = df.copy()
        if name_filter:
            filtered_df = filtered_df[filtered_df["name"].str.contains(name_filter)]
        if type_filter != "すべて":
            filtered_df = filtered_df[filtered_df["type"] == type_filter]

        st.dataframe(filtered_df, use_container_width=True)

    with st.expander("🗑️ データを削除"):
        st.write("削除したい日付・名前・タイプを選択してください。")
        delete_date = st.date_input("日付（削除対象）")
        delete_name = st.text_input("名前（削除対象）")
        delete_type = st.selectbox("タイプ（削除対象）", options=["app", "survey"])

        if st.button("⚠️ このデータを削除する"):
            deleted = delete_record(delete_date.strftime("%Y-%m-%d"), delete_name, delete_type)
            if deleted:
                st.success("データが削除されました。ページを更新してください。")
            else:
                st.warning("該当するデータが見つかりませんでした。")

def delete_record(date_str, name, category):
    conn = sqlite3.connect("recommend.db")
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM records WHERE date=? AND name=? AND type=?",
        (date_str, name, category)
    )
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted > 0
