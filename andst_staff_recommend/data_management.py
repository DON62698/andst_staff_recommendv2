import streamlit as st
import pandas as pd
from db_gsheets import load_all_records, delete_record

def show_data_management():
    st.header("📋 データ管理")

    records = load_all_records()
    if not records:
        st.info("現在、データが登録されていません。")
        return

    df = pd.DataFrame(records)
    # 確保 date 可轉為日期排序
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df.sort_values(by=["date", "name", "type"], ascending=[False, True, True], inplace=True)

    with st.expander("🔍 データを表示・検索", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            name_filter = st.text_input("名前フィルター（空白で全件）")
        with col2:
            type_filter = st.selectbox("タイプ", options=["すべて", "app", "survey"])

        filtered_df = df.copy()
        if name_filter:
            # 避免 NaN 造成錯誤、並改為部分一致（不使用正則）
            filtered_df = filtered_df[filtered_df["name"].astype(str).str.contains(name_filter, na=False, regex=False)]
        if type_filter != "すべて":
            filtered_df = filtered_df[filtered_df["type"] == type_filter]

        st.dataframe(filtered_df, use_container_width=True)

    with st.expander("🗑️ データを削除"):
        st.write("削除したい日付・名前・タイプを選択してください。")
        delete_date = st.date_input("日付（削除対象）")
        delete_name = st.text_input("名前（削除対象）")
        delete_type = st.selectbox("タイプ（削除対象）", options=["app", "survey"])

        if st.button("⚠️ このデータを削除する", type="primary"):
            if not delete_name:
                st.warning("名前を入力してください。")
            else:
                ok = delete_record(delete_date.strftime("%Y-%m-%d"), delete_name, delete_type)
                if ok:
                    st.success("データが削除されました。画面を更新します。")
                    try:
                          # Streamlit 1.30+
                    except Exception:
                          # 旧版互換
                else:
                    st.warning("該当するデータが見つかりませんでした。")

