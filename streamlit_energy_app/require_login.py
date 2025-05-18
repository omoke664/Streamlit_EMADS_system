import streamlit as st 

def require_login():
    if not st.session_state.user:
        st.warning("⚠️ Please log in or register to access this page.")
        st.stop()
