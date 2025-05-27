import streamlit as st
from require_login import require_login
from db import load_energy_data
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import joblib
import os

def prophet_forecast_page():
    require_login()
    st.title("Prophet Energy Forecasting")
    st.markdown("""
        This page uses Facebook's Prophet model to forecast energy consumption.
        Prophet is particularly good at handling seasonal patterns and holidays in time series data.
    """)

    # Load the Prophet model
    try:
        model_path = "new_models/prophet_model.pkl"
        if not os.path.exists(model_path):
            st.error("Prophet model file not found. Please ensure the model is trained and saved correctly.")
            return
            
        model = joblib.load(model_path)
        st.success("Prophet model loaded successfully!")
    except Exception as e:
        st.error(f"Error loading the model: {str(e)}")
        return

    # Date range selector
    st.markdown("### Select Time Range")
    col1, col2 = st.columns([2, 1])
    with col1:
        time_range = st.selectbox(
            "Choose a time range",
            ["Last 24 hours", "Last 7 days", "Last 30 days", "Last 90 days", "All time"],
            index=4  # Default to "All time"
        )
    
    with col2:
        st.markdown("### Forecast Horizon")
        forecast_days = st.slider(
            "Number of days to forecast",
            min_value=1,
            max_value=30,
            value=7,
            help="Select how many days ahead you want to forecast"
        )

    # Load and filter data
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

    # Prepare data for Prophet
    prophet_df = df.copy()
    prophet_df = prophet_df.rename(columns={'timestamp': 'ds', 'energy_wh': 'y'})
    prophet_df['ds'] = pd.to_datetime(prophet_df['ds'])

    # Calculate daily sums for historical data
    daily_df = prophet_df.set_index('ds').resample('D').sum().reset_index()

    # Generate forecast
    future = model.make_future_dataframe(periods=forecast_days, freq='D')  # Use daily frequency
    forecast = model.predict(future)

    # Plot results
    fig = go.Figure()

    # Add actual values (daily sum)
    fig.add_trace(go.Scatter(
        x=daily_df['ds'],
        y=daily_df['y'],
        mode='lines+markers',
        name='Actual (Daily Total)',
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=8)
    ))

    # Add forecast
    fig.add_trace(go.Scatter(
        x=forecast['ds'],
        y=forecast['yhat'],
        mode='lines',
        name='Forecast',
        line=dict(color='#ff7f0e', dash='dash', width=2)
    ))

    # Add confidence intervals
    fig.add_trace(go.Scatter(
        x=forecast['ds'],
        y=forecast['yhat_upper'],
        fill=None,
        mode='lines',
        line_color='rgba(255, 127, 14, 0.2)',
        name='Upper Bound'
    ))

    fig.add_trace(go.Scatter(
        x=forecast['ds'],
        y=forecast['yhat_lower'],
        fill='tonexty',
        mode='lines',
        line_color='rgba(255, 127, 14, 0.2)',
        name='Lower Bound'
    ))

    fig.update_layout(
        title=f'Daily Energy Consumption Forecast ({forecast_days} days ahead)',
        xaxis_title='Date',
        yaxis_title='Energy (Wh)',
        height=600,
        showlegend=True,
        template='plotly_white',
        hovermode='x unified',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # Display metrics
    st.subheader("Forecast Metrics")
    col1, col2 = st.columns(2)
    
    # Calculate metrics for daily data
    # Ensure we only compare overlapping dates
    common_dates = set(daily_df['ds']).intersection(set(forecast['ds']))
    daily_df_filtered = daily_df[daily_df['ds'].isin(common_dates)]
    forecast_filtered = forecast[forecast['ds'].isin(common_dates)]
    
    # Sort both dataframes by date to ensure alignment
    daily_df_filtered = daily_df_filtered.sort_values('ds')
    forecast_filtered = forecast_filtered.sort_values('ds')
    
    # Calculate metrics
    mae = np.mean(np.abs(daily_df_filtered['y'].values - forecast_filtered['yhat'].values))
    rmse = np.sqrt(np.mean((daily_df_filtered['y'].values - forecast_filtered['yhat'].values) ** 2))
    
    with col1:
        st.metric("Mean Absolute Error", f"{mae:.2f} Wh")
    with col2:
        st.metric("Root Mean Square Error", f"{rmse:.2f} Wh")

    # Display forecast components
    st.subheader("Forecast Components")
    components_fig = model.plot_components(forecast)
    st.pyplot(components_fig)

    # Display detailed forecast
    st.subheader("Detailed Forecast")
    forecast_display = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
    forecast_display['ds'] = forecast_display['ds'].dt.strftime('%Y-%m-%d')
    forecast_display.columns = ['Date', 'Forecast (Wh)', 'Lower Bound (Wh)', 'Upper Bound (Wh)']
    st.dataframe(forecast_display, use_container_width=True) 