import smtplib
from email.message import EmailMessage
from auth_utils import generate_reset_token
import streamlit as st 
from db import get_user_collection 
import os 
import pandas as pd
from verify import hash_password
from utils.email_utils import validate_email, send_reset_email
import secrets
import logging
import datetime
import time

# Get logger
logger = logging.getLogger(__name__)

def forgot_password_page():
    # Welcome message
    st.markdown("<h1 style='text-align: center;'>Forgot Password</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Enter your email address to reset your password</p>", unsafe_allow_html=True)

    # Create a centered container for the form
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        # Reset password form
        with st.form("forgot_password_form", clear_on_submit=True):
            email = st.text_input("Email")
            submitted = st.form_submit_button("Send Reset Link")

        # Navigation guidance
        st.markdown("""
        <div style='text-align: center; margin-top: 20px; color: #666;'>
            <p>Remember your password? Use the sidebar navigation to <strong>Login</strong>.</p>
            <p>Don't have an account? Use the sidebar navigation to <strong>Register</strong>.</p>
        </div>
        """, unsafe_allow_html=True)

    if submitted:
        if not email:
            st.error("Please enter your email address.")
            return
        
        if not validate_email(email):
            st.error("Please enter a valid email address.")
            return
        
        users = get_user_collection()
        user = users.find_one({"email": email})
        
        if not user:
            st.error("No account found with that email address.")
            return
        
        try:
            token = generate_reset_token()
            users.update_one(
                {"email": email},
                {"$set": {
                    "reset_token": token,
                    "reset_token_expires": datetime.datetime.now() + datetime.timedelta(hours=1)
                }}
            )
            
            send_reset_email(email, token)
            st.success("Password reset link has been sent to your email.")
            st.info("Please check your email for the reset link. If you don't see it, check your spam folder.")
            time.sleep(3)
            st.session_state.next_page = "Login"
            st.rerun()
        except Exception as e:
            logger.error(f"Error sending reset email: {str(e)}")
            st.error("Failed to send reset email. Please try again later.")
