
import streamlit as st 
from db import get_alerts_collection 
from require_login import require_login 
import pandas as pd 




def alerts_page():
    require_login()
    st.title("🚨 Active Alerts")

    # First run the checker (so new alerts get created & emailed)
    from alerts import check_consecutive_anomalies
    check_consecutive_anomalies(threshold=2)

    # Load alerts
    alerts = get_alerts_collection()
    docs   = list(alerts.find().sort("detected_at", -1))

    if not docs:
        st.info("No active alerts.")
        return

    # Display a table of alerts
    df_alerts = pd.DataFrame(docs)
    df_alerts["detected_at"] = df_alerts["detected_at"].dt.strftime("%Y-%m-%d %H:%M:%S")
    st.dataframe(
        df_alerts[["sensor_id","detected_at","type","count","message"]],
        use_container_width=True
    )