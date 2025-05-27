import streamlit as st 
from require_login import require_login
from db import get_energy_collection
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import joblib
import numpy as np

# Cache the data loading function with a shorter TTL
@st.cache_data(ttl=60)  # Cache for 1 minute
def load_energy_data(start_time, end_time):
    """Load energy data from MongoDB with caching"""
    energy_collection = get_energy_collection()
    # Optimize query by only fetching needed fields and using proper sort
    energy_data = list(energy_collection.find(
        {
            "timestamp": {
                "$gte": start_time,
                "$lte": end_time
            }
        },
        {
            "_id": 0,
            "timestamp": 1,
            "energy_wh": 1
        }
    ).sort("timestamp", 1))
    
    if not energy_data:
        return None
    
    df = pd.DataFrame(energy_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def dashboard_page():
    require_login()

    # Header with user info
    st.title("Energy Dashboard")
    user = st.session_state.user
    st.markdown(f"**Welcome back, {user['first_name']}!** You're logged in as {user['role'].title()}")
    
    # Date range selector
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### Select Time Range")
        time_range = st.selectbox(
            "Choose a time range",
            ["Last 24 hours", "Last 7 days", "Last 30 days", "Last 90 days", "All time"],
            index=4
        )
    
    # Calculate time range
    now = datetime.now()
    if time_range == "Last 24 hours":
        start_time = now - timedelta(days=1)
        end_time = now
    elif time_range == "Last 7 days":
        start_time = now - timedelta(days=7)
        end_time = now
    elif time_range == "Last 30 days":
        start_time = now - timedelta(days=30)
        end_time = now
    elif time_range == "Last 90 days":
        start_time = now - timedelta(days=90)
        end_time = now
    else:  # All time
        start_time = datetime.min
        end_time = now

    # Load and filter data using the same function as anomalies page
    df = load_energy_data(start_time, end_time)
    if df is None or df.empty:
        st.warning("No energy data available.")
        return

    # Calculate KPIs
    total_wh = df["energy_wh"].sum()
    avg_wh = df["energy_wh"].mean()
    peak_wh = df["energy_wh"].max()

    # Calculate anomaly rate using the same method as anomalies page
    try:
        model_path = "new_models/IF_model.joblib"
        model = joblib.load(model_path)
        # Get anomaly scores
        scores = model.decision_function(df[['energy_wh']].values)
        
        # Calculate thresholds based on score distribution
        high_threshold = np.percentile(scores, 0.5)    # Top 0.5% most anomalous
        medium_threshold = np.percentile(scores, 1.0)  # Top 1% most anomalous
        low_threshold = np.percentile(scores, 2.0)     # Top 2% most anomalous
        
        # Categorize anomalies
        df['anomaly_score'] = scores
        df['anomaly'] = model.predict(df[['energy_wh']].values)
        
        # Add severity levels
        df['severity'] = 'normal'
        df.loc[df['anomaly_score'] <= high_threshold, 'severity'] = 'high'
        df.loc[(df['anomaly_score'] > high_threshold) & 
               (df['anomaly_score'] <= medium_threshold), 'severity'] = 'medium'
        df.loc[(df['anomaly_score'] > medium_threshold) & 
               (df['anomaly_score'] <= low_threshold), 'severity'] = 'low'
        
        # Additional filtering to ensure anomalies are significant
        df['z_score'] = (df['energy_wh'] - df['energy_wh'].mean()) / df['energy_wh'].std()
        df.loc[abs(df['z_score']) < 2.0, 'anomaly'] = 1
        df.loc[abs(df['z_score']) < 2.0, 'severity'] = 'normal'
        
        # Calculate anomaly rate
        total_anomalies = len(df[df['severity'].isin(['high', 'medium', 'low'])])
        anomaly_rate = (total_anomalies / len(df)) * 100 if len(df) > 0 else 0
    except Exception as e:
        st.warning(f"Could not calculate anomaly rate: {str(e)}")
        anomaly_rate = 0.0

    # Display KPI cards
    st.markdown("### Key Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Energy",
            f"{total_wh/1000:,.1f} kWh",
            delta=f"{(total_wh/1000/24):,.1f} kWh/day"
        )
    with col2:
        st.metric(
            "Average Energy",
            f"{avg_wh:,.1f} Wh",
            delta=f"{(avg_wh - df['energy_wh'].mean()):,.1f} Wh"
        )
    with col3:
        st.metric(
            "Peak Energy",
            f"{peak_wh:,.1f} Wh",
            delta=f"{(peak_wh - df['energy_wh'].max()):,.1f} Wh"
        )
    with col4:
        st.metric(
            "Anomaly Rate",
            f"{anomaly_rate:.2f}%",
            delta=None
        )

    # Main time series plot
    st.markdown("### Energy Consumption Over Time")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["energy_wh"],
        mode="lines",
        name="Energy Consumption",
        line=dict(color="#1f77b4", width=2)
    ))
    
    # Add 7-day moving average
    df["7-day MA"] = df["energy_wh"].rolling(window=7).mean()
    fig.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["7-day MA"],
        mode="lines",
        name="7-Day Moving Average",
        line=dict(color="#ff7f0e", width=2, dash="dash")
    ))
    
    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=20, b=20),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis_title="Time",
        yaxis_title="Energy (Wh)",
        template="plotly_white"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Daily summary and patterns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Daily Energy Summary")
        # Fix for resampling issue
        df_daily = df.copy()
        df_daily.set_index('timestamp', inplace=True)
        daily_summary = df_daily.resample('D')['energy_wh'].sum().reset_index()
        daily_summary['timestamp'] = daily_summary['timestamp'].dt.date
        daily_summary.columns = ['Date', 'Total Energy (kWh)']
        daily_summary['Total Energy (kWh)'] = daily_summary['Total Energy (kWh)'] / 1000
        
        fig = px.bar(
            daily_summary,
            x="Date",
            y="Total Energy (kWh)",
            title="Daily Energy Consumption"
        )
        fig.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=40, b=20),
            showlegend=False,
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### Weekly Patterns")
        df["day_of_week"] = df["timestamp"].dt.day_name()
        avg_by_day = df.groupby("day_of_week")["energy_wh"].mean()
        avg_by_day = avg_by_day.reindex(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        
        fig = px.bar(
            x=avg_by_day.index,
            y=avg_by_day.values,
            title="Average Energy Consumption by Day of Week"
        )
        fig.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=40, b=20),
            showlegend=False,
            xaxis_title="Day of Week",
            yaxis_title="Average Energy (Wh)",
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)

    # Data table with download option
    with st.expander("View Raw Data", expanded=False):
        st.dataframe(
            df[["timestamp", "energy_wh"]].rename(columns={
                "timestamp": "Time",
                "energy_wh": "Energy (Wh)"
            }),
            use_container_width=True
        )
        st.download_button(
            "Download Data",
            df.to_csv(index=False),
            "energy_data.csv",
            "text/csv",
            key="download-csv"
        )



