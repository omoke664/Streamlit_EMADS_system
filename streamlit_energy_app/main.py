import streamlit as st 

# Set page config - must be the first Streamlit command
st.set_page_config(
    page_title="EMADS - Energy Monitoring & Anomaly Detection System",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/emads',
        'Report a bug': 'https://github.com/yourusername/emads/issues',
        'About': '# EMADS - Energy Monitoring & Anomaly Detection System'
    }
)

import os
from dotenv import load_dotenv
from db import get_mongo_client, get_db
import pandas as pd
import asyncio
import torch
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from db import get_energy_collection, get_alerts_collection, get_user_collection, get_communications_collection
from email_utils import send_email
from require_login import require_login
from anomalies import anomalies_page
from dashboard import dashboard_page
from alerts_page import alerts_page
from preferences import preferences_page
from login import login_page
from registration import registration_page
from forgot import forgot_password_page
from reset_password import reset_password_page
from user_management import user_management_page
from about import about_page

# Initialize PyTorch
torch.set_num_threads(1)  # Limit PyTorch to single thread to avoid conflicts

# Set up event loop
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from registration import registration_page
from logout_app import logout
from forgot import forgot_password_page
from reset_password import reset_password_page
from db import get_user_collection 

from dashboard import dashboard_page 
from anomalies import anomalies_page 
from analytics import analytics_page 
from reports import reports_page 
from upload import upload_and_analyze
from preferences import preferences_page 
from communications import communications_page 
from recommendations import recommendations_page
from lstm_network import lstm_network_page
from prophet_forecast import prophet_forecast_page

import io 
import sys, os
sys.path.append(os.path.abspath("."))

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'role' not in st.session_state:
    st.session_state.role = None
if 'page' not in st.session_state:
    st.session_state.page = 'login'
if 'next_page' not in st.session_state:
    st.session_state.next_page = None
if 'user' not in st.session_state:
    st.session_state.user = None

# Load environment variables
load_dotenv()

# Initialize MongoDB connection
get_mongo_client()

def main():    
    st.sidebar.title("Navigation")

    # Check for reset token in URL
    if "token" in st.query_params:
        reset_password_page()
        return

    # Handle navigation based on session state
    if st.session_state.next_page:
        page = st.session_state.next_page
        st.session_state.next_page = None
        if page == "Login":
            login_page()
        elif page == "Registration":
            registration_page()
        elif page == "Forgot Password":
            forgot_password_page()
        return

    if not st.session_state.user:
        choice = st.sidebar.radio("Go to", ["Login", "Register", "Forgot Password"])
        if choice == "Login":
            login_page()
        elif choice == "Register":
            registration_page()
        else:
            forgot_password_page()
        return
    else:
        # Logged in: show role-based menu
        role = st.session_state.user["role"]
        pages = ["Dashboard", "Reports", "Analytics", "Recommendations", "Preferences", "About"]
        if role in ("admin", "manager"):
            pages += ["Anomalies", "LSTM Network", "Prophet Forecast", "Upload Dataset", "Alerts", "User Management", "Communications"]
        selection = st.sidebar.radio("Go to", pages)
        st.sidebar.button("Logout", on_click = logout)

        #Dispatch
        if selection == "Dashboard":
            dashboard_page()
        elif selection == "Anomalies":
            anomalies_page()
        elif selection == "LSTM Network":
            lstm_network_page()
        elif selection == "Prophet Forecast":
            prophet_forecast_page()
        elif selection == "Upload Dataset":
            upload_and_analyze()
        elif selection == "Analytics":
            analytics_page()
        elif selection == "Reports":
            reports_page()
        elif selection == "Recommendations":
            recommendations_page()
        elif selection == "Alerts":
            alerts_page()
        elif selection == "Preferences":
            preferences_page()
        elif selection == "About":
            about_page()
        elif selection == "User Management":
            user_management_page()
        elif selection == "Communications":
            communications_page()

if __name__ == "__main__":
    main()

