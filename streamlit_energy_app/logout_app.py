import streamlit as st 



def logout():
    #logout_user()
    st.session_state.user = None
    st.session_state.next_page = "Login"
    st.success("✅ You have been logged out.")