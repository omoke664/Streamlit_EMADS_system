import streamlit as st
import pandas as pd
from db import get_user_collection
from verify import hash_password
import os
import time

def reset_password_page():
    # Get token from URL parameters
    token = st.query_params.get("token", None)
    
    if not token:
        st.error("Invalid or missing reset token.")
        if st.button("Return to Login"):
            st.session_state.next_page = "Login"
            st.rerun()
        return

    # Welcome message
    st.markdown("Reset Your Password")
    st.markdown("Enter your new password below")

    # Reset password form
    with st.form("reset_password_form", clear_on_submit=True):
        password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submitted = st.form_submit_button("Reset Password")

    if submitted:
        if not password or not confirm_password:
            st.error("Please enter both password fields.")
            return
        
        if password != confirm_password:
            st.error("Passwords do not match.")
            return
        
        users = get_user_collection()
        user = users.find_one({
            "reset_token": token,
            "reset_token_expires": {"$gt": pd.Timestamp.now()}
        })
        
        if not user:
            st.error("Invalid or expired reset token.")
            return
        
        # Update password
        hashed_password = hash_password(password)
        users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {"password": hashed_password},
                "$unset": {"reset_token": "", "reset_token_expires": ""}
            }
        )
        
        st.success("Password has been reset successfully!")
        st.info("You can now log in with your new password.")
        time.sleep(2)
        st.session_state.next_page = "Login"
        st.rerun() 