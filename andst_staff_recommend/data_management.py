import streamlit as st
import pandas as pd
from datetime import date

# --- 安全匯入 db_gsheets：匯入失敗也不讓整頁爆掉 ---
_DB = None
_IMPORT_ERR = None
try:
    import db_gsheets as _DB
except Exception as e:
    _IMPORT_ERR = e

def _load_all_records_safe():
    if _DB and hasattr(_DB, "load_all_records"):
        return _DB.load_all_records()
    st.error("❌ 無法載入資料：db_gsheets.load_all_records 不存在（或匯入失敗）。")
    return []

def _delete_record_safe(date_str: str, name: str, tp: str) -> bool:
    if _DB and hasattr(_DB, "delete_record"):
        return _DB.delete_record(date_str, name, tp)
    st.error("❌ 無法刪除：db_gsheets.delete_record 不存在（或匯入失敗）。")
    return False

def show_data_management():
    st.header("データ管理")
    st.caption("build: dm-restore-safeimport")

    # 匯入診斷資訊（只在匯入失敗時顯示）
    if _DB is None:
        with st.expander("⚠️ 診斷：db_gsheets 匯入失敗（點我展開）", expanded=True):
            st.write("原始 ImportError（非敏感版）：", str(_IMPORT_ERR))
            st.write("請檢查：")
            st.markdown(
                "- 檔案是否存在：`andst_staff_recommend/db_gsheets.py`\n"
                "- 是否跟 `data_management.py` 在**同一個資料夾**\n"
                "- 檔名是否拼對（是 `db_gsheets.py` 不是 `db.py`）\n"
                "- 覆蓋後有沒有 **⋯ → Clear cache** 再 **Rerun**\n"
            )
    else:
        # 顯示實際載入模組的路徑與可用函式，有助確認覆蓋到正確檔案
        with st.expander("ℹ️ 已載入的 db_gsheets（定位用）", expanded=False):
            st.write("file:", getattr(_DB, "__file__", "(unknown)"))
            st.write("exports:", [n for n in dir(_DB) if not n.startswith("_")])

    # 讀取資料
    if "data" not in st.session_state or st.button("🔄 最新データを取得"):
        st.session_state.data = _load_all_records_safe()

    records = st.session_state.get("data") or []
    df = pd.DataFrame(records)

    # 顯示資料表
    if df.empty:
        st.info("データがありません。")
    else:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["count"] = pd.to_numeric(df["count"], errors="coerce").fillna(0).astype(int)
        df = df.sort_values(["date", "name", "type"], ascending=[False, True, True])

        st.subheader("全レコード")
        st.dataframe(df, use_container_width=True)

    st.divider()

    # 刪除單筆
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
            ok = _delete_record_safe(d.strftime("%Y-%m-%d"), name.strip(), tp)
            if ok:
                st.success("削除しました。")
                st.session_state.data = _load_all_records_safe()
            else:
                st.warning("該当レコードが見つかりませんでした。")
