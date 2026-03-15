
import streamlit as st

def apply_dark_theme():
    st.markdown(
    '''
    <style>
    .stApp{
        background-color:#0B0F1A;
        color:#F3F4F6;
    }
    .card{
        background:#151A2D;
        padding:18px;
        border-radius:12px;
        border:1px solid #232845;
        margin-bottom:10px;
    }
    .kpi{
        font-size:28px;
        font-weight:700;
    }
    .kpi-label{
        font-size:14px;
        color:#9CA3AF;
    }
    </style>
    ''',
    unsafe_allow_html=True
    )

def kpi(label,value):
    st.markdown(
        f'''
        <div class="card">
        <div class="kpi-label">{label}</div>
        <div class="kpi">{value}</div>
        </div>
        ''',
        unsafe_allow_html=True
    )
