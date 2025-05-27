import pandas as pd
from datetime import datetime, timedelta
from db import get_db, get_user_collection, get_alerts_collection
from anomaly_detection.anomaly_detector import AnomalyDetector
from email_utils import send_email
from dotenv import load_dotenv
import numpy as np

load_dotenv()
import os

def get_notification_recipients(alert_type):
    """Get recipients based on their notification preferences"""
    users = get_user_collection()
    recipients = []
    
    for user in users.find({"role": {"$in": ["admin", "manager"]}}):
        prefs = user.get("preferences", {})
        notifications = prefs.get("notifications", {})
        
        # Check if user has enabled notifications for this alert type
        if notifications.get("alerts", True):  # Default to True if not set
            if alert_type == "consecutive_anomalies" and notifications.get("alerts", True):
                recipients.append(user["email"])
            elif alert_type == "energy_spike" and notifications.get("alerts", True):
                recipients.append(user["email"])
            elif alert_type == "unusual_pattern" and notifications.get("alerts", True):
                recipients.append(user["email"])
    
    return recipients

def check_consecutive_anomalies(threshold=2):
    db = get_db()
    readings = db[os.getenv("MONGO_ALERTS_COLLECTION")]
    alerts = get_alerts_collection()
    users = get_user_collection()

    # 1) Pull last 'threshold' readings
    docs = list(readings.find()
                .sort("timestamp", -1)
                .limit(threshold))
    if len(docs) < threshold:
        return

    # 2) Convert to DataFrame and check for anomalies
    df = pd.DataFrame(docs)
    
    # If no anomaly scores exist, run anomaly detection
    if "anomaly_score" not in df.columns:
        detector = AnomalyDetector()
        try:
            # Run anomaly detection
            results = detector.detect_anomalies(df)
            df = results
            
            # Update readings with anomaly scores
            for _, row in df.iterrows():
                readings.update_one(
                    {"_id": row["_id"]},
                    {"$set": {
                        "anomaly_score": row["anomaly_score"],
                        "is_anomaly": row["is_anomaly"]
                    }}
                )
        except Exception as e:
            print(f"Error running anomaly detection: {e}")
            return
    
    # Consider a reading anomalous if its score is below -0.5 (typical threshold for isolation forest)
    if "is_anomaly" not in df.columns:
        df["is_anomaly"] = df["anomaly_score"] < -0.5
    
    if not df["is_anomaly"].all():
        return  # no run of anomalies

    sensor = df.loc[0, "sensor_id"]
    last_ts = df.loc[0, "timestamp"]

    # 3) Has an alert already been created for this run?
    exists = alerts.find_one({
        "sensor_id": sensor,
        "type": "consecutive_anomalies",
        "detected_at": {"$gte": last_ts - timedelta(minutes=5)}  # 5-minute window
    })

    if exists:
        return  # already alerted for this event

    # 4) Create alert document
    alert_doc = {
        "sensor_id": sensor,
        "detected_at": last_ts,
        "type": "consecutive_anomalies",
        "count": threshold,
        "notified": False,
        "message": f"{threshold} successive anomalies detected on sensor {sensor} at {last_ts}",
        "severity": "high" if threshold >= 3 else "medium"
    }

    alerts.insert_one(alert_doc)

    # 5) Notify via email based on user preferences
    recipients = get_notification_recipients("consecutive_anomalies")
    if recipients:
        subject = f"EMADS Alert: {threshold} consecutive anomalies"
        body = alert_doc["message"]
        send_email(recipients, subject, body)

        # 6) Mark notified
        alerts.update_one(
            {"_id": alert_doc["_id"]},
            {"$set": {"notified": True}}
        )

def check_energy_spike(threshold_percent=50):
    """Check for sudden spikes in energy consumption"""
    db = get_db()
    readings = db[os.getenv("MONGO_ALERTS_COLLECTION")]
    alerts = get_alerts_collection()
    users = get_user_collection()

    # Get last 24 hours of readings
    last_24h = datetime.now() - timedelta(hours=24)
    docs = list(readings.find({"timestamp": {"$gte": last_24h}})
                .sort("timestamp", -1))
    
    if len(docs) < 2:
        return

    df = pd.DataFrame(docs)
    df = df.sort_values("timestamp")
    
    # Calculate percentage change
    df["pct_change"] = df["energy_wh"].pct_change() * 100
    
    # Check for spikes
    spikes = df[df["pct_change"] > threshold_percent]
    
    for _, spike in spikes.iterrows():
        # Check if alert already exists
        exists = alerts.find_one({
            "sensor_id": spike["sensor_id"],
            "type": "energy_spike",
            "detected_at": {"$gte": spike["timestamp"] - timedelta(minutes=5)}
        })
        
        if exists:
            continue
            
        # Create alert
        alert_doc = {
            "sensor_id": spike["sensor_id"],
            "detected_at": spike["timestamp"],
            "type": "energy_spike",
            "value": spike["energy_wh"],
            "pct_change": spike["pct_change"],
            "notified": False,
            "message": f"Energy spike detected: {spike['pct_change']:.1f}% increase on sensor {spike['sensor_id']}",
            "severity": "high" if spike["pct_change"] > 100 else "medium"
        }
        
        alerts.insert_one(alert_doc)
        
        # Notify based on user preferences
        recipients = get_notification_recipients("energy_spike")
        if recipients:
            subject = f"EMADS Alert: Energy Spike Detected"
            body = alert_doc["message"]
            send_email(recipients, subject, body)
            
            # Mark notified
            alerts.update_one(
                {"_id": alert_doc["_id"]},
                {"$set": {"notified": True}}
            )

def check_unusual_patterns(window_hours=24):
    """Check for unusual patterns in energy consumption"""
    db = get_db()
    readings = db[os.getenv("MONGO_ALERTS_COLLECTION")]
    alerts = get_alerts_collection()
    users = get_user_collection()

    # Get readings for the window
    window_start = datetime.now() - timedelta(hours=window_hours)
    docs = list(readings.find({"timestamp": {"$gte": window_start}})
                .sort("timestamp", -1))
    
    if len(docs) < 24:  # Need at least 24 readings for meaningful analysis
        return

    df = pd.DataFrame(docs)
    df = df.sort_values("timestamp")
    
    # Calculate hourly statistics
    df["hour"] = df["timestamp"].dt.hour
    hourly_stats = df.groupby("hour")["energy_wh"].agg(["mean", "std"]).reset_index()
    
    # Check for unusual patterns
    for hour in range(24):
        hour_data = df[df["hour"] == hour]
        if len(hour_data) == 0:
            continue
            
        mean = hourly_stats.loc[hour, "mean"]
        std = hourly_stats.loc[hour, "std"]
        
        # Check if current readings are significantly different
        unusual = hour_data[abs(hour_data["energy_wh"] - mean) > 2 * std]
        
        for _, reading in unusual.iterrows():
            # Check if alert already exists
            exists = alerts.find_one({
                "sensor_id": reading["sensor_id"],
                "type": "unusual_pattern",
                "detected_at": {"$gte": reading["timestamp"] - timedelta(minutes=5)}
            })
            
            if exists:
                continue
                
            # Create alert
            alert_doc = {
                "sensor_id": reading["sensor_id"],
                "detected_at": reading["timestamp"],
                "type": "unusual_pattern",
                "value": reading["energy_wh"],
                "expected_mean": mean,
                "notified": False,
                "message": f"Unusual energy pattern detected at hour {hour}: {reading['energy_wh']:.1f} Wh (expected {mean:.1f} ± {2*std:.1f} Wh)",
                "severity": "medium"
            }
            
            alerts.insert_one(alert_doc)
            
            # Notify based on user preferences
            recipients = get_notification_recipients("unusual_pattern")
            if recipients:
                subject = f"EMADS Alert: Unusual Energy Pattern Detected"
                body = alert_doc["message"]
                send_email(recipients, subject, body)
                
                # Mark notified
                alerts.update_one(
                    {"_id": alert_doc["_id"]},
                    {"$set": {"notified": True}}
                )

def create_alert(timestamp, energy_value, anomaly_score, severity, message):
    """
    Create an alert in the database and notify users.
    
    Args:
        timestamp (datetime): When the anomaly was detected
        energy_value (float): The energy value that triggered the alert
        anomaly_score (float): The anomaly score from the model
        severity (str): Alert severity ('high', 'medium', 'low')
        message (str): Description of the alert
    """
    alerts_collection = get_alerts_collection()
    communications_collection = get_db()["communications"]
    
    # Create alert document
    alert = {
        "timestamp": timestamp,
        "energy_wh": energy_value,
        "anomaly_score": anomaly_score,
        "severity": severity,
        "message": message,
        "type": "anomaly_isolation_forest",
        "resolved": False,
        "created_at": datetime.now()
    }
    
    # Insert alert
    result = alerts_collection.insert_one(alert)
    
    # Get admin and manager users
    users = get_user_collection()
    recipients = []
    for user in users.find({"role": {"$in": ["admin", "manager"]}}):
        recipients.append(user["email"])
        
        # Add message to user's communication inbox
        communication = {
            "user_id": user["_id"],
            "type": "alert",
            "title": f"Anomaly Alert: {severity.capitalize()} Severity",
            "message": message,
            "timestamp": datetime.now(),
            "read": False,
            "alert_id": result.inserted_id
        }
        communications_collection.insert_one(communication)
    
    # Send email notifications
    if recipients:
        subject = f"EMADS Alert: {severity.capitalize()} Severity Anomaly Detected"
        body = f"""
        Anomaly Alert Details:
        ---------------------
        Severity: {severity.capitalize()}
        Time: {timestamp}
        Energy Value: {energy_value:.2f} Wh
        Anomaly Score: {anomaly_score:.3f}
        
        Message: {message}
        
        Please check the EMADS system for more details.
        """
        
        try:
            send_email(recipients, subject, body)
        except Exception as e:
            print(f"Error sending email notification: {str(e)}")

def determine_severity(anomaly_score):
    """
    Determine alert severity based on anomaly score.
    
    Args:
        anomaly_score (float): The anomaly score from the model
        
    Returns:
        str: Severity level ('high', 'medium', 'low')
    """
    # Use the same thresholds as the anomalies page
    high_threshold = -0.35    # Top 0.5% most anomalous
    medium_threshold = -0.25  # Top 1% most anomalous
    low_threshold = -0.20     # Top 2% most anomalous
    
    if anomaly_score <= high_threshold:
        return "high"
    elif anomaly_score <= medium_threshold:
        return "medium"
    elif anomaly_score <= low_threshold:
        return "low"
    else:
        return "normal"

def generate_alert_message(energy_value, anomaly_score):
    """
    Generate a descriptive message for the alert.
    
    Args:
        energy_value (float): The energy value that triggered the alert
        anomaly_score (float): The anomaly score from the model
        
    Returns:
        str: Alert message
    """
    severity = determine_severity(anomaly_score)
    if severity == "high":
        return f"Critical energy consumption detected: {energy_value:.2f} Wh (Anomaly Score: {anomaly_score:.2f})"
    elif severity == "medium":
        return f"Unusual energy consumption detected: {energy_value:.2f} Wh (Anomaly Score: {anomaly_score:.2f})"
    else:
        return f"Minor energy consumption anomaly detected: {energy_value:.2f} Wh (Anomaly Score: {anomaly_score:.2f})"

def generate_anomaly_report(df, anomaly_scores):
    """
    Generate a comprehensive anomaly report.
    
    Args:
        df (pd.DataFrame): DataFrame containing energy data
        anomaly_scores (np.array): Array of anomaly scores
        
    Returns:
        dict: Report containing anomaly statistics and details
    """
    # Calculate anomaly statistics
    total_points = len(df)
    anomaly_df = df[df['severity'] != 'Normal']
    total_anomalies = len(anomaly_df)
    anomaly_rate = (total_anomalies / total_points) * 100 if total_points > 0 else 0
    
    # Calculate severity distribution
    severity_counts = anomaly_df['severity'].value_counts().to_dict()
    
    # Get most recent anomalies
    recent_anomalies = anomaly_df.sort_values('timestamp', ascending=False).head(5)
    
    # Calculate average anomaly score
    avg_anomaly_score = anomaly_df['anomaly_score'].mean() if not anomaly_df.empty else 0
    
    return {
        "total_points": total_points,
        "total_anomalies": total_anomalies,
        "anomaly_rate": anomaly_rate,
        "severity_distribution": severity_counts,
        "recent_anomalies": recent_anomalies,
        "avg_anomaly_score": avg_anomaly_score,
        "timestamp": datetime.now()
    }

def send_anomaly_report(report, recipients):
    """
    Send anomaly report to all recipients.
    
    Args:
        report (dict): Anomaly report data
        recipients (list): List of recipient user documents
    """
    communications = get_db()["communications"]
    
    # Create email content
    email_subject = f"EMADS Anomaly Report - {report['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"
    
    # Build email body
    email_body = f"""
    EMADS Anomaly Detection Report
    =============================
    Generated: {report['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
    
    Summary:
    -------
    Total Data Points Analyzed: {report['total_points']}
    Total Anomalies Detected: {report['total_anomalies']}
    Anomaly Rate: {report['anomaly_rate']:.1f}%
    Average Anomaly Score: {report['avg_anomaly_score']:.3f}
    
    Severity Distribution:
    --------------------
    """
    
    for severity, count in report['severity_distribution'].items():
        email_body += f"{severity}: {count} anomalies\n"
    
    email_body += "\nMost Recent Anomalies:\n-------------------\n"
    for _, anomaly in report['recent_anomalies'].iterrows():
        email_body += f"""
        Time: {anomaly['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
        Severity: {anomaly['severity']}
        Energy Value: {anomaly['energy_wh']:.2f} Wh
        Anomaly Score: {anomaly['anomaly_score']:.3f}
        """
    
    email_body += "\nPlease check the EMADS system for more details."
    
    # Send to each recipient
    for recipient in recipients:
        # Add to communications inbox
        communication = {
            "username": recipient["username"],
            "type": "anomaly_report",
            "title": f"Anomaly Detection Report - {report['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}",
            "message": email_body,
            "timestamp": datetime.now(),
            "read": False
        }
        communications.insert_one(communication)
        
        # Send email notification
        try:
            send_email([recipient["email"]], email_subject, email_body)
        except Exception as e:
            print(f"Error sending email to {recipient['email']}: {str(e)}")

def generate_anomaly_alerts(df, anomaly_scores):
    """
    Generate alerts for detected anomalies and send reports.
    
    Args:
        df (pd.DataFrame): DataFrame containing energy data
        anomaly_scores (np.array): Array of anomaly scores
    """
    # Get alerts collection
    alerts_collection = get_alerts_collection()
    
    # Clear old alerts before generating new ones
    alerts_collection.delete_many({
        "type": "anomaly_isolation_forest",
        "timestamp": {"$lt": df['timestamp'].min()}
    })
    
    # Process each anomaly
    for idx, (timestamp, energy_value, score) in enumerate(zip(df['timestamp'], df['energy_wh'], anomaly_scores)):
        # Only create alerts for anomalies (score <= low_threshold)
        if score <= -0.20:  # Low threshold from anomalies page
            severity = determine_severity(score)
            message = generate_alert_message(energy_value, score)
            
            # Check if alert already exists for this timestamp
            existing_alert = alerts_collection.find_one({
                "timestamp": timestamp,
                "type": "anomaly_isolation_forest"
            })
            
            if not existing_alert:
                create_alert(timestamp, energy_value, score, severity, message)
    
    # Generate and send anomaly report
    report = generate_anomaly_report(df, anomaly_scores)
    
    # Get all admin and manager users
    users = get_user_collection()
    recipients = list(users.find({"role": {"$in": ["admin", "manager"]}}))
    
    # Send report to all recipients
    send_anomaly_report(report, recipients)

def run_alert_checks():
    """Run all alert checks"""
    # Clear old alerts before running checks
    alerts_collection = get_alerts_collection()
    alerts_collection.delete_many({
        "type": "anomaly_isolation_forest",
        "timestamp": {"$lt": datetime.now() - timedelta(days=30)}  # Keep only last 30 days
    })
    
    check_consecutive_anomalies(threshold=2)
    check_energy_spike(threshold_percent=50)
    check_unusual_patterns(window_hours=24)