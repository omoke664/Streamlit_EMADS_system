

import streamlit as st 
import plotly.graph_objects as go 
import plotly.express as px

from require_login import require_login
from db import load_energy_data 

def analytics_page():
    require_login()
    st.title("Data Analytics")

    # 1) Load and filter data by date range
    df = load_energy_data()
    if df.empty:
        st.warning("⚠️ No energy data available.")
        return

    # Date‐range selector
    min_date = df["timestamp"].dt.date.min()
    max_date = df["timestamp"].dt.date.max()
    start_date, end_date = st.date_input(
        "Select date range",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
    df = df[(df["timestamp"].dt.date >= start_date) & (df["timestamp"].dt.date <= end_date)]

    # 2) Aggregated View
    st.subheader("Aggregated Consumption")
    agg_level = st.selectbox("Aggregation level", ["Daily", "Weekly", "Monthly"])
    freq_map = {"Daily": "D", "Weekly": "W", "Monthly": "M"}
    df_agg = (
        df.set_index("timestamp")
          .resample(freq_map[agg_level])["energy_wh"]
          .sum()
          .reset_index()
    )
    df_agg["timestamp"] = df_agg["timestamp"].dt.date
    st.bar_chart(df_agg.rename(columns={"timestamp": "index"}).set_index("index")["energy_wh"],
                 use_container_width=True)

    # 3) Distribution Plots
    st.subheader("Consumption Distribution")
    fig_hist = px.histogram(df, x="energy_wh", nbins=30,
                            title="Histogram of Energy Consumption")
    st.plotly_chart(fig_hist, use_container_width=True)

    fig_box = px.box(df, y="energy_wh", points="all",
                     title="Boxplot of Energy Consumption")
    st.plotly_chart(fig_box, use_container_width=True)

    # 4) Comparison: Hourly Profiles by Weekday
    st.subheader("Hourly Profiles by Weekday")
    df["hour"] = df["timestamp"].dt.hour
    df["weekday"] = df["timestamp"].dt.day_name()
    hourly = (
        df.groupby(["weekday", "hour"])["energy_wh"]
          .mean()
          .reindex(index=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"], level=0)
          .reset_index()
    )

    fig = go.Figure()
    for day in hourly["weekday"].unique():
        df_day = hourly[hourly["weekday"] == day]
        fig.add_trace(go.Scatter(
            x=df_day["hour"],
            y=df_day["energy_wh"],
            mode="lines+markers",
            name=day
        ))

    fig.update_layout(
        xaxis_title="Hour of Day",
        yaxis_title="Avg Energy (kWh)",
        legend_title="Weekday",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)

