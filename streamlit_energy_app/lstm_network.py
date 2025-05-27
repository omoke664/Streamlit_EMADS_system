import streamlit as st
from require_login import require_login
from db import load_energy_data
import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import joblib
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import os

# Define the LSTM model architecture
class LSTMModel(nn.Module):
    def __init__(self, input_size=1, hidden_size=50, num_layers=1, dropout=0.0):
        super(LSTMModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM layer
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        # Linear layer for prediction
        self.linear = nn.Linear(hidden_size, 1)
    
    def forward(self, x):
        # Initialize hidden state with zeros
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        
        # Forward propagate LSTM
        out, _ = self.lstm(x, (h0, c0))
        
        # Decode the hidden state of the last time step
        out = self.linear(out[:, -1, :])
        return out

def create_and_save_scaler(data, scaler_path):
    """Create and save a scaler for the data"""
    try:
        # Create models directory if it doesn't exist
        os.makedirs(os.path.dirname(scaler_path), exist_ok=True)
        
        # Create and fit scaler
        scaler = StandardScaler()  # Changed to StandardScaler for better normalization
        scaler.fit(data)
        
        # Save scaler
        joblib.dump(scaler, scaler_path)
        return scaler
    except Exception as e:
        st.error(f"Error creating scaler: {str(e)}")
        return None

def load_model_and_scaler():
    """Load the LSTM model and scaler with proper error handling"""
    try:
        # Define paths
        models_dir = os.path.join(os.path.dirname(__file__), "new_models")
        model_path = os.path.join(models_dir, "lstm_model_state_dict.pth")
        scaler_path = os.path.join(models_dir, "lstm_scaler.joblib")
        
        # Create models directory if it doesn't exist
        os.makedirs(models_dir, exist_ok=True)
        
        # Load or create scaler
        if os.path.exists(scaler_path):
            scaler = joblib.load(scaler_path)
        else:
            # Load data to create scaler
            df = load_energy_data()
            if df.empty:
                raise ValueError("No data available to create scaler")
            data = df['energy_wh'].values.reshape(-1, 1)
            scaler = create_and_save_scaler(data, scaler_path)
            if scaler is None:
                raise ValueError("Failed to create scaler")
        
        # Load model
        if not os.path.exists(model_path):
            raise FileNotFoundError("LSTM model file not found")
            
        # Initialize model with single layer architecture to match saved model
        model = LSTMModel(input_size=1, hidden_size=50, num_layers=1, dropout=0.0)
        model.load_state_dict(torch.load(model_path))
        model.eval()
        
        return model, scaler
    except Exception as e:
        st.error(f"Error loading model or scaler: {str(e)}")
        return None, None

def prepare_sequences(data, seq_length):
    """Prepare sequences for LSTM prediction with improved preprocessing"""
    X = []
    y = []
    for i in range(len(data) - seq_length):
        X.append(data[i:(i + seq_length)])
        y.append(data[i + seq_length])
    return np.array(X), np.array(y)

def add_time_features(df):
    """Add time-based features to improve prediction"""
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['month'] = df['timestamp'].dt.month
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    return df

def predict_next_energy(model, scaler, seq_length, historical_data_scaled):
    """Predicts the next single energy value using the loaded LSTM model."""
    if len(historical_data_scaled) != seq_length:
        raise ValueError(f"Historical data must contain exactly {seq_length} points.")

    # Convert the input sequence to a PyTorch tensor
    seq_tensor = torch.FloatTensor(historical_data_scaled).view(1, -1, 1)  # Reshape for LSTM input

    with torch.no_grad():
        # Reset hidden state for a new sequence prediction
        model.hidden_cell = (
            torch.zeros(1, 1, model.hidden_size),
            torch.zeros(1, 1, model.hidden_size)
        )

        # Get the prediction (output is a tensor)
        scaled_prediction_tensor = model(seq_tensor)

        # Get the value from the tensor and inverse transform
        scaled_prediction = scaled_prediction_tensor.item()
        predicted_value_original_scale = scaler.inverse_transform(np.array([[scaled_prediction]]))[0][0]

    return predicted_value_original_scale

def generate_predictions(model, scaler, last_sequence, forecast_steps):
    """Generate predictions using the LSTM model following the successful approach"""
    predictions = []
    current_sequence = last_sequence.copy()
    
    with torch.no_grad():
        for _ in range(forecast_steps):
            # Get prediction using the single prediction function
            pred_value = predict_next_energy(model, scaler, len(current_sequence), current_sequence)
            predictions.append(pred_value)
            
            # Update sequence for next prediction
            current_sequence = np.roll(current_sequence, -1)
            current_sequence[-1] = scaler.transform(np.array([[pred_value]]))[0][0]
    
    return np.array(predictions)

def lstm_network_page():
    require_login()
    st.title("LSTM Energy Forecasting")
    st.markdown("""
        This page uses a Long Short-Term Memory (LSTM) neural network to forecast energy consumption.
        The model has been optimized for better prediction accuracy.
    """)

    # Load model and scaler
    model, scaler = load_model_and_scaler()
    if model is None or scaler is None:
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

    # Resample data to hourly intervals
    df.set_index('timestamp', inplace=True)
    # Create a new DataFrame with only the energy_wh column for resampling
    energy_df = df[['energy_wh']].copy()
    # Resample the energy data
    energy_resampled = energy_df.resample('H').mean().fillna(method='ffill')
    # Create the final resampled DataFrame
    df_resampled = pd.DataFrame(index=energy_resampled.index)
    df_resampled['energy_wh'] = energy_resampled['energy_wh']
    df_resampled.reset_index(inplace=True)
    
    # Check for complete days in resampled data
    df_resampled['date'] = df_resampled['timestamp'].dt.date
    daily_counts = df_resampled.groupby('date').size()
    complete_days = daily_counts[daily_counts == 24]
    
    if len(complete_days) == 0:
        st.warning("""
            No complete days found in the selected time range. This could be due to:
            1. Missing data points in the selected period
            2. Data collection gaps
            3. Time range too short
            
            Please try:
            - Selecting a longer time range
            - Checking if data is being collected properly
            - Verifying the data source
        """)
        return

    # Use resampled data for further processing
    df = df_resampled

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

    # Sort data by timestamp to ensure correct sequence
    df = df.sort_values('timestamp')

    # Prepare data for LSTM
    data = df['energy_wh'].values.reshape(-1, 1)
    scaled_data = scaler.transform(data)

    # Create sequences for prediction
    sequence_length = 24  # Using 24 hours as sequence length to match training
    X, y = prepare_sequences(scaled_data, sequence_length)

    if len(X) == 0:
        st.warning("Not enough data points to create sequences for prediction. Please select a longer time range.")
        return

    # Generate historical predictions
    historical_predictions = []
    for i in range(len(X)):
        pred = predict_next_energy(model, scaler, sequence_length, X[i])
        historical_predictions.append(pred)
    historical_predictions = np.array(historical_predictions)
    actual_values = scaler.inverse_transform(y)

    # Calculate hourly metrics first
    hourly_mae = np.mean(np.abs(actual_values - historical_predictions.reshape(-1, 1)))
    hourly_rmse = np.sqrt(np.mean((actual_values - historical_predictions.reshape(-1, 1)) ** 2))

    # Calculate daily sums for historical data
    df['date'] = df['timestamp'].dt.date
    daily_df = df.groupby('date')['energy_wh'].sum().reset_index()
    daily_df['date'] = pd.to_datetime(daily_df['date'])

    # Calculate daily sums for predictions and actual values
    pred_df = pd.DataFrame({
        'timestamp': df['timestamp'].iloc[sequence_length:],
        'energy_wh': historical_predictions,
        'actual': actual_values.flatten()
    })
    pred_df['date'] = pred_df['timestamp'].dt.date
    
    # Ensure we have complete days for both predictions and actual values
    complete_days = pred_df.groupby('date').size() == 24
    pred_df = pred_df[pred_df['date'].isin(complete_days[complete_days].index)]
    
    # Calculate daily sums
    daily_pred = pred_df.groupby('date').agg({
        'energy_wh': 'sum',
        'actual': 'sum'
    }).reset_index()
    daily_pred['date'] = pd.to_datetime(daily_pred['date'])

    # Check if we have valid data
    if daily_pred.empty:
        st.warning("""
            No complete days of data available for prediction. This could be due to:
            1. Missing data points in the selected period
            2. Data collection gaps
            3. Time range too short
            
            Please try:
            - Selecting a longer time range
            - Checking if data is being collected properly
            - Verifying the data source
        """)
        return

    # Generate future predictions
    last_sequence = scaled_data[-sequence_length:].reshape(1, sequence_length, 1)
    future_predictions = generate_predictions(model, scaler, last_sequence.flatten(), forecast_days * 24)

    # Get the last valid date and create future dates
    last_date = daily_pred['date'].max()
    if pd.isna(last_date):
        st.warning("No valid dates found in the data. Please try a different time range.")
        return

    # Convert future predictions to daily sums
    future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=forecast_days)
    future_df = pd.DataFrame({
        'date': future_dates,
        'energy_wh': np.array(future_predictions).reshape(-1, 24).sum(axis=1)
    })

    # Combine historical and future predictions
    all_predictions = pd.concat([daily_pred[['date', 'energy_wh']], future_df])

    # Plot results
    fig = go.Figure()

    # Add actual values (daily sum)
    fig.add_trace(go.Scatter(
        x=daily_df['date'],
        y=daily_df['energy_wh'],
        mode='lines+markers',
        name='Actual (Daily Total)',
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=8)
    ))

    # Add historical predictions
    fig.add_trace(go.Scatter(
        x=daily_pred['date'],
        y=daily_pred['energy_wh'],
        mode='lines',
        name='Historical Predictions',
        line=dict(color='#ff7f0e', dash='dash', width=2)
    ))

    # Add future predictions
    fig.add_trace(go.Scatter(
        x=future_df['date'],
        y=future_df['energy_wh'],
        mode='lines',
        name='Future Forecast',
        line=dict(color='#2ca02c', dash='dot', width=2)
    ))

    fig.update_layout(
        title=f'Daily Energy Consumption Forecast ({forecast_days} days ahead)',
        xaxis_title='Date',
        yaxis_title='Energy (Wh)',
        height=600,
        showlegend=True,
        template='plotly_white',
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # Display metrics
    st.subheader("Forecast Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculate metrics for historical predictions
    daily_mae = np.mean(np.abs(daily_pred['actual'] - daily_pred['energy_wh']))
    daily_rmse = np.sqrt(np.mean((daily_pred['actual'] - daily_pred['energy_wh']) ** 2))
    
    with col1:
        st.metric("Hourly MAE", f"{hourly_mae:.2f} Wh")
    with col2:
        st.metric("Hourly RMSE", f"{hourly_rmse:.2f} Wh")
    with col3:
        st.metric("Daily MAE", f"{daily_mae:.2f} Wh")
    with col4:
        st.metric("Daily RMSE", f"{daily_rmse:.2f} Wh")

    # Display predictions table
    st.subheader("Detailed Predictions")
    predictions_display = all_predictions[['date', 'energy_wh']].copy()
    predictions_display['date'] = predictions_display['date'].dt.strftime('%Y-%m-%d')
    predictions_display.columns = ['Date', 'Predicted Energy (Wh)']
    st.dataframe(predictions_display, use_container_width=True) 