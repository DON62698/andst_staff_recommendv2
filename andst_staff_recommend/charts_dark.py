import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def _theme_palette(theme: str = "dark"):
    theme = (theme or "dark").lower()
    if theme == "light":
        return {
            "paper": "#FFFFFF",
            "plot": "#FFFFFF",
            "grid": "#E5E7EB",
            "text": "#111827",
            "border": "#E5E7EB",
            "new": "#3B82F6",
            "exist": "#F59E0B",
            "line": "#22C55E",
            "target": "#84CC16",
            "progress": "#EF4444",
        }
    return {
        "paper": "#151A2D",
        "plot": "#151A2D",
        "grid": "#2A314D",
        "text": "#F3F4F6",
        "border": "#232845",
        "new": "#3B82F6",
        "exist": "#F59E0B",
        "line": "#22C55E",
        "target": "#84CC16",
        "progress": "#EF4444",
    }


def weekly_progress_chart(df: pd.DataFrame, category: str = "app", theme: str = "dark"):
    if df is None or df.empty:
        st.info("No chart data")
        return

    c = _theme_palette(theme)
    fig = go.Figure()

    if category == "app":
        fig.add_bar(name="New", x=df["week_label"], y=df["new"], marker_color=c["new"])
        fig.add_bar(name="Existing", x=df["week_label"], y=df["exist"], marker_color=c["exist"])
        fig.add_bar(name="LINE", x=df["week_label"], y=df["line"], marker_color=c["line"])
    else:
        fig.add_bar(name="Survey", x=df["week_label"], y=df["survey"], marker_color=c["new"])

    fig.add_trace(
        go.Scatter(
            x=df["week_label"],
            y=[100] * len(df),
            mode="lines",
            name="Target",
            line=dict(color=c["target"], dash="dash", width=2),
            yaxis="y2",
            hovertemplate="%{x}<br>Target: 100%<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["week_label"],
            y=df["progress_rate"],
            mode="lines+markers+text",
            name="Progress Rate",
            line=dict(color=c["progress"], width=3),
            marker=dict(size=9, color=c["progress"]),
            text=[f"{v:.0f}%" for v in df["progress_rate"]],
            textposition="top center",
            yaxis="y2",
            hovertemplate="%{x}<br>Progress Rate: %{y:.1f}%<extra></extra>",
        )
    )

    fig.update_layout(
        barmode="stack",
        height=440,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor=c["paper"],
        plot_bgcolor=c["plot"],
        font=dict(color=c["text"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        xaxis=dict(title="Week", gridcolor=c["grid"], zeroline=False),
        yaxis=dict(title="Count", gridcolor=c["grid"], zeroline=False),
        yaxis2=dict(title="Progress Rate (%)", overlaying="y", side="right", showgrid=False, rangemode="tozero"),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})

# adjustments: larger bargap for PC print clarity and improved grid colors
