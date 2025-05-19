import streamlit as st 
import pandas as pd

from registration import registration_page
from login import login_page
from logout_app import logout
from require_login import require_login
# from forgot import forgot_password_page 
from db import get_user_collection 


from dashboard import dashboard_page 
from anomalies import anomalies_page 
from forecasting import forecasting_page 
from analytics import analytics_page 
from reports import reports_page 
from upload import upload_and_analyze
from alerts_page import alerts_page 
from preferences import preferences_page 
from communications import communications_page 
from recommendations import recommendations_page
from about import about_page 
from user_management import user_management_page 




import plotly.express as px 
from prophet import Prophet 
from bson import ObjectId
import io 
import sys, os
sys.path.append(os.path.abspath("."))


if "user" not in st.session_state:
    st.session_state.user = None


if "next_page" not in st.session_state:
    st.session_state.next_page = None

st.set_page_config(
    page_title="EMADS Dashboard",
    layout="wide",
    page_icon="assets/energy_logo.png",
    initial_sidebar_state="collapsed"
)

st.markdown(
        """
        <style>
        .centered-image {
            display: flex;
            justify-content: center;
        }
        </style>
        """,
        unsafe_allow_html=True
             )

def main():    
    st.sidebar.title("Navigation")


    # if registration just happened, force show login 
    if st.session_state.next_page == "Login":
        st.session_state.next_page = None
        login_page()
        return 
    """-------------------------------------"""
    # check for a reset token in the URL
    
    """-------------------------------------"""
    if not st.session_state.user:
        choice = st.sidebar.radio("Go to", ["Login", "Register"])
        if choice == "Login":
            login_page()
        else:
            registration_page()
        return
    else:
        # Logged in: show role-based menu
        role = st.session_state.user["role"]
        pages = ["Dashboard", "Reports", "Analytics", "Recommendations", "Preferences", "About"]
        if role in ("admin", "manager"):
            pages += ["Forecasting", "Anomalies","Upload Dataset","Alerts","User Management","Communications"]
        selection = st.sidebar.radio("Go to", pages)
        st.sidebar.button("Logout", on_click = logout)

        #Dispatch
        if selection == "Dashboard":
            dashboard_page()
        elif selection == "Anomalies":
            anomalies_page()
        elif selection == "Forecasting":
            forecasting_page()
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

