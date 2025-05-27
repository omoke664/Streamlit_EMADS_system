import streamlit as st
from require_login import require_login 
from db import get_user_collection
import pandas as pd
import os

def preferences_page():
    require_login()
    
    # Custom CSS
    st.markdown("""
        <style>
        .pref-card {
            background-color: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            margin-bottom: 1rem;
        }
        .pref-header {
            color: #333;
            font-size: 1.2rem;
            font-weight: bold;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .pref-description {
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }
        .stButton>button {
            width: 100%;
            background-color: #4CAF50;
            color: white;
            padding: 0.5rem;
            border-radius: 5px;
            border: none;
            font-weight: bold;
            margin-top: 1rem;
        }
        .stButton>button:hover {
            background-color: #45a049;
        }
        .notification-preview {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 5px;
            margin-top: 0.5rem;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("User Preferences")
    
    users = get_user_collection()
    username = st.session_state.user["username"]
    user_doc = users.find_one({"username": username})
    prefs = user_doc.get("preferences", {})

    # Default values
    default_start = pd.to_datetime(prefs.get("date_range", [None, None])[0]) or pd.Timestamp.now() - pd.Timedelta(days=7)
    default_end = pd.to_datetime(prefs.get("date_range", [None, None])[1]) or pd.Timestamp.now()
    default_agg = prefs.get("aggregation", "Daily")
    default_thresh = prefs.get("anomaly_threshold", 1.0)
    default_notifications = prefs.get("notifications", {
        "email": True,
        "dashboard": True,
        "alerts": True,
        "reports": False
    })
    default_language = prefs.get("language", "English")
    default_timezone = prefs.get("timezone", "UTC")
    default_chart_type = prefs.get("default_chart_type", "Line")

    with st.form("preferences_form"):
        st.markdown('<div class="pref-header">Data Visualization</div>', unsafe_allow_html=True)
        chart_type = st.selectbox(
            "Default Chart Type",
            ["Line", "Bar", "Area"],
            index=["Line", "Bar", "Area"].index(prefs.get("chart_type", "Line"))
        )
        
        time_range = st.selectbox(
            "Default Time Range",
            ["Last 24 hours", "Last 7 days", "Last 30 days", "Last 90 days", "All time"],
            index=["Last 24 hours", "Last 7 days", "Last 30 days", "Last 90 days", "All time"].index(prefs.get("time_range", "All time"))
        )
        
        st.markdown('<div class="pref-header">Notification Settings</div>', unsafe_allow_html=True)
        email_notifications = st.checkbox(
            "Email Notifications",
            value=prefs.get("email_notifications", True)
        )
        
        dashboard_notifications = st.checkbox(
            "Dashboard Notifications",
            value=prefs.get("dashboard_notifications", True)
        )
        
        alert_notifications = st.checkbox(
            "Alert Notifications",
            value=prefs.get("alert_notifications", True)
        )
        
        report_notifications = st.checkbox(
            "Weekly Report Notifications",
            value=prefs.get("report_notifications", True)
        )
        
        st.markdown('<div class="pref-header">Regional Settings</div>', unsafe_allow_html=True)
        timezone = st.selectbox(
            "Timezone",
            ["UTC", "EST", "CST", "PST"],
            index=["UTC", "EST", "CST", "PST"].index(prefs.get("timezone", "UTC"))
        )
        
        date_format = st.selectbox(
            "Date Format",
            ["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"],
            index=["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"].index(prefs.get("date_format", "YYYY-MM-DD"))
        )
        
        submitted = st.form_submit_button("Save Preferences")
        
        if submitted:
            new_prefs = {
                "chart_type": chart_type,
                "time_range": time_range,
                "email_notifications": email_notifications,
                "dashboard_notifications": dashboard_notifications,
                "alert_notifications": alert_notifications,
                "report_notifications": report_notifications,
                "timezone": timezone,
                "date_format": date_format
            }
            
            users.update_one(
                {"username": username},
                {"$set": {
                    "preferences": new_prefs
                }}
            )
            
            # Update session state
            st.session_state.user["preferences"] = new_prefs
            
            st.success("Preferences updated successfully!")
            
            st.info("Preview of your changes:")
            st.json(new_prefs)