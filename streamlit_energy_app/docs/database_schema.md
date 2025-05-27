# Database Schema Documentation

## Collections Overview

### 1. Users Collection
```json
{
    "_id": "ObjectId",
    "username": "String",
    "email": "String",
    "first_name": "String",
    "last_name": "String",
    "password": "String (hashed)",
    "role": "String (resident/admin/manager)",
    "status": "String (active/pending)",
    "disabled": "Boolean",
    "requested_role": "String (optional)",
    "created_at": "DateTime",
    "preferences": {
        "notifications": {
            "alerts": "Boolean",
            "reports": "Boolean"
        }
    }
}
```

### 2. Energy Data Collection
```json
{
    "_id": "ObjectId",
    "timestamp": "DateTime",
    "energy_wh": "Number",
    "sensor_id": "String",
    "anomaly_score": "Number (optional)",
    "is_anomaly": "Boolean (optional)"
}
```

### 3. Alerts Collection
```json
{
    "_id": "ObjectId",
    "timestamp": "DateTime",
    "energy_wh": "Number",
    "anomaly_score": "Number",
    "severity": "String (high/medium/low)",
    "message": "String",
    "type": "String (anomaly_isolation_forest/energy_spike/consecutive_anomalies)",
    "resolved": "Boolean",
    "created_at": "DateTime",
    "sensor_id": "String",
    "pct_change": "Number (optional)"
}
```

### 4. Communications Collection
```json
{
    "_id": "ObjectId",
    "user_id": "ObjectId (ref: users._id)",
    "type": "String (alert/message)",
    "title": "String",
    "message": "String",
    "timestamp": "DateTime",
    "read": "Boolean",
    "alert_id": "ObjectId (ref: alerts._id, optional)"
}
```

## Relationships

1. **Users → Communications**
   - One-to-Many relationship
   - A user can have multiple communications
   - Connected via `user_id` in communications collection

2. **Alerts → Communications**
   - One-to-Many relationship
   - An alert can generate multiple communications
   - Connected via `alert_id` in communications collection

3. **Energy Data → Alerts**
   - One-to-Many relationship
   - Energy readings can generate multiple alerts
   - Connected via timestamp and sensor_id

## Indexes

1. Users Collection:
   - `username` (unique)
   - `email` (unique)
   - `role`
   - `status`

2. Energy Data Collection:
   - `timestamp`
   - `sensor_id`
   - Compound index on `{timestamp: 1, sensor_id: 1}`

3. Alerts Collection:
   - `timestamp`
   - `type`
   - `severity`
   - `sensor_id`
   - Compound index on `{timestamp: 1, type: 1}`

4. Communications Collection:
   - `user_id`
   - `timestamp`
   - `type`
   - `read`
   - Compound index on `{user_id: 1, timestamp: -1}`

## Data Flow

1. Energy readings are stored in the Energy Data collection
2. Anomaly detection processes these readings and creates alerts
3. Alerts trigger communications to relevant users
4. Users can view and manage their communications
5. Users can view and manage alerts based on their role

## Security Considerations

1. Passwords are stored as hashed values
2. Role-based access control implemented
3. User status tracking for pending approvals
4. Disabled user accounts are prevented from accessing the system 