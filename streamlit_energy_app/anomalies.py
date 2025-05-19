import streamlit as st
from require_login import require_login
from db import load_energy_data
import pandas as pd
import joblib
import numpy as np
import plotly.express as px



MODEL_PATH = "models\IF_model.joblib"


def anomalies_page():
    require_login()
    st.title("📊 Anomaly Detection")

    # 1) Load data
    df = load_energy_data()
    if df.empty:
        st.warning("⚠️ No energy data available.")
        return

    # 2) Load pre-trained Isolation Forest model
    try:
        if_model = joblib.load(MODEL_PATH)
    except FileNotFoundError:
        st.error(f"Cannot find model at {MODEL_PATH}")
        return

    # 3) Predict anomalies and scores
    X = df[["energy_wh"]]
    df["anomaly_flag"]  = if_model.predict(X) == -1
    df["anomaly_score"] = if_model.decision_function(X)

    # 4) Summary metrics
    total    = len(df)
    anomalies = df["anomaly_flag"].sum()
    rate     = anomalies / total if total else 0.0

    # Compute longest run of consecutive anomalies
    runs = (df["anomaly_flag"] != df["anomaly_flag"].shift()).cumsum()
    cons_counts = df.groupby(runs)["anomaly_flag"].sum()
    longest_run = int(cons_counts.max()) if not cons_counts.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Records", f"{total}")
    c2.metric("Total Anomalies", f"{anomalies}")
    c3.metric("Anomaly Rate", f"{rate:.2%}")
    c4.metric("Longest Consecutive Anomalies", f"{longest_run}")

    # 5) Time-series plot with anomalies highlighted
    st.subheader("Energy Consumption with Anomalies Highlighted")
    fig = px.line(df, x="timestamp", y="energy_wh", title="Energy Over Time")
    fig.add_scatter(
        x=df.loc[df["anomaly_flag"], "timestamp"],
        y=df.loc[df["anomaly_flag"], "energy_wh"],
        mode="markers",
        marker=dict(color="red", size=6),
        name="Anomaly"
    )
    st.plotly_chart(fig, use_container_width=True)

    # 6) Detailed table
    st.subheader("All Records with Anomaly Flag & Score")
    display_df = df.copy()
    display_df["Status"] = np.where(display_df["anomaly_flag"], "Anomaly", "Normal")
    display_df = display_df[["timestamp", "energy_wh", "Status", "anomaly_score"]]
    display_df = display_df.sort_values("timestamp").reset_index(drop=True)
    st.dataframe(display_df, use_container_width=True)
    st.download_button(
        "Download Detailed Anomalies CSV",
        display_df.to_csv(index=False),
        "anomalies_detailed.csv",
        "text/csv"
    )

    # 7) Model description
    st.markdown("---")
    st.subheader("How the Isolation Forest Model Works")
    params = if_model.get_params()
    st.markdown(f"""
- **Model parameters**  
  - `n_estimators`: {params['n_estimators']}  
  - `contamination`: {params['contamination']}  
  - `max_samples`: {params.get('max_samples', 'auto')}  
  - `random_state`: {params['random_state']}  

Isolation Forest isolates anomalies by recursively partitioning the data. Since anomalies are few and different, they require fewer splits to isolate, resulting in lower “anomaly scores.” Points with negative predictions (`-1`) are flagged as anomalies.

**Summary Metrics**  
- Total points analyzed: **{total}**  
- Points flagged anomalous: **{anomalies}**  
- Anomaly rate: **{rate:.2%}**  
- Longest consecutive anomaly run: **{longest_run}**
    """)

