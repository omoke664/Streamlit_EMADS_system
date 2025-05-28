import streamlit as st
from db import get_user_collection, get_communications_collection
from verify import hash_password
from datetime import datetime
import time
import logging
import os
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def registration_page():
    # Initialize session state for form data if not exists
    if 'reg_form_data' not in st.session_state:
        st.session_state.reg_form_data = {
            'first_name': '',
            'last_name': '',
            'email': '',
            'username': '',
            'role': 'resident'
        }

    # Check if environment variables are loaded
    if not os.getenv('MONGO_URI'):
        st.error("Database connection not configured. Please ensure .env file exists with MONGO_URI.")
        return

    st.markdown("<h1 style='text-align: center;'>Registration</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Please fill out the form below to create your account.<br>All fields are required.</p>", unsafe_allow_html=True)
    
    # Get collections
    try:
        users = get_user_collection()
        communications = get_communications_collection()
        logger.info("Successfully connected to database collections")
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        st.error(f"Failed to connect to database: {str(e)}. Please ensure MongoDB is running and .env file is configured correctly.")
        return

    # Create a centered container for the form
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        # Registration form
        with st.form("registration_form", clear_on_submit=True):
            # Personal Information
            st.markdown("<h3 style='text-align: center;'>Personal Information</h3>", unsafe_allow_html=True)
            first_name = st.text_input("First Name", value=st.session_state.reg_form_data['first_name'])
            last_name = st.text_input("Last Name", value=st.session_state.reg_form_data['last_name'])
            email = st.text_input("Email", value=st.session_state.reg_form_data['email'])
            
            # Account Information
            st.markdown("<h3 style='text-align: center;'>Account Information</h3>", unsafe_allow_html=True)
            username = st.text_input("Username", value=st.session_state.reg_form_data['username'])
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            # Role Selection
            st.markdown("<h3 style='text-align: center;'>Role Selection</h3>", unsafe_allow_html=True)
            role = st.selectbox(
                "Select your role",
                ["resident", "manager", "admin"],
                index=["resident", "manager", "admin"].index(st.session_state.reg_form_data['role']),
                help="Residents can view their own data. Managers and Admins have additional privileges."
            )
            
            # Submit button
            submitted = st.form_submit_button("Create Account")
            
            if submitted:
                # Update session state with form data
                st.session_state.reg_form_data.update({
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'username': username,
                    'role': role
                })
                
                logger.info(f"Registration attempt for username: {username}")
                
                # Validate inputs
                if not all([first_name, last_name, email, username, password, confirm_password]):
                    logger.warning("Missing required fields")
                    st.error("Please fill in all fields.")
                    return
                
                if password != confirm_password:
                    logger.warning("Passwords do not match")
                    st.error("Passwords do not match.")
                    return
                
                try:
                    # Check if username or email already exists
                    existing_user = users.find_one({"$or": [{"username": username}, {"email": email}]})
                    if existing_user:
                        logger.warning(f"Username or email already exists: {username}")
                        st.error("Username or email already exists.")
                        return
                    
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
                    logger.info(f"Attempting to insert user: {username}")
                    result = users.insert_one(user_doc)
                    
                    if result.inserted_id:
                        logger.info(f"Successfully created user: {username}")
                        
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
                        logger.info(f"Created welcome message for user: {username}")
                        
                        # Clear form data from session state
                        st.session_state.reg_form_data = {
                            'first_name': '',
                            'last_name': '',
                            'email': '',
                            'username': '',
                            'role': 'resident'
                        }
                        
                        # Show success message
                        st.success("Account created successfully!")
                        st.info("Please wait while we redirect you to the login page...")
                        
                        # Wait a moment to show the success message
                        time.sleep(2)
                        
                        # Redirect to login page
                        st.session_state.page = "Login"
                        st.rerun()
                    else:
                        logger.error(f"Failed to create user: {username}")
                        st.error("Failed to create account. Please try again.")
                    
                except Exception as e:
                    logger.error(f"Error during registration: {str(e)}")
                    st.error(f"An error occurred during registration: {str(e)}")
                    return

        # Navigation guidance
        st.markdown("""
        <div style='text-align: center; margin-top: 20px; color: #666;'>
            <p>Already have an account? Use the sidebar navigation to <strong>Login</strong>.</p>
            <p>Forgot your password? Use the sidebar navigation to <strong>Reset Password</strong>.</p>
        </div>
        """, unsafe_allow_html=True)

