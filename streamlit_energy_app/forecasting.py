# forecasting.py
import os
import joblib
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from sklearn.metrics import mean_absolute_error, mean_squared_error
from require_login import require_login
from db import load_energy_data
import math

MODEL_PATH = os.path.join("models", "Prophet.pkl")

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
        df.set_index("timestamp")   # make ts the index
          .resample("D")            # calendar days
          .sum()                    # sum energy_wh per day
          .reset_index()            # back to column
    )
    data = df_daily.rename(columns={"timestamp": "ds", "energy_wh": "y"})

    # 3) Choose your forecast horizon
    horizon = st.slider("Forecast Horizon (days)", 1, 30, 7)

    # 4) Load your saved Prophet model
    if not os.path.exists(MODEL_PATH):
        st.error(f"Model file not found at `{MODEL_PATH}`")
        return
    m = joblib.load(MODEL_PATH)

    # 5) Build future and forecast
    future = m.make_future_dataframe(periods=horizon, freq="D")
    forecast = m.predict(future)

    # 6) Plot with Plotly
    fig = go.Figure()
    # historical
    fig.add_trace(go.Scatter(
        x=data["ds"], y=data["y"],
        mode="lines", name="Historical"
    ))
    # forecast
    fig.add_trace(go.Scatter(
        x=forecast["ds"], y=forecast["yhat"],
        mode="lines", name="Forecast"
    ))
    # uncertainty band
    fig.add_trace(go.Scatter(
        x=forecast["ds"], y=forecast["yhat_upper"],
        mode="lines", line=dict(width=0), showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=forecast["ds"], y=forecast["yhat_lower"],
        mode="lines", fill="tonexty",
        fillcolor="rgba(0,100,80,0.2)",
        line=dict(width=0), showlegend=False
    ))

    fig.update_layout(
        title="Daily Energy Forecast",
        xaxis_title="Date", yaxis_title="Energy (kWh)",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)

    # 7) Compute accuracy against the last `horizon` days
    #   align historical test window
    test = data.iloc[-horizon:].set_index("ds")["y"]
    #   align forecast
    fcst = forecast.set_index("ds")["yhat"].reindex(test.index)
    y_true, y_pred = test.values, fcst.values

    mae  = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = math.sqrt(mse)

    st.subheader("Forecast Accuracy (last {} days)".format(horizon))
    c1, c2 = st.columns(2)
    c1.metric("MAE", f"{mae:,.2f}")
    c2.metric("RMSE", f"{rmse:,.2f}")

    # 8) Show the forecast table
    with st.expander("See forecasted values"):
        disp = forecast[["ds","yhat","yhat_lower","yhat_upper"]].tail(horizon)
        disp = disp.rename(columns={
            "ds":   "Date",
            "yhat": "Forecast",
            "yhat_lower": "Lower",
            "yhat_upper": "Upper"
        })
        st.dataframe(disp, use_container_width=True)
