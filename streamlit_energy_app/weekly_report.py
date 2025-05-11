import os
import pandas as pd
from datetime import datetime, timedelta
from db import get_db, get_user_collection, get_alerts_collection
from email_utils import send_email
from prophet import Prophet  # or your ARIMA code import
import pickle

def generate_weekly_report():
    db       = get_db()
    readings = pd.DataFrame(list(db["energy_readings"].find()))
    alerts   = pd.DataFrame(list(get_alerts_collection().find()))
    users    = get_user_collection()

    if readings.empty:
        print("No readings — skipping report.")
        return

    # 1) Define date windows
    today       = pd.Timestamp.now().normalize()
    last_monday = today - timedelta(days=today.weekday()+7)
    this_monday = today - timedelta(days=today.weekday())
    prev_monday = last_monday - timedelta(days=7)

    # Filter readings for these windows
    mask_last_week = (readings["timestamp"] >= last_monday) & (readings["timestamp"] < this_monday)
    mask_prev_week = (readings["timestamp"] >= prev_monday) & (readings["timestamp"] < last_monday)
    week1 = readings.loc[mask_prev_week]
    week2 = readings.loc[mask_last_week]

    # 2) Compute consumption totals
    total_prev = week1["energy_kwh"].sum()
    total_last = week2["energy_kwh"].sum()
    pct_change = ((total_last - total_prev) / total_prev * 100) if total_prev else float("nan")

    # 3) Forecast next week
    # Load pre-trained Prophet model & scaler
    model = Prophet()
    model.load("models/prophet_weekly.pkl")    # adjust path
    # Prepare future dataframe
    future = model.make_future_dataframe(periods=7, freq="D")
    fcst   = model.predict(future)
    week_forecast = fcst.set_index("ds")["yhat"].loc[this_monday + timedelta(days=7):
                                                   this_monday + timedelta(days=13)]
    forecast_str = "\n".join(
        f"  {d.date()}: {v:.2f} kWh" 
        for d, v in week_forecast.items()
    )

    # 4) Anomaly summary
    mask_alerts = (alerts["detected_at"] >= last_monday) & (alerts["detected_at"] < this_monday)
    week_alerts = alerts.loc[mask_alerts]
    num_alerts  = len(week_alerts)

    # 5) Build email body
    subject = f"EMADS Weekly Report: {last_monday.date()} – {this_monday.date() - timedelta(days=1)}"
    body = f"""
Hello,

Here is your EMADS weekly summary for {last_monday.date()} to {this_monday.date() - timedelta(days=1)}:

1) Energy Consumption
   • Previous week total: {total_prev:,.2f} kWh  
   • Last week total:     {total_last:,.2f} kWh  
   • Change:              {pct_change:+.2f}%

2) Forecast for next week:
{forecast_str}

3) Anomalies Detected Last Week:
   • Total anomaly events: {num_alerts}

Please log in to the dashboard for full details and charts.

Best regards,  
EMADS Automated Reporting System
    """

    # 6) Send email
    recipient_emails = [u["email"] for u in users.find(
        {"role": {"$in": ["admin", "manager"]}},
        {"email": 1, "_id": 0}
    )]
    send_email(recipient_emails, subject, body)
    print("Weekly report sent to:", recipient_emails)
