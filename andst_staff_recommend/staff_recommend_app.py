# === 月別累計（年次）長條圖 ===
st.subheader("月別累計（年次）")
years3 = year_options(df_all)
default_year3 = date.today().year if date.today().year in years3 else years3[-1]
year_sel3 = st.selectbox("年を選択", options=years3, index=years3.index(default_year3), key=f"monthly_year_{category}")

if category == "app":
    df_year = df_all[(df_all["date"].dt.year == int(year_sel3)) & (df_all["type"].isin(["new", "exist", "line"]))]
else:
    df_year = df_all[(df_all["date"].dt.year == int(year_sel3)) & (df_all["type"] == "survey")]

if df_year.empty:
    st.info("対象データがありません。")
else:
    import calendar

    # 產生 12 個月份的序列（即使沒資料也顯示 0）
    monthly = (
        df_year.groupby(df_year["date"].dt.strftime("%Y-%m"))["count"]
        .sum()
        .reindex([f"{year_sel3}-{str(m).zfill(2)}" for m in range(1, 13)], fill_value=0)
    )

    # X 軸：英文月份簡寫；Y：該月數值
    labels = [calendar.month_abbr[int(s.split("-")[1])] for s in monthly.index.tolist()]  # Jan, Feb, ...
    values = monthly.values.tolist()

    plt.figure()
    bars = plt.bar(labels, values)

    # 加上 y 軸細網格線，幫助讀值
    plt.grid(True, axis="y", linestyle="--", linewidth=0.5)

    # X 標籤用英文縮寫就不需要旋轉
    plt.xticks(rotation=0, ha="center")

    # 標題（有日文字型→日文；無→英文，避免亂碼）
    plt.title(chart_title(label, int(year_sel3)))

    # 在每個長條上方標出數值
    ymax = max(values) if values else 0
    if ymax > 0:
        plt.ylim(0, ymax * 1.15)  # 保留上方空間給數字
    for bar, val in zip(bars, values):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{int(val)}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    st.pyplot(plt.gcf())
