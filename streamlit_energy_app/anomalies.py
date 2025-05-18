
import streamlit as st
from require_login import require_login
from db import load_energy_data
from anomaly_detection.anomaly_detector import AnomalyDetector



def anomalies_page():
    require_login()
    st.title("📊 Anomalies")
    # TODO: highlight anomalies, table, metrics

    # 1) Load energy data
    df = load_energy_data()
    if df.empty:
        st.warning("No energy data available")
        return
    
    # 2) Run anomaly detection
    detector = AnomalyDetector(contamination = 0.01)
    df_flagged = detector.fit_detect(df, feature_cols =["energy_kwh"])

    #3) Computer Summary metrics
    total = len(df_flagged)
    anomalies = df_flagged["is_anomaly"].sum()
    rate = anomalies / total if total else 0.0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Records", f"{total}")
    col2.metric("Anomalies", f"{anomalies}")
    col3.metric("Anomaly Rate", f"{rate:.2%}")


    #4) Plot time series with anomaly markers
    st.subheader("Energy Consumption with Anomalies")

    # Mark normal vs. anomaly values
    df_flagged["Anomaly"] = df_flagged["energy_kwh"].where(df_flagged["is_anomaly"], None)

    # Create a multi-series DataFrame for the chart
    chart_df = df_flagged.set_index("timestamp")[["energy_kwh", "Anomaly"]]

    st.line_chart(chart_df, use_container_width=True)

    st.subheader("Anomaly Details")
    st.dataframe(
        df_flagged[df_flagged["is_anomaly"]]
        [["timestamp", "energy_kwh", "anomaly_score"]]
        .sort_values("timestamp")
        .reset_index(drop = True),
        use_container_width=True,
    )
