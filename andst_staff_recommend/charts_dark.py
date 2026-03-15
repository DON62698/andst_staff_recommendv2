import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def weekly_progress_chart(df: pd.DataFrame, category: str = "app"):
    if df is None or df.empty:
        st.info("No chart data")
        return

    fig = go.Figure()

    if category == "app":
        fig.add_bar(name="New", x=df["week_label"], y=df["new"], marker_color="#3B82F6")
        fig.add_bar(name="Existing", x=df["week_label"], y=df["exist"], marker_color="#F59E0B")
        fig.add_bar(name="LINE", x=df["week_label"], y=df["line"], marker_color="#22C55E")
    else:
        fig.add_bar(name="Survey", x=df["week_label"], y=df["survey"], marker_color="#3B82F6")

    fig.add_trace(
        go.Scatter(
            x=df["week_label"],
            y=df["target"],
            mode="lines",
            name="Target",
            line=dict(color="#84CC16", dash="dash", width=2),
            yaxis="y1",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["week_label"],
            y=df["total"],
            mode="lines+markers+text",
            name="Progress Rate",
            line=dict(color="#EF4444", width=3),
            marker=dict(size=10, color="#EF4444"),
            text=[f"{v:.0f}%" for v in df["progress_rate"]],
            textposition="top center",
            yaxis="y1",
            customdata=df[["progress_rate"]].values,
            hovertemplate="%{x}<br>Total: %{y}<br>Progress Rate: %{customdata[0]:.1f}%<extra></extra>",
        )
    )

    fig.update_layout(
        barmode="stack",
        height=440,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor="#151A2D",
        plot_bgcolor="#151A2D",
        font=dict(color="#F3F4F6"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(title="Week", gridcolor="#2A314D", zeroline=False),
        yaxis=dict(title="Count", gridcolor="#2A314D", zeroline=False),
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})
