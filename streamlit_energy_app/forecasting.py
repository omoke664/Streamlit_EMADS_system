
import streamlit as st 
from require_login import require_login
from db import load_energy_data
from sklearn.metrics import mean_absolute_error, mean_squared_error
from prophet import Prophet
import plotly.graph_objects as go



def forecasting_page():
    require_login()
    st.title("📈 Energy Forecasting (Prophet)")

    # 1) Load minute-level data
    df = load_energy_data()
    if df.empty:
        st.warning("⚠️ No energy data available.")
        return

    # 2) Aggregate to daily totals
    df_daily = (
        df.set_index("timestamp")   # minute timestamps → index
          .resample("D")            # group by calendar day
          .sum()                    # sum energy_kwh per day
          .reset_index()            # bring timestamp back as column
    )

    # Allow user to pick horizon
    horizon = st.slider("Forecast Horizon (days)", 1, 30, 7)

    # Prepare for Prophet: rename cols
    data = df_daily.rename(columns={"timestamp": "ds", "energy_kwh": "y"})

    # Split train/test on the last `horizon` days
    train = data.iloc[:-horizon]
    test  = data.iloc[-horizon:]

    # Fit Prophet on daily data
    m = Prophet(daily_seasonality=True, weekly_seasonality=True)
    m.fit(train)

    # Make future and forecast
    future   = m.make_future_dataframe(periods=horizon, freq="D")
    forecast = m.predict(future)

    # Plot with Plotly
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=train["ds"], y=train["y"], mode="lines", name="Historical"
    ))
    fig.add_trace(go.Scatter(
        x=forecast["ds"], y=forecast["yhat"], mode="lines", name="Forecast"
    ))
    fig.add_trace(go.Scatter(
        x=forecast["ds"], y=forecast["yhat_upper"],
        mode="lines", line=dict(width=0), showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=forecast["ds"], y=forecast["yhat_lower"],
        mode="lines", fill="tonexty", fillcolor="rgba(0,100,80,0.2)",
        line=dict(width=0), showlegend=False
    ))
    fig.update_layout(
        title="Daily Energy Forecast",
        xaxis_title="Date", yaxis_title="Energy (kWh)",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)

    # Compute accuracy on test daily totals
    # Align on dates
    fcst_df = forecast.set_index("ds")[["yhat"]]
    actual  = test.set_index("ds")["y"]
    y_pred  = fcst_df.loc[actual.index, "yhat"].values
    y_true  = actual.values

    mae  = mean_absolute_error(y_true, y_pred)
    mse  = mean_squared_error(y_true, y_pred)
    rmse = mse ** 0.5

    st.subheader("Forecast Accuracy")
    col1, col2 = st.columns(2)
    col1.metric("MAE", f"{mae:,.2f}")
    col2.metric("RMSE", f"{rmse:,.2f}")

    # Show the forecasted days
    with st.expander("Forecast Table"):
        disp = forecast[["ds","yhat","yhat_lower","yhat_upper"]].tail(horizon)
        disp = disp.rename(columns={
            "ds": "Date", "yhat":"Forecast", "yhat_lower":"Lower", "yhat_upper":"Upper"
        })
        st.dataframe(disp, use_container_width=True)

