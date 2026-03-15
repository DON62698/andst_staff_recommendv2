
import plotly.graph_objects as go

def weekly_progress_chart(df):

    fig = go.Figure()

    fig.add_bar(
        x=df["week"],
        y=df["new"],
        name="New",
        marker_color="#3B82F6"
    )

    fig.add_bar(
        x=df["week"],
        y=df["existing"],
        name="Existing",
        marker_color="#F59E0B"
    )

    fig.add_bar(
        x=df["week"],
        y=df["line"],
        name="LINE",
        marker_color="#22C55E"
    )

    fig.add_scatter(
        x=df["week"],
        y=df["progress"],
        name="Progress Rate",
        mode="lines+markers+text",
        text=[f"{p}%" for p in df["progress"]],
        textposition="top center",
        line=dict(color="#EF4444",width=3)
    )

    fig.add_scatter(
        x=df["week"],
        y=df["target"],
        name="Target",
        mode="lines",
        line=dict(color="#84CC16",dash="dash")
    )

    fig.update_layout(
        barmode="stack",
        template="plotly_dark",
        height=420,
        legend_orientation="h",
        legend_y=1.1
    )

    return fig
