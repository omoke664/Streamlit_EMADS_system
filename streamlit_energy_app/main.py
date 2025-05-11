import streamlit as st 
import pandas as pd

from db import get_user_collection, load_energy_data, get_alerts_collection
from verify import hash_password, verify_password
from anomaly_detection.anomaly_detector import AnomalyDetector 
from sklearn.metrics import mean_absolute_error, mean_squared_error 

import plotly.graph_objects as go
import plotly.express as px 
from prophet import Prophet 
from bson import ObjectId


import io 
import sys, os
sys.path.append(os.path.abspath("."))


if "user" not in st.session_state:
    st.session_state.user = None


if "next_page" not in st.session_state:
    st.session_state.next_page = None

st.set_page_config(
    page_title="EMADS Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def registration_page():
    st.title("🔒Register")
    users = get_user_collection()



    with st.form("reg_form", clear_on_submit = True):
        username = st.text_input("Username")
        email = st.text_input("Email")
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        password = st.text_input("Password", type = "password")
        requested = st.selectbox("Role", ["admin", "manager", "resident"])
        submitted = st.form_submit_button("Create Account")


    if submitted:
        if users.find_one({"username": username}):
            st.error("❌ Username already exists. Log in instead.")
        if not username or not email or not password:
            st.error("❌ Please fill in all fields.")
        elif users.find_one({"username":username}):
            st.error("❌ Username already exists.")
        elif users.find_one({"email":email}):
            st.error("❌ An account with that email already exists.")
        else:
            users.insert_one({
                "username": username,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "created_at": pd.Timestamp.now(),
                "password": hash_password(password),
                "role": "resident", # persitent role until approved
                "requested_role": requested, # role requested by user
                "approved": requested == "resident",
            })
            if requested == "resident":
                st.success("✅ Account created!. You may now log in.")
            else:
                st.info("🕑 Your request for elevated access is pending admin approval.")

            st.rerun()



def login_page():
    st.title("🔑 Login")
    users = get_user_collection()

    with st.form("login_form", clear_on_submit=True):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log In")

    if submitted:
        user = users.find_one({"username": username})
        if user:
            if not user.get("Approved", False):
                st.error("🚫 Your account is pending approval.")
                return 

        # ←— DISABLED CHECK 
        if user and user.get("disabled", False):
            st.error("🚫 Your account has been disabled. Contact an administrator.")
            return

        if user and verify_password(password, user["password"]):
            # Store user info
            st.session_state.user = {
                "username": username,
                "role": user["role"]
            }
            st.success(f"✅ Welcome back, {username}!")
            st.session_state.next_page = "Dashboard"

            # Force a rerun so we immediately switch to the dashboard
            st.rerun()

        else:
            st.error("❌ Invalid username or password.")

            

def logout():
    st.session_state.user = None
    st.session_state.next_page = "Login"
    st.success("✅ You have been logged out.")


def require_login():
    if not st.session_state.user:
        st.warning("⚠️ Please log in or register to access this page.")
        st.stop()


#Placeholder page functions

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





def anomalies_page():
    require_login()
    st.title("📊 Anomalies")
    # TODO: highlight anomalies, table, metrics

    # 1) Load energy data
    df = load_energy_data()
    if df.empty:
        st.warning("No energy data available")
        return
    
    # 2) Run anomaly detection
    detector = AnomalyDetector(contamination = 0.01)
    df_flagged = detector.fit_detect(df, feature_cols =["energy_kwh"])

    #3) Computer Summary metrics
    total = len(df_flagged)
    anomalies = df_flagged["is_anomaly"].sum()
    rate = anomalies / total if total else 0.0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Records", f"{total}")
    col2.metric("Anomalies", f"{anomalies}")
    col3.metric("Anomaly Rate", f"{rate:.2%}")


    #4) Plot time series with anomaly markers
    st.subheader("Energy Consumption with Anomalies")

    # Mark normal vs. anomaly values
    df_flagged["Anomaly"] = df_flagged["energy_kwh"].where(df_flagged["is_anomaly"], None)

    # Create a multi-series DataFrame for the chart
    chart_df = df_flagged.set_index("timestamp")[["energy_kwh", "Anomaly"]]

    st.line_chart(chart_df, use_container_width=True)

    st.subheader("Anomaly Details")
    st.dataframe(
        df_flagged[df_flagged["is_anomaly"]]
        [["timestamp", "energy_kwh", "anomaly_score"]]
        .sort_values("timestamp")
        .reset_index(drop = True),
        use_container_width=True,
    )


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



def analytics_page():
    require_login()
    st.title("📊 Data Analytics")

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
          .resample(freq_map[agg_level])["energy_kwh"]
          .sum()
          .reset_index()
    )
    df_agg["timestamp"] = df_agg["timestamp"].dt.date
    st.bar_chart(df_agg.rename(columns={"timestamp": "index"}).set_index("index")["energy_kwh"],
                 use_container_width=True)

    # 3) Distribution Plots
    st.subheader("Consumption Distribution")
    fig_hist = px.histogram(df, x="energy_kwh", nbins=30,
                            title="Histogram of Energy Consumption")
    st.plotly_chart(fig_hist, use_container_width=True)

    fig_box = px.box(df, y="energy_kwh", points="all",
                     title="Boxplot of Energy Consumption")
    st.plotly_chart(fig_box, use_container_width=True)

    # 4) Comparison: Hourly Profiles by Weekday
    st.subheader("Hourly Profiles by Weekday")
    df["hour"] = df["timestamp"].dt.hour
    df["weekday"] = df["timestamp"].dt.day_name()
    hourly = (
        df.groupby(["weekday", "hour"])["energy_kwh"]
          .mean()
          .reindex(index=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"], level=0)
          .reset_index()
    )

    fig = go.Figure()
    for day in hourly["weekday"].unique():
        df_day = hourly[hourly["weekday"] == day]
        fig.add_trace(go.Scatter(
            x=df_day["hour"],
            y=df_day["energy_kwh"],
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




def reports_page():
    require_login()
    st.title("📄 Reports")

    # Load data
    df = load_energy_data()
    if df.empty:
        st.warning("⚠️ No energy data available.")
        return

    # Date‐range filter
    min_date = df["timestamp"].dt.date.min()
    max_date = df["timestamp"].dt.date.max()
    start_date, end_date = st.date_input(
        "Select date range",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
    mask = (df["timestamp"].dt.date >= start_date) & (df["timestamp"].dt.date <= end_date)
    df_filtered = df.loc[mask]

    st.subheader("Download Energy Data")
    csv_buffer = io.StringIO()
    df_filtered.to_csv(csv_buffer, index=False)
    st.download_button(
        label="Download CSV",
        data=csv_buffer.getvalue(),
        file_name=f"energy_data_{start_date}_{end_date}.csv",
        mime="text/csv"
    )

    # Also include anomalies
    st.subheader("Download Anomaly Report")
    detector = AnomalyDetector(contamination=0.01)
    df_flagged = detector.fit_detect(df, feature_cols=["energy_kwh"])
    anomalies = df_flagged[df_flagged["is_anomaly"]]

    if anomalies.empty:
        st.info("No anomalies detected in the full dataset.")
    else:
        csv_buffer2 = io.StringIO()
        anomalies.to_csv(csv_buffer2, index=False)
        st.download_button(
            label="Download Anomalies CSV",
            data=csv_buffer2.getvalue(),
            file_name=f"anomalies_{start_date}_{end_date}.csv",
            mime="text/csv"
        )


def recommendations_page():
    require_login()
    st.title("💡 Recommendations")

    # Load daily summary
    df = load_energy_data()
    if df.empty:
        st.warning("⚠️ No energy data available.")
        return

    # Daily totals
    daily = df.set_index("timestamp").resample("D")["energy_kwh"].sum()

    # Compute week-over-week change
    week_ago = daily.shift(7)
    pct_change = ((daily - week_ago) / week_ago) * 100

    st.subheader("Weekly Change in Daily Consumption")
    st.line_chart(pct_change, use_container_width=True)

    # Simple tip rules
    st.subheader("Auto‐Generated Tips")
    tips = []
    # 1) High peak day
    peak_day = daily.idxmax().date()
    tips.append({
        "severity": "High",
        "message": f"⚠️ {peak_day} had the highest consumption this period ({daily.max():.2f} kWh). Investigate unusual loads."
    })
    # 2) Increasing trend
    recent_change = pct_change.iloc[-1]
    if recent_change > 10:
        tips.append({
            "severity": "Medium",
            "message": f"🔺 Consumption up {recent_change:.1f}% vs. last week—encourage energy-saving behavior."
        })
    elif recent_change < -10:
        tips.append({
            "severity": "Low",
            "message": f"🔻 Consumption down {abs(recent_change):.1f}% vs. last week—good job on savings!"
        })
    else:
        tips.append({
            "severity": "Info",
            "message": "ℹ️ Consumption is stable week-over-week."
        })

    # 3) Night‐time usage
    # average usage 10pm–6am vs. daytime
    df["hour"] = df["timestamp"].dt.hour
    night = df[(df["hour"] >= 22) | (df["hour"] < 6)]["energy_kwh"].mean()
    day   = df[(df["hour"] >= 6) & (df["hour"] < 22)]["energy_kwh"].mean()
    if night > day * 0.5:
        tips.append({
            "severity": "Medium",
            "message": f"🌙 Night‐time usage ({night:.2f} kWh avg) is more than 50% of daytime—consider scheduling lights‐off automation."
        })

    # Display tips
    for tip in tips:
        if tip["severity"] == "High":
            st.error(tip["message"])
        elif tip["severity"] == "Medium":
            st.warning(tip["message"])
        else:
            st.info(tip["message"])


def alerts_page():
    require_login()
    st.title("🚨 Active Alerts")

    # First run the checker (so new alerts get created & emailed)
    from alerts import check_consecutive_anomalies
    check_consecutive_anomalies(threshold=2)

    # Load alerts
    alerts = get_alerts_collection()
    docs   = list(alerts.find().sort("detected_at", -1))

    if not docs:
        st.info("No active alerts.")
        return

    # Display a table of alerts
    df_alerts = pd.DataFrame(docs)
    df_alerts["detected_at"] = df_alerts["detected_at"].dt.strftime("%Y-%m-%d %H:%M:%S")
    st.dataframe(
        df_alerts[["sensor_id","detected_at","type","count","message"]],
        use_container_width=True
    )


def preferences_page():
    require_login()
    st.title("⚙️ User Preferences")

    users = get_user_collection()
    username = st.session_state.user["username"]

    # Fetch current user doc
    user_doc = users.find_one({"username": username})
    prefs = user_doc.get("preferences", {})

    # Default fallback values
    default_start = pd.to_datetime(prefs.get("date_range", [None, None])[0]) or pd.Timestamp.now() - pd.Timedelta(days=7)
    default_end = pd.to_datetime(prefs.get("date_range", [None, None])[1]) or pd.Timestamp.now()
    default_agg = prefs.get("aggregation", "Daily")
    default_thresh = prefs.get("anomaly_threshold", 1.0)

    # Form
    with st.form("preferences_form"):
        st.subheader("Date Range")
        date_range = st.date_input("Default Date Range", [default_start.date(), default_end.date()])

        st.subheader("Aggregation Level")
        aggregation = st.selectbox("Default Aggregation", ["Daily", "Weekly", "Monthly"], index=["Daily", "Weekly", "Monthly"].index(default_agg))

        st.subheader("Anomaly Detection")
        threshold = st.slider("Default Anomaly Threshold (%)", 0.1, 10.0, float(default_thresh), step=0.1)

        submitted = st.form_submit_button("Save Preferences")

    if submitted:
        users.update_one(
            {"username": username},
            {"$set": {
                "preferences": {
                    "date_range": [str(date_range[0]), str(date_range[1])],
                    "aggregation": aggregation,
                    "anomaly_threshold": float(threshold)
                }
            }}
        )
        st.success("✅ Preferences updated!")
        st.session_state.user["preferences"] = {
            "date_range": [str(date_range[0]), str(date_range[1])],
            "aggregation": aggregation,
            "anomaly_threshold": float(threshold)
        }

def user_management_page():
    require_login()
    st.title("🛠️ User Management")
    user_coll = get_user_collection()

    # Fetch all users
    users = list(user_coll.find({}, {"password": 0}))  # hide hashes
    if not users:
        st.info("No users found in the system.")
        return

    df = pd.DataFrame(users)
    df = df.rename(columns={
        "_id": "user_id",
        "username": "Username",
        "email": "Email",
        "first_name": "First Name",
        "last_name": "Last Name",
        "role": "Role",
        "created_at": "Created At",
        "disabled": "Disabled",  # optional field
    })

    # Show in a table
    st.subheader("Existing Users")
    st.dataframe(df.set_index("user_id"), use_container_width=True)


    #Pending role requests
    st.subheader("Pending Role Requests")
    pending = list(user_coll.find({
        "approved": False,
        "requested_role": {"$in": ["manager","admin"]}
    }))
    if pending:
        for u in pending:
            col1, col2, col3 = st.columns([2,2,1])
            col1.write(f"**{u['username']}**  ({u['email']})")
            col2.write(f"wants **{u['requested_role']}** access")
            if col3.button("✅ Approve", key=f"app_{u['_id']}"):
                user_coll.update_one(
                    {"_id": u["_id"]},
                    {"$set": {
                        "role": u["requested_role"],
                        "approved": True
                    }}
                )
                st.success(f"{u['username']} is now {u['requested_role']}.")
                st.experimental_rerun()
            if col3.button("❌ Reject", key=f"rej_{u['_id']}"):
                # either leave them as resident or delete, your choice
                user_coll.update_one(
                    {"_id": u["_id"]},
                    {"$set": {
                        "requested_role": "resident",
                        "approved": True
                    }}
                )
                st.info(f"{u['username']}'s request was rejected.")
                st.experimental_rerun()
    else:
        st.write("No pending requests.")
    st.markdown("---")


    st.markdown("---")
    st.subheader("Modify a User")

    # Select a user by id
    user_ids = df["user_id"].astype(str).tolist()
    selected = st.selectbox("Pick a user to modify", user_ids)

    if selected:
        user_doc = user_coll.find_one({"_id": ObjectId(selected)})
        # display current values
        st.write(f"**Username:** {user_doc['username']}")
        st.write(f"**Email:** {user_doc['email']}")
        st.write(f"**Current Role:** {user_doc['role']}")
        disabled = user_doc.get("disabled", False)

        # Role change
        new_role = st.selectbox("New Role", ["admin", "manager", "resident"], index=["admin","manager","resident"].index(user_doc["role"]))
        if st.button("Update Role"):
            user_coll.update_one(
                {"_id": ObjectId(selected)},
                {"$set": {"role": new_role}}
            )
            st.success(f"Role updated to `{new_role}`")
            st.experimental_rerun()

        # Enable / disable login
        toggle_label = "Revoke Access" if not disabled else "Restore Access"
        if st.button(toggle_label):
            user_coll.update_one(
                {"_id": ObjectId(selected)},
                {"$set": {"disabled": not disabled}}
            )
            st.success(f"Access {'revoked' if not disabled else 'restored'}")
            st.experimental_rerun()

        # Delete user
        if st.button("❌ Delete User"):
            user_coll.delete_one({"_id": ObjectId(selected)})
            st.success("User deleted")
            st.experimental_rerun()

    st.markdown("---")
    st.subheader("Add a New User")
    with st.form("add_user_form", clear_on_submit=True):
        un = st.text_input("Username")
        em = st.text_input("Email")
        fn = st.text_input("First Name")
        ln = st.text_input("Last Name")
        pw = st.text_input("Password", type="password")
        rl = st.selectbox("Role", ["admin", "manager", "resident"])
        submitted = st.form_submit_button("Create User")

    if submitted:
        if user_coll.find_one({"username": un}) or user_coll.find_one({"email": em}):
            st.error("Username or email already in use.")
        else:
            user_coll.insert_one({
                "username": un,
                "email": em,
                "first_name": fn,
                "last_name": ln,
                "password": hash_password(pw),
                "role": rl,
                "created_at": pd.Timestamp.now(),
                "disabled": False
            })
            st.success("New user added!")
            st.experimental_rerun()
def about_page():
    st.title("ℹ️ About EMADS")
    st.markdown(
        """
        **Energy Monitoring & Anomaly Detection System (EMADS)**  
        A Streamlit-powered web app that lets you track and analyze energy usage in your university hostel in real-time, detect anomalies, forecast future consumption, and generate actionable insights.

        ---
        #### 📊 Dashboard  
        - **Key Metrics**: Total, average, and peak kWh consumed, anomaly rate  
        - **Time Series Chart**: Interactive line plot of consumption over time  
        - **Daily Summary**: Per-day usage table and 7-day moving average  
        - **Weekday Breakdown**: Bar chart comparing each day of the week

        #### 🚨 Anomalies  
        - **Real-time Detection**: IsolationForest flags unusual consumption points  
        - **Visualization**: Consumption plot with anomaly markers  
        - **Details Table**: Timestamp, score, and flag for each anomaly

        #### 📈 Forecasting  
        - **ARIMA/Prophet Models**: Short-term load forecasting  
        - **Parameter Controls**: Choose model and horizon  
        - **Accuracy Metrics**: MAE & RMSE on test data

        #### 📊 Analytics  
        - **Aggregated Views**: Daily/weekly/monthly energy summaries  
        - **Distribution Plots**: Histograms & boxplots of consumption levels  
        - **Comparison Charts**: e.g. all Mondays vs. all Saturdays

        #### 📄 Reports  
        - **Exportable Reports**: CSV/PDF exports of energy data and anomalies  
        - **Scheduled Reports**: Weekly summary emailed to managers/admins

        #### 💡 Recommendations  
        - **Automated Tips**: Energy-saving advice based on usage patterns  
        - **Threshold Alerts**: Guidance when consumption crosses set limits

        #### ⚙️ Preferences  
        - **User Settings**: Default time-range, asset selection, alert thresholds  
        - **Profile**: View and update your user details

        #### 🛠️ User Management *(Admin only)*  
        - **CRUD Users**: Add, delete, enable/disable accounts  
        - **Role Assignment**: Grant admin, manager, or resident privileges  

        ---  
        **Contact & Support**  
        If you run into any issues or have ideas, reach out to your system administrator or open a GitHub issue in the project repo.
        """
    )


def main():
    st.sidebar.title("Navigation")

    # if registration just happened, force show login
    if st.session_state.next_page == "Login":
        st.session_state.next_page = None
        login_page()
        return 
    

    if not st.session_state.user:
        choice = st.sidebar.radio("Go to", ["Login", "Register"])
        if choice == "Login":
            login_page()
        else:
            registration_page()
    else:
        # Logged in: show role-based menu
        role = st.session_state.user["role"]
        pages = ["Dashboard", "Reports", "Analytics", "Recommendations", "Preferences", "About"]
        if role in ("admin", "manager"):
            pages += ["Forecasting", "Anomalies","Alerts","User Management"]
        selection = st.sidebar.radio("Go to", pages)
        st.sidebar.button("Logout", on_click = logout)

        #Dispatch
        if selection == "Dashboard":
            dashboard_page()
        elif selection == "Anomalies":
            anomalies_page()
        elif selection == "Forecasting":
            forecasting_page()
        elif selection == "Analytics":
            analytics_page()
        elif selection == "Reports":
            reports_page()
        elif selection == "Recommendations":
            recommendations_page()
        elif selection == "Alerts":
            alerts_page()
        elif selection == "Preferences":
            preferences_page()
        elif selection == "About":
            about_page()
        elif selection == "User Management":
            user_management_page()

    


if __name__ == "__main__":
    main()

