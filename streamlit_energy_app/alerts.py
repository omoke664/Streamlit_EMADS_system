import pandas as pd
from datetime import datetime 
from db import get_db, get_user_collection, get_alerts_collection
from anomaly_detection.anomaly_detector import AnomalyDetector 
from email_utils import send_email 
from dotenv import load_dotenv

load_dotenv()
import os

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
    

    # 2) Are they all flagged anomalies?
    df = pd.DataFrame(docs)
    if not df["is_anomaly"].all():
        return # no run of anomalies 
    
    sensor = df.loc[0, "sensor_id"]
    last_ts = df.loc[0, "timestamp"]


    # 3) Has an alert already been created for this run?
    exists = alerts.find_one({
        "sensor_id": sensor,
        "type": "consecutive_anomalies",
        "detected_at": {"$gte": last_ts}
    })

    if exists:
        return # already alerted for this event
    

    # 4) Create alert document
    alert_doc = {
        "sensor_id": sensor,
        "detected at": last_ts,
        "type": "consecutive_anomalies",
        "count": threshold,
        "notified": False,
        "message": f"{threshold} successive anoamalies on {sensor} at {last_ts}"
    }

    alerts.insert_one(alert_doc)

    #5) Notify via email
    # find all admins / managers emails
    recipients = [u["email"] for u in users.find(
        {"role": {"$in": ['admin", "manager"']}},
        {"email":1, "_id":0}
    )]

    subject = f"EMADS Alert: {threshold} consecutive anomalies"
    body = alert_doc["message"]
    send_email(recipients, subject, body)


    # 6) Mark notified
    alerts.update_one(
        {"_id": alert_doc["_id"]},
        {"$set": {"notified": True}}
        
    )