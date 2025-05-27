import streamlit as st
from require_login import require_login
from db import get_alerts_collection, get_user_collection, get_communications_collection
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from email_utils import send_email

def alerts_page():
    require_login()
    st.title("Alerts Dashboard")
    
    # Add auto-refresh
    st.empty()
    placeholder = st.empty()
    
    # Get current time
    now = datetime.now()
    start_time = now - timedelta(days=30)  # Show last 30 days by default
    
    # Get alerts collection
    alerts_collection = get_alerts_collection()
    
    # Get alerts with auto-refresh
    @st.cache_data(ttl=10)  # Cache for 10 seconds
    def get_alerts():
        return list(alerts_collection.find({
            "timestamp": {"$gte": start_time}
        }).sort("timestamp", -1))
    
    # Get alerts
    alerts = get_alerts()
    
    # Convert to DataFrame
    df = pd.DataFrame(alerts)
    
    if len(df) == 0:
        st.info("No alerts found in the selected time range.")
        return
        
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Standardize severity levels
    severity_map = {
        'high': 'High',
        'medium': 'Medium',
        'low': 'Low',
        'normal': 'Normal'
    }
    df['severity'] = df['severity'].str.lower().map(severity_map).fillna('Normal')
    
    # Calculate statistics
    total_alerts = len(df)
    high_severity = len(df[df['severity'] == 'High'])
    medium_severity = len(df[df['severity'] == 'Medium'])
    low_severity = len(df[df['severity'] == 'Low'])
    alerts_per_day = total_alerts / ((now - start_time).days or 1)
    
    # Display statistics with auto-refresh
    with placeholder.container():
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Alerts", total_alerts)
        with col2:
            st.metric("High Severity", high_severity)
        with col3:
            st.metric("Medium Severity", medium_severity)
        with col4:
            st.metric("Low Severity", low_severity)
        
        # Filter options
        st.subheader("Filter Alerts")
        severity_filter = st.multiselect(
            "Severity",
            ['High', 'Medium', 'Low'],
            default=['High', 'Medium', 'Low']
        )
        
        # Apply filters
        if severity_filter:
            df = df[df['severity'].isin(severity_filter)]
        
        # Visualizations
        st.subheader("Alert Analysis")
        
        # Time series plot
        fig1 = px.line(
            df.groupby(df['timestamp'].dt.date).size().reset_index(),
            x='timestamp',
            y=0,
            title="Alerts Over Time",
            labels={'timestamp': 'Date', '0': 'Number of Alerts'}
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        # Severity distribution
        fig2 = px.pie(
            df,
            names='severity',
            title="Alert Distribution by Severity",
            color='severity',
            color_discrete_map={
                'High': 'red',
                'Medium': 'orange',
                'Low': 'yellow',
                'Normal': 'blue'
            }
        )
        st.plotly_chart(fig2, use_container_width=True)
        
        # Display alerts table
        st.subheader("Recent Alerts")
        for _, alert in df.iterrows():
            with st.expander(f"{alert['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} - {alert['severity']} Severity"):
                st.write(alert['message'])
                if st.button("Mark as Resolved", key=f"resolve_{alert['_id']}"):
                    alerts_collection.update_one(
                        {"_id": alert['_id']},
                        {"$set": {"resolved": True}}
                    )
                    st.success("Alert marked as resolved!")
                    st.rerun()