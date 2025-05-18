import streamlit as st 
from require_login import require_login
from db import load_energy_data

def dashboard_page():
    require_login()

    st.title("🏠 Dashboard")
    user = st.session_state.user 
    st.write(f"**Logged in as:** {user['username']} ({user['role']})")
    
    # 1) Load data
    df = load_energy_data()
    if df.empty:
        st.warning("⚠️ No energy data available.")
        return
    #2) Computer KPIs
    total_kwh = df["energy_kwh"].sum()
    avg_kwh = df["energy_kwh"].mean()
    peak_kwh = df["energy_kwh"].max()

    #Stub anomaly rate 
    anomaly_rate = 0.0 

    #3) Display KPI cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Energy (kWh)", f"{total_kwh:,.2f}")
    col2.metric("Average Energy (kWh)", f"{avg_kwh:,.2f}")
    col3.metric("Peak Energy (kWh)", f"{peak_kwh:,.2f}")
    col4.metric("Anomaly Rate (%)", f"{anomaly_rate:,.2f}%")

    #4) Time Series Plot
    st.subheader("Energy Consumption Over Time.")
    st.line_chart(df.set_index("timestamp")["energy_kwh"], use_container_width = True)

    # 5) Data Table
    with st.expander("View Data", expanded = False):
        st.dataframe(df, use_container_width = True)
        st.download_button("Download Data", df.to_csv(index = False), "energy_data.csv", "text/csv", key = "download-csv")

    # 6) Daily Summary
    st.subheader("Daily Energy Summary")
    daily_summary = df.resample("D", on = "timestamp").sum().reset_index()
    daily_summary["timestamp"] = daily_summary["timestamp"].dt.date
    daily_summary.columns = ["Date", "Total Energy (kWh)"]
    st.dataframe(daily_summary, use_container_width = True)

    # 7)Moving Average
    st.subheader("7-Day Moving Average")
    df["7-day MA"] = df["energy_kwh"].rolling(window = 7).mean()
    st.line_chart(df.set_index("timestamp")[["energy_kwh", "7-day MA"]], use_container_width = True)

    # 8) Average for each day of the week
    st.subheader("Average Energy Consumption by Day of the Week")
    df["day_of_week"] = df["timestamp"].dt.day_name()
    avg_by_day = df.groupby("day_of_week")["energy_kwh"].mean().reindex(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
    st.bar_chart(avg_by_day, use_container_width = True)



