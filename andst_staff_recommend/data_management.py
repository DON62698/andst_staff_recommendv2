import streamlit as st
import pandas as pd
from db_gsheets import load_all_records, delete_record

def show_data_management():
    st.header("📋 データ管理")

    # 1) 讀取資料
    records = load_all_records()
    if not records:
        st.info("現在、データが登録されていません。")
        return

    df = pd.DataFrame(records)

    # 確保基本欄位存在
    for col in ["date", "week", "name", "type", "count"]:
        if col not in df.columns:
            df[col] = None

    # 整理欄位型別與排序
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    # count 轉成數字（非數字者視為 0）
    df["count"] = pd.to_numeric(df["count"], errors="coerce").fillna(0).astype(int)
    df.sort_values(by=["date", "name", "type"], ascending=[False, True, True], inplace=True)

    # -----------------------------
    # 🔍 檢視／搜尋
    # -----------------------------
    with st.expander("🔍 データを表示・検索", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            name_filter = st.text_input("名前フィルター（空白で全件）")
        with col2:
            # ✅ UI 顯示：加入「App（新規+既存）」作為集合篩選；其餘對應到單一類型
            type_filter = st.selectbox(
                "タイプ",
                options=["すべて", "App（新規+既存）", "新規", "既存", "LINE", "アンケート"]
            )

        filtered_df = df.copy()
        if name_filter:
            # 避免 NaN + 模糊比對
            filtered_df = filtered_df[filtered_df["name"].fillna("").str.contains(name_filter, case=False, na=False)]

        # ✅ UI -> 實際存檔類型對應表
        ui_to_types = {
            "すべて": None,
            "App（新規+既存）": ["new", "exist"],
            "新規": ["new"],
            "既存": ["exist"],
            "LINE": ["line"],
            "アンケート": ["survey"],
        }

        # 依選項套用篩選
        if type_filter != "すべて":
            filtered_df = filtered_df[filtered_df["type"].isin(ui_to_types[type_filter])]

        # 顯示時把英文類型轉日文
        display_df = filtered_df.copy()
        jp_map = {"new": "新規", "exist": "既存", "line": "LINE", "survey": "アンケート"}
        display_df["タイプ"] = display_df["type"].map(jp_map).fillna(display_df["type"])

        # 選擇顯示欄位（ date, name, type->タイプ, count ； week 如需也可加進來）
        show_cols = []
        if "date" in display_df.columns:
            show_cols.append("date")
        if "name" in display_df.columns:
            show_cols.append("name")
        show_cols.append("タイプ")
        if "count" in display_df.columns:
            show_cols.append("count")

        st.dataframe(display_df[show_cols], use_container_width=True)

    # -----------------------------
    # 🗑️ 刪除資料
    # -----------------------------
    with st.expander("🗑️ データを削除", expanded=False):
        st.write("削除したい日付・名前・タイプを選択してください。")

        delete_date = st.date_input("日付（削除対象）")
        delete_name = st.text_input("名前（削除対象）")

        # ✅ 刪除時必須精確指定一個真實類型（不可用集合的 App）
        delete_type_ui = st.selectbox(
            "タイプ（削除対象）",
            options=["新規", "既存", "LINE", "アンケート"]
        )
        type_map = {"新規": "new", "既存": "exist", "LINE": "line", "アンケート": "survey"}
        delete_type = type_map[delete_type_ui]

      if st.button("⚠️ このデータを削除する", type="primary"):
    if not delete_name:
        st.warning("名前を入力してください。")
    else:
        ok = delete_record(delete_date.strftime("%Y-%m-%d"), delete_name, delete_type)
        if ok:
            st.success("データが削除されました。")
        else:
            st.warning("該当するデータが見つかりませんでした。")


 
    st.markdown(
       '''
     <style>
        .stApp {
        background-image: url('https://cdn.openai.com/chat-assets/brand/3682/A_graphic_design_advertisement_poster_for_%22niko_an.png');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
      }
    </style>
       '''
    , unsafe_allow_html=True
    )

