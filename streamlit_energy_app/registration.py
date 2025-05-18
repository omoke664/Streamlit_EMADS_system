import streamlit as st
import pandas as pd
from db import get_user_collection, hash_password



def registration_page():
    st.markdown("<center>Welcome To The Energy Monitoring and Anomaly Detection System.</center>", unsafe_allow_html=True)
    st.write("🔒Register")
    users = get_user_collection()



    with st.form("reg_form", clear_on_submit = True):
        st.subheader("Create Account")
        username = st.text_input("Username")
        email = st.text_input("Email")
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        password = st.text_input("Password", type = "password")
        requested = st.selectbox("Role", ["admin", "manager", "resident"])
        submitted = st.form_submit_button("Create Account")


    if submitted:
        if users.find_one({"username": username}):
            st.error("❌ Username already exists. Log in instead.")
        if not username or not email or not password:
            st.error("❌ Please fill in all fields.")
        elif users.find_one({"username":username}):
            st.error("❌ Username already exists.")
        elif users.find_one({"email":email}):
            st.error("❌ An account with that email already exists.")
        else:
            users.insert_one({
                "username": username,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "created_at": pd.Timestamp.now(),
                "password": hash_password(password),
                "role": "resident", # persitent role until approved
                "requested_role": requested, # role requested by user
                "approved": requested == "resident",
            })
            if requested == "resident":
                st.success("✅ Account created!. You may now log in.")
            else:
                st.info("🕑 Your request for elevated access is pending admin approval.")

            st.rerun()

