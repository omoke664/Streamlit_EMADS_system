import streamlit as st 
from require_login import require_login
from db import load_energy_data 
from anomaly_detection.anomaly_detector import AnomalyDetector

import io


def reports_page():
    require_login()
    st.title("📄 Reports")

    # Load data
    df = load_energy_data()
    if df.empty:
        st.warning("⚠️ No energy data available.")
        return

    # Date‐range filter
    min_date = df["timestamp"].dt.date.min()
    max_date = df["timestamp"].dt.date.max()
    start_date, end_date = st.date_input(
        "Select date range",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
    mask = (df["timestamp"].dt.date >= start_date) & (df["timestamp"].dt.date <= end_date)
    df_filtered = df.loc[mask]

    st.subheader("Download Energy Data")
    csv_buffer = io.StringIO()
    df_filtered.to_csv(csv_buffer, index=False)
    st.download_button(
        label="Download CSV",
        data=csv_buffer.getvalue(),
        file_name=f"energy_data_{start_date}_{end_date}.csv",
        mime="text/csv"
    )

    # Also include anomalies
    st.subheader("Download Anomaly Report")
    detector = AnomalyDetector(contamination=0.01)
    df_flagged = detector.fit_detect(df, feature_cols=["energy_kwh"])
    anomalies = df_flagged[df_flagged["is_anomaly"]]

    if anomalies.empty:
        st.info("No anomalies detected in the full dataset.")
    else:
        csv_buffer2 = io.StringIO()
        anomalies.to_csv(csv_buffer2, index=False)
        st.download_button(
            label="Download Anomalies CSV",
            data=csv_buffer2.getvalue(),
            file_name=f"anomalies_{start_date}_{end_date}.csv",
            mime="text/csv"
        )
