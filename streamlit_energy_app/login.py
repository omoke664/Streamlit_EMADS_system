
import streamlit as st 
from db import get_user_collection
from verify import verify_password

def login_page():
    st.markdown("<center>Welcome Back to the Energy Monitoring and Anomaly Detection System.</center>", unsafe_allow_html=True)
    st.write("🔑 Login")
    users = get_user_collection()

    with st.form("login_form", clear_on_submit=True):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log In")

    if submitted:
        user = users.find_one({"username": username})
       
        if not user:
            st.error("❌ Invalid username or password.")
            return 
        

        # ←— DISABLED CHECK 
        # Only block if they requested manager/admin *and* haven't been approved
        if user.get("requested_role") in ("manager", "admin") and not user.get("approved", False):
            st.error("🚫 Your request for elevated access is still pending admin approval.")
            return

        # Everyone else (residents, or pre-existing users) can log in as long as password matches:
        if verify_password(password, user["password"]):
            user_obj = {"username": user["username"], "role": user["role"]}
            # 1) write the JWT into a cookie
           #  login_user(user_obj)
            # 2) also put it into session_state so the rest of this run picks it up
            st.session_state.user = user_obj
            st.success(f"✅ Welcome back, {username}!")
            st.rerun()

        else:
            st.error("❌ Invalid username or password.")
        