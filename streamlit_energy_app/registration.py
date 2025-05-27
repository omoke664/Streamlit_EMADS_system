import streamlit as st
from db import get_user_collection, get_communications_collection
from verify import hash_password
from datetime import datetime
import time

def registration_page():
    st.markdown("<h1 style='text-align: center;'>Registration</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Please fill out the form below to create your account.<br>All fields are required.</p>", unsafe_allow_html=True)
    
    # Get collections
    users = get_user_collection()
    communications = get_communications_collection()

    # Create a centered container for the form
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        # Registration form
        with st.form("registration_form", clear_on_submit=True):
            # Personal Information
            st.markdown("<h3 style='text-align: center;'>Personal Information</h3>", unsafe_allow_html=True)
            first_name = st.text_input("First Name")
            last_name = st.text_input("Last Name")
            email = st.text_input("Email")
            
            # Account Information
            st.markdown("<h3 style='text-align: center;'>Account Information</h3>", unsafe_allow_html=True)
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            # Role Selection
            st.markdown("<h3 style='text-align: center;'>Role Selection</h3>", unsafe_allow_html=True)
            role = st.selectbox(
                "Select your role",
                ["resident", "manager", "admin"],
                help="Residents can view their own data. Managers and Admins have additional privileges."
            )
            
            # Submit button
            submitted = st.form_submit_button("Create Account")
            
            if submitted:
                # Validate inputs
                if not all([first_name, last_name, email, username, password, confirm_password]):
                    st.error("Please fill in all fields.")
                    return
                
                if password != confirm_password:
                    st.error("Passwords do not match.")
                    return
                
                # Check if username or email already exists
                if users.find_one({"$or": [{"username": username}, {"email": email}]}):
                    st.error("Username or email already exists.")
                    return
                
                try:
                    # Create user document
                    user_doc = {
                        "username": username,
                        "email": email,
                        "first_name": first_name,
                        "last_name": last_name,
                        "password": hash_password(password),
                        "role": "resident",  # Always start as resident
                        "created_at": datetime.now(),
                        "status": "active",
                        "disabled": False,
                        "preferences": {
                            "notifications": {
                                "alerts": True,
                                "reports": True
                            }
                        }
                    }
                    
                    # If requesting admin/manager role, set status to pending
                    if role in ["admin", "manager"]:
                        user_doc["status"] = "pending"
                        user_doc["requested_role"] = role
                    
                    # Insert user
                    result = users.insert_one(user_doc)
                    
                    if result.inserted_id:
                        # Create welcome message
                        welcome_message = {
                            "username": username,
                            "title": "Welcome to EMADS!",
                            "message": f"""
                            Welcome to the Energy Management and Anomaly Detection System (EMADS)!

                            Your account has been created successfully.
                            You can now log in to access the system.
                            """,
                            "type": "system_message",
                            "timestamp": datetime.now(),
                            "read": False
                        }
                        
                        # Add role request notification if applicable
                        if role in ["admin", "manager"]:
                            welcome_message["message"] += f"""
                            
                            You have requested the role of {role}. Your request is pending approval.
                            You will be notified once your request is reviewed.
                            You can currently access the system as a resident.
                            """
                            
                            # Notify existing admins and managers
                            for admin in users.find({"role": {"$in": ["admin", "manager"]}}):
                                notification = {
                                    "username": admin["username"],
                                    "title": "New Role Request",
                                    "message": f"""
                                    A new role request has been submitted:
                                    
                                    User: {first_name} {last_name} ({username})
                                    Requested Role: {role}
                                    Email: {email}
                                    
                                    Please review this request in the User Management section.
                                    """,
                                    "type": "role_request",
                                    "timestamp": datetime.now(),
                                    "read": False
                                }
                                communications.insert_one(notification)
                        
                        # Insert welcome message
                        communications.insert_one(welcome_message)
                        
                        # Show success message
                        st.success("Account created successfully!")
                        st.info("Please wait while we redirect you to the login page...")
                        
                        # Wait a moment to show the success message
                        time.sleep(2)
                        
                        # Redirect to login page
                        st.session_state.next_page = "Login"
                        st.rerun()
                    else:
                        st.error("Failed to create account. Please try again.")
                    
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    return

