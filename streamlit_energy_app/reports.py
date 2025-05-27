import streamlit as st
from require_login import require_login
from db import load_energy_data, get_db, get_alerts_collection
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import joblib
import os

def reports_page():
    require_login()
    st.title("Energy Reports")
    st.markdown("""
        This page provides comprehensive reports on energy consumption and anomalies.
        Download detailed reports for analysis and record-keeping.
    """)

    # Date range selector
    st.markdown("### Select Time Range")
    time_range = st.selectbox(
        "Choose a time range",
        ["Last 24 hours", "Last 7 days", "Last 30 days", "Last 90 days", "All time"],
        index=4  # Default to "All time"
    )

    # Load data
    df = load_energy_data()
    if df.empty:
        st.warning("No energy data available.")
        return

    # Apply time filter
    now = datetime.now()
    if time_range == "Last 24 hours":
        df = df[df['timestamp'] >= now - timedelta(days=1)]
    elif time_range == "Last 7 days":
        df = df[df['timestamp'] >= now - timedelta(days=7)]
    elif time_range == "Last 30 days":
        df = df[df['timestamp'] >= now - timedelta(days=30)]
    elif time_range == "Last 90 days":
        df = df[df['timestamp'] >= now - timedelta(days=90)]

    # Calculate daily statistics
    daily_stats = df.set_index('timestamp').resample('D').agg({
        'energy_wh': ['sum', 'mean', 'min', 'max', 'std']
    }).reset_index()
    daily_stats.columns = ['Date', 'Total Energy (Wh)', 'Average Energy (Wh)', 
                         'Minimum Energy (Wh)', 'Maximum Energy (Wh)', 'Standard Deviation (Wh)']

    # Detect anomalies using Isolation Forest
    try:
        model_path = "new_models/IF_model.joblib"
        if not os.path.exists(model_path):
            st.error("Anomaly detection model not found.")
            return
            
        model = joblib.load(model_path)
        # Create DataFrame with proper feature name
        data_df = pd.DataFrame({
            'energy_wh': df['energy_wh'].values
        })
        predictions = model.predict(data_df)
        scores = model.score_samples(data_df)
        
        # Convert scores to anomaly scores (higher is more anomalous)
        anomaly_scores = -scores
        
        # Add predictions and scores to dataframe
        df['is_anomaly'] = predictions == -1
        df['anomaly_score'] = anomaly_scores
        
        # Calculate anomaly statistics
        total_anomalies = df['is_anomaly'].sum()
        anomaly_rate = total_anomalies / len(df)
        avg_anomaly_score = df.loc[df['is_anomaly'], 'anomaly_score'].mean()
        
        # Create anomaly report
        anomaly_report = df[df['is_anomaly']].copy()
        anomaly_report = anomaly_report[['timestamp', 'energy_wh', 'anomaly_score']]
        anomaly_report.columns = ['Timestamp', 'Energy (Wh)', 'Anomaly Score']
        anomaly_report['Timestamp'] = anomaly_report['Timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
    except Exception as e:
        st.error(f"Error in anomaly detection: {str(e)}")
        return

    # Create reports
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Download Energy Report")
        energy_report = daily_stats.copy()
        energy_report['Date'] = energy_report['Date'].dt.strftime('%Y-%m-%d')
        st.download_button(
            "Download Energy Report",
            energy_report.to_csv(index=False),
            "energy_report.csv",
            "text/csv",
            key="download-energy"
        )

    with col2:
        st.markdown("### Download Anomaly Report")
        st.download_button(
            "Download Anomaly Report",
            anomaly_report.to_csv(index=False),
            "anomaly_report.csv",
            "text/csv",
            key="download-anomaly"
        )

    # Display summary statistics
    st.markdown("### Summary Statistics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Energy", f"{daily_stats['Total Energy (Wh)'].sum()/1000:,.1f} kWh")
    with col2:
        st.metric("Anomaly Rate", f"{anomaly_rate:.1%}")
    with col3:
        st.metric("Total Anomalies", f"{total_anomalies:,}")

    # Plot daily energy consumption
    st.markdown("### Daily Energy Consumption")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily_stats['Date'],
        y=daily_stats['Total Energy (Wh)'],
        mode='lines+markers',
        name='Daily Energy',
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title='Daily Energy Consumption',
        xaxis_title='Date',
        yaxis_title='Energy (Wh)',
        height=400,
        showlegend=True,
        template='plotly_white'
    )
    st.plotly_chart(fig, use_container_width=True)

    # Display anomaly statistics
    st.markdown("### Anomaly Statistics")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Average Anomaly Score", f"{avg_anomaly_score:.2f}")
    with col2:
        st.metric("Anomalies per Day", f"{total_anomalies/len(daily_stats):.1f}")
