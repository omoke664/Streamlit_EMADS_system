import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.express as px

MODEL_PATH = "models/isolation_forest_model.joblib"


def upload_and_analyze():
    st.markdown("## 📂 Upload Your Own Dataset for Anomaly Analysis")
    uploaded = st.file_uploader(
        label="Upload a CSV with at least `timestamp` & `energy_kwh` columns",
        type="csv",
    )
    if not uploaded:
        return

    # 1) Read user CSV
    try:
        user_df = pd.read_csv(uploaded, parse_dates=["timestamp"])
    except Exception as e:
        st.error(f"Failed to read CSV: {e}")
        return

    # 2) Ensure required columns
    if not {"timestamp", "energy_kwh"}.issubset(user_df.columns):
        st.error("CSV must contain `timestamp` and `energy_kwh` columns.")
        return

    # 3) Load model
    try:
        if_model = joblib.load(MODEL_PATH)
    except FileNotFoundError:
        st.error(f"Model file not found at {MODEL_PATH}")
        return

    # 4) Predict anomalies
    X = user_df[["energy_kwh"]]
    user_df["anomaly_flag"]  = if_model.predict(X) == -1
    user_df["anomaly_score"] = if_model.decision_function(X)

    # 5) Summary metrics
    total     = len(user_df)
    anomalies = user_df["anomaly_flag"].sum()
    rate      = anomalies / total if total else 0.0

    # Longest consecutive anomalies
    runs       = (user_df["anomaly_flag"] != user_df["anomaly_flag"].shift()).cumsum()
    consec_sum = user_df.groupby(runs)["anomaly_flag"].sum()
    longest_run = int(consec_sum.max()) if not consec_sum.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Rows", f"{total}")
    c2.metric("Anomalies", f"{anomalies}")
    c3.metric("Anomaly Rate", f"{rate:.2%}")
    c4.metric("Max Consecutive", f"{longest_run}")

    # 6) Time‑series chart
    st.subheader("Your Data: Energy & Anomalies")
    fig = px.line(user_df, x="timestamp", y="energy_kwh", title="Uploaded Data")
    fig.add_scatter(
        x=user_df.loc[user_df["anomaly_flag"], "timestamp"],
        y=user_df.loc[user_df["anomaly_flag"], "energy_kwh"],
        mode="markers",
        marker=dict(color="red", size=6),
        name="Anomaly"
    )
    st.plotly_chart(fig, use_container_width=True)

    # 7) Detailed table
    st.subheader("Detailed Results")
    out = user_df.copy()
    out["Status"] = np.where(out["anomaly_flag"], "Anomaly", "Normal")
    out = out[["timestamp", "energy_kwh", "Status", "anomaly_score"]]
    st.dataframe(out, use_container_width=True)
    st.download_button(
        "Download Your Anomaly Report",
        out.to_csv(index=False),
        "your_anomaly_report.csv",
        "text/csv"
    )