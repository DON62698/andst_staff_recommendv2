import streamlit as st


def apply_dark_theme():
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 1300px;
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }

        /* ---------- Shared ---------- */
        [data-testid="stTabs"] button {
            border-radius: 10px 10px 0 0;
            padding: 0.5rem 1rem;
        }
        .stButton > button,
        .stDownloadButton > button,
        div[data-testid="stFormSubmitButton"] > button {
            border-radius: 12px;
            padding: 0.55rem 1rem;
            font-weight: 600;
        }
        .theme-card {
            border-radius: 18px;
            padding: 1rem 1.1rem;
            min-height: 112px;
        }
        .theme-card .label {
            font-size: 0.95rem;
            margin-bottom: 0.45rem;
        }
        .theme-card .value {
            font-size: 2rem;
            font-weight: 700;
            line-height: 1.1;
        }
        .theme-card .unit {
            font-size: 1rem;
            margin-left: 0.2rem;
        }
        .theme-card .sub {
            margin-top: 0.35rem;
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
            margin-bottom: 1rem;
        }

        /* ---------- Desktop / PC / iPad : white base ---------- */
        @media (min-width: 768px) {
            :root {
                color-scheme: light;
            }

            .stApp,
            [data-testid="stAppViewContainer"],
            [data-testid="stAppViewContainer"] > .main,
            [data-testid="stAppViewContainer"] > .main > div,
            [data-testid="stMainBlockContainer"],
            .main .block-container {
                background: #FFFFFF !important;
                color: #111111 !important;
            }

            [data-testid="stHeader"],
            [data-testid="stToolbar"],
            header {
                background: #FFFFFF !important;
            }

            section[data-testid="stSidebar"],
            [data-testid="stSidebar"] {
                background: #FFFFFF !important;
                border-right: 1px solid #E5E7EB;
            }

            section[data-testid="stSidebar"] *,
            [data-testid="stSidebar"] * {
                color: #111111 !important;
            }

            h1, h2, h3, h4, h5, h6,
            p, label, span, div, li, small,
            [data-testid="stMarkdownContainer"] *,
            [data-testid="stText"] {
                color: #111111 !important;
            }

            .section-sub,
            small,
            [data-testid="stCaptionContainer"] {
                color: #666666 !important;
            }

            [data-testid="stTabs"] button {
                color: #666666 !important;
                background: transparent !important;
            }
            [data-testid="stTabs"] button[aria-selected="true"] {
                color: #111111 !important;
                border-bottom: 2px solid #111111 !important;
            }

            /* input wrappers */
            [data-testid="stSelectbox"] > div,
            [data-testid="stDateInput"] > div,
            [data-testid="stNumberInput"] > div,
            [data-testid="stTextInput"] > div,
            [data-testid="stTextArea"] > div,
            [data-testid="stMultiSelect"] > div {
                background: #FFFFFF !important;
                border: 1px solid #D1D5DB !important;
                border-radius: 12px !important;
                color: #111111 !important;
            }

            /* BaseWeb controls */
            div[data-baseweb="input"],
            div[data-baseweb="input"] > div,
            div[data-baseweb="base-input"],
            div[data-baseweb="base-input"] > div,
            div[data-baseweb="textarea"],
            div[data-baseweb="textarea"] > div,
            div[data-baseweb="select"],
            div[data-baseweb="select"] > div,
            div[data-baseweb="popover"] > div {
                background: #FFFFFF !important;
                color: #111111 !important;
                border-color: #D1D5DB !important;
            }

            input,
            textarea,
            [data-testid="stDateInput"] input,
            [data-testid="stNumberInput"] input,
            [data-testid="stTextInput"] input,
            [data-testid="stTextArea"] textarea,
            div[data-baseweb="input"] input,
            div[data-baseweb="base-input"] input,
            div[data-baseweb="textarea"] textarea,
            div[data-baseweb="select"] input,
            div[data-baseweb="select"] span,
            div[data-baseweb="select"] div,
            div[data-baseweb="tag"] span {
                background: #FFFFFF !important;
                color: #111111 !important;
                -webkit-text-fill-color: #111111 !important;
                caret-color: #111111 !important;
            }

            input::placeholder,
            textarea::placeholder {
                color: #6B7280 !important;
                -webkit-text-fill-color: #6B7280 !important;
            }

            svg,
            div[data-baseweb="select"] svg,
            [data-testid="stDateInput"] svg {
                fill: #111111 !important;
                color: #111111 !important;
            }

            /* dropdown menu */
            div[role="listbox"],
            ul[role="listbox"],
            div[data-baseweb="menu"],
            div[data-baseweb="popover"] {
                background: #FFFFFF !important;
                border: 1px solid #D1D5DB !important;
            }

            div[role="option"],
            li[role="option"],
            div[data-baseweb="menu"] ul li {
                background: #FFFFFF !important;
                color: #111111 !important;
            }

            div[role="option"] *,
            li[role="option"] *,
            div[data-baseweb="menu"] ul li * {
                color: #111111 !important;
            }

            /* form labels and helpers */
            [data-testid="stForm"] *,
            [data-testid="stRadio"] *,
            [data-testid="stCheckbox"] * {
                color: #111111 !important;
            }

            /* buttons */
            .stButton > button,
            .stDownloadButton > button,
            div[data-testid="stFormSubmitButton"] > button {
                background: #111111 !important;
                color: #FFFFFF !important;
                border: 1px solid #111111 !important;
            }

            /* KPI cards */
            .theme-card {
                background: #F7F7F7 !important;
                border: 1px solid #E5E7EB !important;
                box-shadow: 0 3px 14px rgba(17, 17, 17, 0.05);
            }
            .theme-card .label,
            .theme-card .unit,
            .theme-card .value {
                color: #111111 !important;
            }
            .theme-card .sub {
                color: #666666 !important;
            }

            /* Dataframe / table */
            [data-testid="stTable"],
            [data-testid="stDataFrame"],
            [data-testid="stDataFrameResizable"],
            [data-testid="stTableGlideDataGrid"] {
                background: #FFFFFF !important;
                border: 1px solid #E5E7EB !important;
                border-radius: 16px;
                overflow: hidden;
                --gdg-bg-cell: #FFFFFF;
                --gdg-bg-cell-medium: #F8FAFC;
                --gdg-bg-header: #F3F4F6;
                --gdg-bg-header-has-focus: #E5E7EB;
                --gdg-border-color: #E5E7EB;
                --gdg-horizontal-border-color: #E5E7EB;
                --gdg-text-dark: #111111;
                --gdg-text-medium: #374151;
                --gdg-accent-color: #111111;
                --gdg-accent-fg: #FFFFFF;
                --gdg-header-font-style: 600 14px;
                --gdg-base-font-style: 500 14px;
                color: #111111 !important;
            }

            [data-testid="stTable"] *,
            [data-testid="stDataFrame"] *,
            [data-testid="stDataFrameResizable"] *,
            [data-testid="stTableGlideDataGrid"] *,
            .glide-data-grid,
            .glide-data-grid * {
                color: #111111 !important;
            }

            .glide-data-grid canvas,
            [data-testid="stDataFrame"] canvas,
            [data-testid="stDataFrameResizable"] canvas,
            [data-testid="stTableGlideDataGrid"] canvas {
                background: #FFFFFF !important;
            }

            [data-testid="stExpander"],
            [data-testid="stVerticalBlock"],
            [data-testid="stHorizontalBlock"] {
                background: transparent !important;
            }
        }

        /* ---------- Mobile : keep dark ---------- */
        @media (max-width: 767px) {
            .stApp {
                background: linear-gradient(180deg, #090d16 0%, #0b0f1a 100%);
                color: #F3F4F6;
            }
            h1, h2, h3, h4, h5, h6, p, label, span, div {
                color: #F3F4F6;
            }
            [data-testid="stTabs"] button {
                color: #cdd5df;
            }
            [data-testid="stTabs"] button[aria-selected="true"] {
                color: #ffffff;
                border-bottom: 2px solid #3B82F6;
            }
            [data-testid="stSelectbox"] > div,
            [data-testid="stDateInput"] > div,
            [data-testid="stNumberInput"] > div,
            [data-testid="stTextInput"] > div,
            [data-testid="stTextArea"] > div,
            [data-testid="stMultiSelect"] > div,
            div[data-baseweb="select"] > div,
            div[data-baseweb="input"] > div,
            div[data-baseweb="base-input"],
            div[data-baseweb="textarea"] > div {
                background: #12182a !important;
                border: 1px solid #232845 !important;
                border-radius: 12px;
                color: #F3F4F6 !important;
            }
            input, textarea,
            div[data-baseweb="select"] input,
            div[data-baseweb="input"] input,
            div[data-baseweb="base-input"] input,
            div[data-baseweb="textarea"] textarea,
            div[data-baseweb="select"] span,
            div[data-baseweb="select"] div {
                color: #F3F4F6 !important;
                -webkit-text-fill-color: #F3F4F6 !important;
            }
            .stButton > button, .stDownloadButton > button, div[data-testid="stFormSubmitButton"] > button {
                background: #2563eb;
                color: #fff;
                border: 0;
            }
            .theme-card {
                background: linear-gradient(180deg, rgba(21,26,45,0.96) 0%, rgba(15,19,34,0.96) 100%);
                border: 1px solid #232845;
                box-shadow: 0 6px 24px rgba(0,0,0,0.22);
            }
            .theme-card .label { color: #c3c9d4; }
            .theme-card .value { color: #f8fafc; }
            .theme-card .unit { color: #c3c9d4; }
            .theme-card .sub { color: #8ce99a; }
            .section-sub { color: #a8b0bf; }
            [data-testid="stDataFrame"],
            [data-testid="stTable"],
            [data-testid="stDataFrameResizable"],
            [data-testid="stTableGlideDataGrid"] {
                border: 1px solid #232845;
                border-radius: 16px;
                overflow: hidden;
            }
        }

        @media (max-width: 768px) {
            .block-container { padding-left: 0.8rem; padding-right: 0.8rem; }
            .theme-card { min-height: 100px; padding: 0.9rem; }
            .theme-card .value { font-size: 1.7rem; }
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
                <div class="theme-card">
                    <div class="label">{label}</div>
                    <div><span class="value">{value}</span><span class="unit">{unit}</span></div>
                    {f'<div class="sub">{sub}</div>' if sub else '<div class="sub">&nbsp;</div>'}
                </div>
                """,
                unsafe_allow_html=True,
            )
