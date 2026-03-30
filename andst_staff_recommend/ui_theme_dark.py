import streamlit as st


def apply_dark_theme():
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(180deg, #090d16 0%, #0b0f1a 100%);
            color: #F3F4F6;
        }
        .block-container {
            max-width: 1300px;
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }
        h1, h2, h3, h4, h5, h6, p, label, span, div {
            color: #F3F4F6;
        }
        [data-testid="stTabs"] button {
            color: #cdd5df;
            border-radius: 10px 10px 0 0;
            padding: 0.5rem 1rem;
        }
        [data-testid="stTabs"] button[aria-selected="true"] {
            color: #ffffff;
            border-bottom: 2px solid #3B82F6;
        }
        [data-testid="stSelectbox"], [data-testid="stDateInput"], [data-testid="stNumberInput"], [data-testid="stTextInput"] {
            background: transparent;
        }
        [data-testid="stSelectbox"] > div,
        [data-testid="stDateInput"] > div,
        [data-testid="stNumberInput"] > div,
        [data-testid="stTextInput"] > div {
            background: #12182a;
            border: 1px solid #232845;
            border-radius: 12px;
        }
        .stButton > button, .stDownloadButton > button, div[data-testid="stFormSubmitButton"] > button {
            background: #2563eb;
            color: #fff;
            border: 0;
            border-radius: 12px;
            padding: 0.55rem 1rem;
            font-weight: 600;
        }
        .dark-card {
            background: linear-gradient(180deg, rgba(21,26,45,0.96) 0%, rgba(15,19,34,0.96) 100%);
            border: 1px solid #232845;
            border-radius: 18px;
            padding: 1rem 1.1rem;
            box-shadow: 0 6px 24px rgba(0,0,0,0.22);
            min-height: 112px;
        }
        .dark-card .label {
            font-size: 0.95rem;
            color: #c3c9d4;
            margin-bottom: 0.45rem;
        }
        .dark-card .value {
            font-size: 2rem;
            font-weight: 700;
            line-height: 1.1;
            color: #f8fafc;
        }
        .dark-card .unit {
            font-size: 1rem;
            color: #c3c9d4;
            margin-left: 0.2rem;
        }
        .dark-card .sub {
            margin-top: 0.35rem;
            color: #8ce99a;
            font-size: 0.9rem;
        }
        .section-wrap {
            margin-bottom: 0.8rem;
        }
        .section-title {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.15rem;
        }
        .section-sub {
            font-size: 0.98rem;
            color: #a8b0bf;
            margin-bottom: 1rem;
        }
        [data-testid="stDataFrame"] {
            border: 1px solid #232845;
            border-radius: 16px;
            overflow: hidden;
        }
        @media (max-width: 768px) {
            .block-container { padding-left: 0.8rem; padding-right: 0.8rem; }
            .dark-card { min-height: 100px; padding: 0.9rem; }
            .dark-card .value { font-size: 1.7rem; }
            .section-title { font-size: 1.7rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_section_title(title: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div class="section-wrap">
            <div class="section-title">{title}</div>
            {f'<div class="section-sub">{subtitle}</div>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_row(cards):
    cols = st.columns(len(cards))
    for col, (label, value, unit, sub) in zip(cols, cards):
        with col:
            st.markdown(
                f"""
                <div class="dark-card">
                    <div class="label">{label}</div>
                    <div><span class="value">{value}</span><span class="unit">{unit}</span></div>
                    {f'<div class="sub">{sub}</div>' if sub else '<div class="sub">&nbsp;</div>'}
                </div>
                """,
                unsafe_allow_html=True,
            )
