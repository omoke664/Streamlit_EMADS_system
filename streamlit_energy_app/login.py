import streamlit as st 
from db import get_user_collection, get_communications_collection
from verify import verify_password
import os
from utils.email_utils import send_welcome_email
import time
from datetime import datetime

def login_page():
    # Welcome message
    st.markdown("<h1 style='text-align: center;'>Welcome Back to EMADS</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Your Energy Monitoring & Anomaly Detection System</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Please Log In to Continue</p>", unsafe_allow_html=True)

    # Create a centered container for the form
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        # Login form
        with st.form("login_form", clear_on_submit=True):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
        
        # Navigation guidance
        st.markdown("""
        <div style='text-align: center; margin-top: 20px; color: #666;'>
            <p>Don't have an account? Use the sidebar navigation to <strong>Register</strong>.</p>
            <p>Forgot your password? Use the sidebar navigation to <strong>Reset Password</strong>.</p>
        </div>
        """, unsafe_allow_html=True)

    if submitted:
        if not username or not password:
            st.error("Please enter both username and password.")
            return
        
        users = get_user_collection()
        communications = get_communications_collection()
        user = users.find_one({"username": username})
        
        if not user:
            st.error("Invalid username or password.")
            return
            
        if not verify_password(password, user["password"]):
            st.error("Invalid username or password.")
            return
            
        # Check if user has a pending role request
        has_pending_request = user.get("requested_role") in ["manager", "admin"] and user.get("status") == "pending"
        
        if has_pending_request:
            st.info("Your request for elevated access is pending approval. You will be logged in as a resident until your request is reviewed.")
        
        # Create welcome back message
        welcome_message = {
            "username": username,
            "title": "Welcome Back!",
            "message": f"""
            Welcome back, {user['first_name']}!

            You have successfully logged in to EMADS.
            Current Role: {user['role']}
            {f'You have requested to become a {user["requested_role"]}. This request is pending approval.' if has_pending_request else ''}

            You can now access all features available to your role.
            If you have any questions or need assistance, please contact an administrator.

            Best regards,
            The EMADS Team
            """,
            "type": "system_message",
            "timestamp": datetime.now(),
            "read": False
        }
        communications.insert_one(welcome_message)
        
        # Set session state - always use current role (resident) for pending requests
        st.session_state["user"] = {
            "username": user["username"],
            "role": user["role"],  # This will be "resident" for pending requests
            "first_name": user["first_name"],
            "last_name": user["last_name"]
        }
        
        st.success(f"Welcome back, {user['first_name']}! You're now logged in.")
        time.sleep(2)
        st.rerun()
        