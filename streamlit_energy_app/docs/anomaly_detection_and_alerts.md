# Anomaly Detection and Alert Generation System

## Overview
The Energy Monitoring and Anomaly Detection System (EMADS) implements a sophisticated anomaly detection and alert generation system that monitors energy consumption patterns and identifies unusual behaviors. The system uses multiple detection methods and provides real-time alerts to administrators and managers.

## Anomaly Detection Module

### Core Components

#### 1. Isolation Forest Model
- **Implementation**: Uses scikit-learn's Isolation Forest algorithm
- **Purpose**: Detects anomalies in energy consumption patterns
- **Features**:
  - Cached model loading for performance optimization
  - Severity levels: high, medium, and low
  - Anomaly scoring with percentile-based thresholds
  - Additional statistical validation using z-scores

#### 2. Statistical Anomaly Detection
- **Method**: Rolling mean and standard deviation analysis
- **Parameters**:
  - Window size: 24 hours (configurable)
  - Standard deviation threshold: 4 (configurable)
- **Features**:
  - Z-score calculation
  - Normalized anomaly scoring
  - Consecutive anomaly detection

#### 3. Energy Spike Detection
- **Method**: Percentage change analysis
- **Features**:
  - Configurable spike threshold
  - Spike score calculation
  - Real-time monitoring

### Implementation Details

#### Data Processing
```python
@st.cache_data(ttl=60)  # Cache for 1 minute
def load_energy_data(start_time, end_time):
    """Load energy data from MongoDB with caching"""
    energy_collection = get_energy_collection()
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
```

#### Anomaly Detection Pipeline
1. Data loading and preprocessing
2. Statistical anomaly detection
3. Consecutive anomaly detection
4. Energy spike detection
5. Isolation Forest model prediction
6. Severity classification

## Alert Generation Module

### Alert Types

#### 1. Consecutive Anomalies
- **Trigger**: Multiple anomalies in sequence
- **Threshold**: Configurable (default: 2 consecutive anomalies)
- **Severity**: High if ≥ 3 consecutive, Medium otherwise

#### 2. Energy Spikes
- **Trigger**: Sudden increase in energy consumption
- **Threshold**: Configurable percentage change (default: 50%)
- **Severity**: High if > 100% change, Medium otherwise

#### 3. Unusual Patterns
- **Trigger**: Deviation from historical patterns
- **Method**: Hourly statistical analysis
- **Threshold**: 2 standard deviations from mean
- **Severity**: Medium

### Alert Management

#### Notification System
- **Channels**:
  - Email notifications
  - In-app alerts
  - System messages
- **Recipients**: Configurable based on user roles and preferences
- **Frequency**: Real-time for critical alerts

#### Alert Storage
- MongoDB collection for persistent storage
- Fields:
  - Timestamp
  - Alert type
  - Severity
  - Message
  - Energy consumption value
  - Anomaly score
  - Resolution status

### Implementation Details

#### Alert Generation
```python
def create_alert(timestamp, energy_value, anomaly_score, severity, message):
    """Create and store an alert"""
    alert = {
        'timestamp': timestamp,
        'type': 'isolation_forest',
        'severity': severity,
        'message': message,
        'energy_consumption': float(energy_value),
        'anomaly_score': float(anomaly_score),
        'resolved': False
    }
```

#### Notification Management
```python
def get_notification_recipients(alert_type):
    """Get recipients based on their notification preferences"""
    users = get_user_collection()
    recipients = []
    
    for user in users.find({"role": {"$in": ["admin", "manager"]}}):
        prefs = user.get("preferences", {})
        notifications = prefs.get("notifications", {})
        
        if notifications.get("alerts", True):
            recipients.append(user["email"])
```

## Performance Optimizations

1. **Caching**:
   - Model caching (1-hour TTL)
   - Data caching (1-minute TTL)
   - Function result caching (5-minute TTL)

2. **Batch Processing**:
   - Batch alert creation
   - Batch notification sending
   - Efficient database queries

3. **Resource Management**:
   - Optimized database queries
   - Proper indexing
   - Memory-efficient data structures

## Security Considerations

1. **Access Control**:
   - Role-based access to alerts
   - Secure notification delivery
   - Protected API endpoints

2. **Data Protection**:
   - Secure storage of sensitive information
   - Encrypted communication
   - Audit logging

## Future Enhancements

1. **Machine Learning Improvements**:
   - Integration of additional ML models
   - Automated model retraining
   - Feature engineering enhancements

2. **Alert System Enhancements**:
   - Custom alert rules
   - Advanced notification routing
   - Alert correlation

3. **Performance Optimizations**:
   - Distributed processing
   - Real-time streaming
   - Enhanced caching strategies 