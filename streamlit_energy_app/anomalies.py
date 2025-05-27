import streamlit as st
from require_login import require_login
from db import get_energy_collection, get_alerts_collection, get_user_collection, get_communications_collection, load_energy_data
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import plotly.express as px
import plotly.graph_objects as go
from email_utils import send_email
import joblib
import os
from sklearn.preprocessing import StandardScaler

# Cache the model loading
@st.cache_resource(ttl=3600)  # Cache for 1 hour
def load_model():
    """Load and cache the Isolation Forest model"""
    try:
        model_path = os.path.join(os.path.dirname(__file__), 'new_models', 'IF_model.joblib')
        return joblib.load(model_path)
    except FileNotFoundError:
        st.error("Error: 'IF_model.joblib' not found in new_models directory.")
        st.stop()

# Load the model once and cache it
loaded_if_model = load_model()

# Cache the data loading function with a shorter TTL
@st.cache_data(ttl=60)  # Cache for 1 minute
def load_energy_data(start_time, end_time):
    """Load energy data from MongoDB with caching"""
    energy_collection = get_energy_collection()
    # Optimize query by only fetching needed fields and using proper sort
    energy_data = list(energy_collection.find(
        {
            "timestamp": {
                "$gte": start_time,
                "$lte": end_time
            }
        },
        {
            "_id": 0,
            "timestamp": 1,
            "energy_wh": 1
        }
    ).sort("timestamp", 1))
    
    if not energy_data:
        return None
    
    df = pd.DataFrame(energy_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

# Cache the anomaly detection functions
@st.cache_data(ttl=300)
def detect_statistical_anomalies(df, window=24, std_threshold=4):
    """Detect anomalies using statistical methods (rolling mean and standard deviation)"""
    # Calculate rolling statistics
    df['rolling_mean'] = df['energy_wh'].rolling(window=window).mean()
    df['rolling_std'] = df['energy_wh'].rolling(window=window).std()
    
    # Calculate z-scores
    df['z_score'] = (df['energy_wh'] - df['rolling_mean']) / df['rolling_std']
    
    # Detect anomalies (more stringent threshold)
    df['statistical_anomaly'] = abs(df['z_score']) > std_threshold
    
    # Calculate anomaly score (normalized z-score)
    df['statistical_score'] = abs(df['z_score']) / std_threshold
    
    return df

@st.cache_data(ttl=300)
def detect_consecutive_anomalies(df, min_consecutive=8):
    """Detect periods of consecutive anomalies"""
    # Initialize consecutive anomaly column
    df['consecutive_anomaly'] = False
    
    # Find consecutive anomalies (increased minimum consecutive points)
    anomaly_mask = df['statistical_anomaly']
    consecutive_count = 0
    
    for i in range(len(df)):
        if anomaly_mask.iloc[i]:
            consecutive_count += 1
            if consecutive_count >= min_consecutive:
                df.loc[df.index[i-min_consecutive+1:i+1], 'consecutive_anomaly'] = True
        else:
            consecutive_count = 0
    
    return df

@st.cache_data(ttl=300)
def detect_energy_spikes(df, spike_threshold=3.0):
    """Detect sudden spikes in energy consumption"""
    # Calculate percentage change
    df['pct_change'] = df['energy_wh'].pct_change()
    
    # Detect spikes (more stringent threshold)
    df['energy_spike'] = df['pct_change'] > spike_threshold
    
    # Calculate spike score
    df['spike_score'] = df['pct_change'] / spike_threshold
    
    return df

# Remove caching from detect_anomalies since it uses an unhashable model parameter
def detect_anomalies(df, _model):
    """Detect anomalies using the Isolation Forest model with severity levels"""
    try:
        # Get anomaly scores
        scores = _model.decision_function(df[['energy_wh']].values)
        
        # Calculate thresholds based on score distribution
        high_threshold = np.percentile(scores, 0.5)    # Top 0.5% most anomalous
        medium_threshold = np.percentile(scores, 1.0)  # Top 1% most anomalous
        low_threshold = np.percentile(scores, 2.0)     # Top 2% most anomalous
        
        # Categorize anomalies
        df['anomaly_score'] = scores
        df['anomaly'] = _model.predict(df[['energy_wh']].values)
        
        # Add severity levels
        df['severity'] = 'normal'
        df.loc[df['anomaly_score'] <= high_threshold, 'severity'] = 'high'
        df.loc[(df['anomaly_score'] > high_threshold) & 
               (df['anomaly_score'] <= medium_threshold), 'severity'] = 'medium'
        df.loc[(df['anomaly_score'] > medium_threshold) & 
               (df['anomaly_score'] <= low_threshold), 'severity'] = 'low'
        
        # Additional filtering to ensure anomalies are significant
        df['z_score'] = (df['energy_wh'] - df['energy_wh'].mean()) / df['energy_wh'].std()
        df.loc[abs(df['z_score']) < 2.0, 'anomaly'] = 1
        df.loc[abs(df['z_score']) < 2.0, 'severity'] = 'normal'
        
        # Process anomalies - include all severity levels
        anomalies = df[df['severity'].isin(['high', 'medium', 'low'])].copy()
        
        if not anomalies.empty:
            # Get collections once
            alerts_collection = get_alerts_collection()
            users = get_user_collection()
            communications = get_communications_collection()
            
            # Get admin/manager users once
            admin_users = list(users.find({"role": {"$in": ["admin", "manager"]}}))
            admin_emails = [user['email'] for user in admin_users if user.get('email')]
            
            # Clear old alerts before creating new ones
            alerts_collection.delete_many({
                "type": "isolation_forest",
                "timestamp": {"$lt": df['timestamp'].min()}
            })
            
            # Prepare alerts in batch
            alerts = []
            notifications = []
            
            for _, row in anomalies.iterrows():
                severity = row['severity']
                alert = {
                    'timestamp': row['timestamp'],
                    'type': 'isolation_forest',
                    'severity': severity,
                    'message': f"""
                    Anomaly detected in energy consumption:
                    - Time: {row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
                    - Energy Consumption: {row['energy_wh']:.2f} kWh
                    - Anomaly Score: {abs(row['anomaly_score']):.3f}
                    - Severity: {severity.capitalize()}
                    - Type: Isolation Forest
                    """,
                    'energy_consumption': float(row['energy_wh']),
                    'anomaly_score': float(abs(row['anomaly_score'])),
                    'resolved': False
                }
                alerts.append(alert)
                
                # Prepare notifications for each admin user
                for user in admin_users:
                    notifications.append({
                        'username': user['username'],
                        'title': f'New Anomaly Alert: {severity.capitalize()} Severity',
                        'message': alert['message'],
                        'type': 'system_message',
                        'timestamp': datetime.now(),
                        'read': False
                    })
            
            # Batch insert alerts and notifications
            if alerts:
                alerts_collection.insert_many(alerts)
            if notifications:
                communications.insert_many(notifications)
            
            # Send email notifications in batch if there are any admin emails
            if admin_emails:
                email_subject = "EMADS: New Anomaly Alerts"
                email_body = "\n\n".join([alert['message'] for alert in alerts])
                send_email(admin_emails, email_subject, email_body)
        
        return df
    except Exception as e:
        st.error(f"Error detecting anomalies: {str(e)}")
        return df

def generate_alerts(df):
    """Generate alerts for detected anomalies"""
    try:
        # Process anomalies - include all severity levels
        anomalies = df[df['severity'].isin(['high', 'medium', 'low'])].copy()
        
        if not anomalies.empty:
            # Get collections once
            alerts_collection = get_alerts_collection()
            users = get_user_collection()
            communications = get_communications_collection()
            
            # Get admin/manager users once
            admin_users = list(users.find({"role": {"$in": ["admin", "manager"]}}))
            admin_emails = [user['email'] for user in admin_users if user.get('email')]
            
            # Clear old alerts before creating new ones
            alerts_collection.delete_many({
                "type": "isolation_forest",
                "timestamp": {"$lt": df['timestamp'].min()}
            })
            
            # Prepare alerts in batch
            alerts = []
            notifications = []
            
            for _, row in anomalies.iterrows():
                severity = row['severity']
                alert = {
                    'timestamp': row['timestamp'],
                    'type': 'isolation_forest',
                    'severity': severity,
                    'message': f"""
                    Anomaly detected in energy consumption:
                    - Time: {row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
                    - Energy Consumption: {row['energy_wh']:.2f} kWh
                    - Anomaly Score: {abs(row['anomaly_score']):.3f}
                    - Severity: {severity.capitalize()}
                    - Type: Isolation Forest
                    """,
                    'energy_consumption': float(row['energy_wh']),
                    'anomaly_score': float(abs(row['anomaly_score'])),
                    'resolved': False
                }
                alerts.append(alert)
                
                # Prepare notifications for each admin user
                for user in admin_users:
                    notifications.append({
                        'username': user['username'],
                        'title': f'New Anomaly Alert: {severity.capitalize()} Severity',
                        'message': alert['message'],
                        'type': 'system_message',
                        'timestamp': datetime.now(),
                        'read': False
                    })
            
            # Batch insert alerts and notifications
            if alerts:
                alerts_collection.insert_many(alerts)
            if notifications:
                communications.insert_many(notifications)
            
            # Send email notifications in batch if there are any admin emails
            if admin_emails:
                email_subject = "EMADS: New Anomaly Alerts"
                email_body = "\n\n".join([alert['message'] for alert in alerts])
                send_email(admin_emails, email_subject, email_body)
            
            return len(alerts)
        return 0
    except Exception as e:
        st.error(f"Error generating alerts: {str(e)}")
        return 0

def load_anomaly_model():
    """Load the Isolation Forest model with caching"""
    @st.cache_resource(ttl=3600)  # Cache for 1 hour
    def load_model():
        try:
            models_dir = os.path.join(os.path.dirname(__file__), "new_models")
            model_path = os.path.join(models_dir, "isolation_forest_model.joblib")
            
            if not os.path.exists(model_path):
                return None
                
            return joblib.load(model_path)
        except Exception as e:
            st.error(f"Error loading anomaly model: {str(e)}")
            return None
    
    return load_model()

def train_anomaly_model(df):
    """Train a new Isolation Forest model with optimized parameters"""
    try:
        # Prepare data
        data = df[['energy_wh']].values
        
        # Initialize model with more balanced parameters
        model = IsolationForest(
            n_estimators=200,      # Increased number of trees for better accuracy
            contamination=0.005,   # 0.5% expected anomalies
            random_state=42,       # For reproducibility
            n_jobs=-1,            # Use all available cores
            max_samples='auto'     # Use all samples for better detection
        )
        
        # Train the model
        model.fit(data)
        
        # Save the model
        models_dir = os.path.join(os.path.dirname(__file__), "new_models")
        os.makedirs(models_dir, exist_ok=True)
        model_path = os.path.join(models_dir, "isolation_forest_model.joblib")
        joblib.dump(model, model_path)
        
        return model
    except Exception as e:
        st.error(f"Error training anomaly model: {str(e)}")
        return None

def anomalies_page():
    require_login()
    st.title("Energy Consumption Anomaly Detection")
    st.markdown("""
        This page uses Isolation Forest to detect anomalies in energy consumption patterns.
        Anomalies are categorized by severity level based on their deviation from normal patterns.
    """)

    # Date range selector
    st.markdown("### Select Time Range")
    time_range = st.selectbox(
        "Choose a time range",
        ["Last 24 hours", "Last 7 days", "Last 30 days", "Last 90 days", "All time"],
        index=4  # Default to "All time"
    )

    # Calculate time range
    now = datetime.now()
    if time_range == "Last 24 hours":
        start_time = now - timedelta(days=1)
        end_time = now
    elif time_range == "Last 7 days":
        start_time = now - timedelta(days=7)
        end_time = now
    elif time_range == "Last 30 days":
        start_time = now - timedelta(days=30)
        end_time = now
    elif time_range == "Last 90 days":
        start_time = now - timedelta(days=90)
        end_time = now
    else:  # All time
        start_time = datetime.min
        end_time = now

    # Load data with caching
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def load_data(start_time, end_time):
        return load_energy_data(start_time, end_time)

    # Load model with caching
    @st.cache_resource(ttl=3600)  # Cache for 1 hour
    def get_model():
        model = load_anomaly_model()
        if model is None:
            df = load_data(start_time, end_time)
            if df is not None and not df.empty:
                model = train_anomaly_model(df)
        return model

    # Load data and model
    with st.spinner('Loading data and model...'):
        df = load_data(start_time, end_time)
        if df is None or df.empty:
            st.warning("No energy data available for the selected time range.")
            return

        model = get_model()
        if model is None:
            st.error("Failed to load or train the anomaly detection model.")
            return

    # Detect anomalies and generate alerts
    with st.spinner('Detecting anomalies and generating alerts...'):
        df = detect_anomalies(df, model)

    # Cache the metrics calculation
    @st.cache_data(ttl=60)  # Cache for 1 minute
    def calculate_metrics(df):
        total_points = len(df)
        anomalies = (df['anomaly'] == -1).sum()
        high_severity = (df['severity'] == 'high').sum()
        medium_severity = (df['severity'] == 'medium').sum()
        low_severity = (df['severity'] == 'low').sum()
        total_anomalies = high_severity + medium_severity + low_severity
        anomaly_rate = (total_anomalies / total_points * 100) if total_points > 0 else 0
        return {
            'total_points': total_points,
            'total_anomalies': total_anomalies,
            'high_severity': high_severity,
            'medium_severity': medium_severity,
            'low_severity': low_severity,
            'anomaly_rate': anomaly_rate
        }

    # Display metrics
    st.subheader("Anomaly Detection Metrics")
    metrics = calculate_metrics(df)
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Data Points", metrics['total_points'])
    with col2:
        st.metric("Anomalies Detected", metrics['total_anomalies'])
    with col3:
        st.metric("High Severity", metrics['high_severity'])
    with col4:
        st.metric("Medium/Low Severity", metrics['medium_severity'] + metrics['low_severity'])
    with col5:
        st.metric("Anomaly Rate", f"{metrics['anomaly_rate']:.2f}%")

    # Add a small note about the metrics
    st.caption("Note: Anomalies are categorized by severity level based on their deviation from normal patterns.")

    # Cache the visualization data
    @st.cache_data(ttl=60)  # Cache for 1 minute
    def prepare_visualization_data(df):
        # Prepare data for time series plot
        normal_df = df[df['anomaly'] == 1]
        anomaly_dfs = {
            'high': df[(df['anomaly'] == -1) & (df['severity'] == 'high')],
            'medium': df[(df['anomaly'] == -1) & (df['severity'] == 'medium')],
            'low': df[(df['anomaly'] == -1) & (df['severity'] == 'low')]
        }
        
        # Prepare distribution data
        distribution = df['severity'].value_counts()
        
        return normal_df, anomaly_dfs, distribution

    # Generate visualizations
    with st.spinner('Generating visualizations...'):
        normal_df, anomaly_dfs, distribution = prepare_visualization_data(df)

        # Plot results
        fig = go.Figure()

        # Add normal points
        fig.add_trace(go.Scatter(
            x=normal_df['timestamp'],
            y=normal_df['energy_wh'],
            mode='lines',
            name='Normal',
            line=dict(color='#1f77b4', width=1)
        ))

        # Add anomalies by severity
        for severity, color in [('high', 'red'), ('medium', 'orange'), ('low', 'yellow')]:
            if not anomaly_dfs[severity].empty:
                fig.add_trace(go.Scatter(
                    x=anomaly_dfs[severity]['timestamp'],
                    y=anomaly_dfs[severity]['energy_wh'],
                    mode='markers',
                    name=f'{severity.capitalize()} Severity',
                    marker=dict(color=color, size=10, symbol='star')
                ))

        fig.update_layout(
            title='Energy Consumption with Detected Anomalies',
            xaxis_title='Timestamp',
            yaxis_title='Energy (Wh)',
            height=600,
            showlegend=True,
            template='plotly_white',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)

        # Add distribution pie chart
        st.subheader("Data Distribution")
        
        # Define colors for each severity level
        colors = ['#1f77b4', '#d62728', '#ff7f0e', '#ffd700']  # Blue, Red, Orange, Yellow
        
        # Create pie chart
        fig_pie = go.Figure(data=[go.Pie(
            labels=distribution.index,
            values=distribution.values,
            hole=.3,
            marker_colors=colors,
            textinfo='percent+label',
            textposition='inside'
        )])
        
        fig_pie.update_layout(
            title='Distribution of Normal vs Anomalous Values',
            height=400,
            showlegend=True,
            template='plotly_white'
        )
        
        # Display pie chart in a column next to metrics
        col1, col2 = st.columns([2, 1])
        with col1:
            st.plotly_chart(fig_pie, use_container_width=True)
        with col2:
            st.markdown("### Value Distribution")
            for severity, count in distribution.items():
                st.metric(
                    f"{severity.capitalize()} Values",
                    count,
                    f"{count/len(df)*100:.1f}% of total"
                )

        # Display anomalies table
        st.subheader("Detected Anomalies")
        anomalies_df = df[df['anomaly'] == -1].copy()
        anomalies_df['timestamp'] = anomalies_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        anomalies_display = anomalies_df[['timestamp', 'energy_wh', 'anomaly_score', 'severity']].rename(
            columns={
                'timestamp': 'Time',
                'energy_wh': 'Energy (Wh)',
                'anomaly_score': 'Anomaly Score',
                'severity': 'Severity'
            }
        )
        st.dataframe(anomalies_display, use_container_width=True)

    # Generate alerts after showing results
    if st.button("Generate Alerts for Detected Anomalies"):
        with st.spinner('Generating alerts...'):
            num_alerts = generate_alerts(df)
            if num_alerts > 0:
                st.success(f"Successfully generated {num_alerts} alerts!")
            else:
                st.info("No new alerts were generated.")
