
import streamlit as st
from require_login import require_login 
from db import get_user_collection
import pandas as pd 




def preferences_page():
    require_login()
    st.title("⚙️ User Preferences")

    users = get_user_collection()
    username = st.session_state.user["username"]

    # Fetch current user doc
    user_doc = users.find_one({"username": username})
    prefs = user_doc.get("preferences", {})

    # Default fallback values
    default_start = pd.to_datetime(prefs.get("date_range", [None, None])[0]) or pd.Timestamp.now() - pd.Timedelta(days=7)
    default_end = pd.to_datetime(prefs.get("date_range", [None, None])[1]) or pd.Timestamp.now()
    default_agg = prefs.get("aggregation", "Daily")
    default_thresh = prefs.get("anomaly_threshold", 1.0)

    # Form
    with st.form("preferences_form"):
        st.subheader("Date Range")
        date_range = st.date_input("Default Date Range", [default_start.date(), default_end.date()])

        st.subheader("Aggregation Level")
        aggregation = st.selectbox("Default Aggregation", ["Daily", "Weekly", "Monthly"], index=["Daily", "Weekly", "Monthly"].index(default_agg))

        st.subheader("Anomaly Detection")
        threshold = st.slider("Default Anomaly Threshold (%)", 0.1, 10.0, float(default_thresh), step=0.1)

        submitted = st.form_submit_button("Save Preferences")

    if submitted:
        users.update_one(
            {"username": username},
            {"$set": {
                "preferences": {
                    "date_range": [str(date_range[0]), str(date_range[1])],
                    "aggregation": aggregation,
                    "anomaly_threshold": float(threshold)
                }
            }}
        )
        st.success("✅ Preferences updated!")
        st.session_state.user["preferences"] = {
            "date_range": [str(date_range[0]), str(date_range[1])],
            "aggregation": aggregation,
            "anomaly_threshold": float(threshold)
        }