
import streamlit as st

def set_pixel_background():
    st.markdown("""
        <style>
        .stApp {
            background-image: url('https://cdn.openai.com/chat-assets/user-uploads/file_00000000787061f9b295d47156b5177a/A_pixel_art_screenshot-style_monthly_tracking_inte.png');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            background-repeat: no-repeat;
        }
        </style>
    """, unsafe_allow_html=True)
