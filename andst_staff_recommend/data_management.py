import streamlit as st
import pandas as pd
from datetime import date
from db_gsheets import load_all_records, delete_record

def show_data_management():
    st.header("データ管理")

    if "data" not in st.session_state or st.button("🔄 最新データを取得"):
        st.session_state.data = load_all_records()

    records = st.session_state.get("data") or []
    df = pd.DataFrame(records)

    if df.empty:
        st.info("データがありません。")
    else:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["count"] = pd.to_numeric(df["count"], errors="coerce").fillna(0).astype(int)
        df = df.sort_values(["date", "name", "type"], ascending=[False, True, True])

        st.subheader("全レコード")
        st.dataframe(df, use_container_width=True)

    st.divider()
    st.subheader("レコード削除")

    c1, c2, c3 = st.columns(3)
    with c1:
        d = st.date_input("日付", value=date.today(), key="dm_del_date")
    with c2:
        name = st.text_input("スタッフ名", key="dm_del_name")
    with c3:
        tp = st.selectbox("種類", ["new", "exist", "line", "survey"], key="dm_del_type")

    if st.button("このレコードを削除"):
        if not name.strip():
            st.warning("スタッフ名を入力してください。")
        else:
            ok = delete_record(d.strftime("%Y-%m-%d"), name.strip(), tp)
            if ok:
                st.success("削除しました。")
                st.session_state.data = load_all_records()
            else:
                st.warning("該当レコードが見つかりませんでした。")


