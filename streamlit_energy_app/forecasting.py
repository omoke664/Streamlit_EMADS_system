import os
import joblib
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.metrics import mean_absolute_error, mean_squared_error
from require_login import require_login
from db import load_energy_data
import math
import torch
from models.train_lstm import LSTMModel

# Locating script's directory
SCRIPT_DIR = os.path.dirname(__file__)

# Build model paths
MODEL_PATH = os.path.join(SCRIPT_DIR, "models", "lstm_model.pth")
SCALER_PATH = os.path.join(SCRIPT_DIR, "models", "lstm_scaler.joblib")

def create_sequences(data, seq_length):
    X = []
    for i in range(len(data) - seq_length):
        X.append(data[i:(i + seq_length)])
    return np.array(X)

def forecasting_page():
    require_login()
    st.title("📈 Energy Forecasts")

    # 1) Load raw data
    df = load_energy_data()
    if df.empty:
        st.warning("⚠️ No energy data available.")
        return

    # 2) Aggregate to daily sums
    df_daily = (
        df.set_index("timestamp")
          .resample("D")
          .sum()
          .reset_index()
    )
    data = df_daily["energy_wh"].values.reshape(-1, 1)

    # 3) Choose your forecast horizon
    horizon = st.slider("Forecast Horizon (days)", 1, 30, 7)

    # 4) Load the saved LSTM model and scaler
    if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
        st.error("Model files not found. Please train the model first.")
        return

    # Initialize and load model
    model = LSTMModel()
    model.load_state_dict(torch.load(MODEL_PATH))
    model.eval()
    scaler = joblib.load(SCALER_PATH)

    # 5) Prepare data for forecasting
    scaled_data = scaler.transform(data)
    seq_length = 7  # Must match the training sequence length
    
    # Create sequences for prediction
    last_sequence = scaled_data[-seq_length:]
    last_sequence = torch.FloatTensor(last_sequence).unsqueeze(0)
    
    # Generate forecasts
    forecast = []
    current_sequence = last_sequence
    
    with torch.no_grad():
        for _ in range(horizon):
            # Predict next value
            next_pred = model(current_sequence)
            forecast.append(next_pred.item())
            
            # Update sequence for next prediction
            current_sequence = torch.roll(current_sequence, -1, dims=1)
            current_sequence[0, -1, 0] = next_pred.item()
    
    # Inverse transform the forecast
    forecast = np.array(forecast).reshape(-1, 1)
    forecast = scaler.inverse_transform(forecast)
    
    # Create forecast dates
    last_date = df_daily["timestamp"].iloc[-1]
    forecast_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=horizon)

    # 6) Plot with Plotly
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_daily["timestamp"], y=df_daily["energy_wh"], mode="lines", name="Historical"))
    fig.add_trace(go.Scatter(x=forecast_dates, y=forecast.flatten(), mode="lines", name="Forecast"))
    
    fig.update_layout(
        title="Daily Energy Forecast",
        xaxis_title="Date",
        yaxis_title="Energy (Wh)",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)

    # 7) Compute accuracy on historical data
    if len(df_daily) > horizon:
        test = df_daily["energy_wh"].iloc[-horizon:].values
        y_true, y_pred = test, forecast.flatten()
        mae = mean_absolute_error(y_true, y_pred)
        mse = mean_squared_error(y_true, y_pred)
        rmse = math.sqrt(mse)

        st.subheader(f"Forecast Accuracy (last {horizon} days)")
        c1, c2 = st.columns(2)
        c1.metric("MAE", f"{mae:,.2f}")
        c2.metric("RMSE", f"{rmse:,.2f}")

    # 8) Show the forecast table
    with st.expander("See forecasted values"):
        forecast_df = pd.DataFrame({
            "Date": forecast_dates,
            "Forecast": forecast.flatten()
        })
        st.dataframe(forecast_df, use_container_width=True)
