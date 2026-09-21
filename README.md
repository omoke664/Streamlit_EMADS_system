# Energy Monitoring and Anomaly Detection System (EMADS)

The **Energy Monitoring and Anomaly Detection System (EMADS)** is a Streamlit-based web application designed to monitor energy consumption, detect abnormal usage patterns, and forecast future energy demand in university hostels.

The system integrates hardware-based energy sensor data with machine learning models to provide real-time monitoring, anomaly detection, energy forecasting, alerts, analytics, and automated reporting.

## Key Features

### Interactive Dashboard

- **`dashboard.py`**
- Provides real-time visualization of energy consumption metrics and trends.
- Displays energy monitoring information through an interactive Streamlit interface.

### Anomaly Detection

- **`anomalies.py`**
- **`anomaly_detection/`**
- Uses the **Isolation Forest** machine learning algorithm to identify unusual energy consumption patterns.
- Detects abnormal energy spikes and drops that may indicate:
  - Hardware faults
  - Unusual consumption
  - Energy wastage
  - Other irregular usage patterns

### Energy Forecasting

- **`forecasting.py`**
- **`lstm_network.py`**
- **`prophet_forecast.py`**
- Forecasts future energy consumption using:
  - Long Short-Term Memory (LSTM) neural networks
  - Facebook Prophet

### Alerts and Notifications

- **`alerts.py`**
- **`email_utils.py`**
- Provides automated notifications when:
  - Energy anomalies are detected
  - Consumption exceeds configured thresholds
  - Other critical monitoring conditions occur

### Analytics and Reporting

- **`analytics.py`**
- **`reports.py`**
- **`weekly_report.py`**
- Provides energy consumption analytics and generates automated reports for monitoring and decision-making.

### Secure User Access

- **`auth.py`**
- **`user_management.py`**
- **`login.py`**
- **`registration.py`**
- Provides user authentication and account management features, including:
  - User registration
  - Login authentication
  - Password management
  - Access control

---

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | Streamlit |
| Programming Language | Python |
| Anomaly Detection | Isolation Forest |
| Forecasting | LSTM, Prophet |
| Hardware Integration | Arduino-based sensors |
| Data Processing | Python |
| Reporting | Automated Python reports |

---

## System Architecture

```text
Arduino Energy Sensors
          |
          v
  Energy Data Collection
          |
          v
    Data Processing
          |
     +----+----+
     |         |
     v         v
  Anomaly   Forecasting
 Detection   (LSTM/Prophet)
     |         |
     +----+----+
          |
          v
   Streamlit Dashboard
          |
     +----+----+
     |         |
     v         v
  Alerts    Analytics &
Notifications  Reporting
Installation
1. Clone the Repository
git clone https://github.com/omoke664/Streamlit_EMADS_system.git

Navigate to the project directory:

cd Streamlit_EMADS_system/streamlit_energy_app
2. Install Dependencies

Install the required Python packages:

pip install -r requirements.txt

It is recommended to use a Python virtual environment to isolate the project's dependencies.

3. Configure Environment Variables

Create a .env file in the project directory and add the required configuration values.

These may include:

Database credentials
API keys
Email configuration
Other application-specific settings

Example:

DATABASE_HOST=your_database_host
DATABASE_USER=your_database_user
DATABASE_PASSWORD=your_database_password
DATABASE_NAME=your_database_name

EMAIL_HOST=your_email_host
EMAIL_PORT=your_email_port
EMAIL_USERNAME=your_email_username
EMAIL_PASSWORD=your_email_password

Important: Do not commit your .env file or other files containing passwords, API keys, or sensitive credentials to GitHub.

Usage
Run the Application

Start the Streamlit application using:

streamlit run main.py

Once the application starts, open the following address in your browser:

http://localhost:8501

The application will display the login page and dashboard.

Project Structure
Streamlit_EMADS_system/
│
├── streamlit_energy_app/
│   │
│   ├── main.py
│   ├── dashboard.py
│   ├── anomalies.py
│   ├── forecasting.py
│   ├── lstm_network.py
│   ├── prophet_forecast.py
│   │
│   ├── anomaly_detection/
│   │   └── ...
│   │
│   ├── new_models/
│   │   └── ...
│   │
│   ├── utils/
│   │   └── ...
│   │
│   ├── assets/
│   │   └── ...
│   │
│   ├── auth.py
│   ├── user_management.py
│   ├── login.py
│   ├── registration.py
│   │
│   ├── alerts.py
│   ├── email_utils.py
│   ├── analytics.py
│   ├── reports.py
│   ├── weekly_report.py
│   ├── db.py
│   │
│   ├── requirements.txt
│   └── run_weekly_report.bat
│
└── README.md
Project Structure Highlights
File / Directory	Description
main.py	Main entry point for the Streamlit application
dashboard.py	Dashboard interface and energy monitoring visualizations
anomalies.py	Anomaly detection functionality
anomaly_detection/	Components and models used for anomaly detection
new_models/	Trained or experimental machine learning models
forecasting.py	Energy forecasting functionality
lstm_network.py	LSTM-based forecasting implementation
prophet_forecast.py	Prophet-based forecasting implementation
utils/	Helper functions for data processing and formatting
assets/	Images and static frontend assets
auth.py	Authentication functionality
user_management.py	User account and access management
login.py	Login functionality
registration.py	User registration functionality
alerts.py	Alert generation and notification logic
email_utils.py	Email-related utilities
analytics.py	Energy consumption analytics
reports.py	Report generation functionality
weekly_report.py	Automated weekly reporting
db.py	Database-related functionality
requirements.txt	Python project dependencies
run_weekly_report.bat	Windows batch script for automated weekly reports
Machine Learning

EMADS uses machine learning for two primary tasks: anomaly detection and energy forecasting.

Anomaly Detection

The system uses the Isolation Forest algorithm to identify energy consumption observations that differ significantly from normal usage patterns.

Energy Consumption Data
          |
          v
    Data Processing
          |
          v
   Isolation Forest
          |
      +---+---+
      |       |
      v       v
   Normal   Anomaly
      |       |
      +---+---+
          |
          v
    Alert / Analysis
Energy Forecasting

The system uses time-series forecasting models to estimate future energy demand.

The forecasting components include:

LSTM: Neural-network-based time-series forecasting.
Prophet: Time-series forecasting for energy consumption trends and patterns.
Hardware Integration

EMADS integrates energy measurements collected through Arduino-based sensors.

The general data flow is:

Energy Sensor
      |
      v
   Arduino
      |
      v
Data Transmission
      |
      v
EMADS Data Processing
      |
      v
Database / Application
      |
 +----+----+
 |         |
 v         v
Anomaly  Forecasting
Detection
 |         |
 +----+----+
      |
      v
  Dashboard
Automated Weekly Reports

EMADS includes a Windows batch script:

run_weekly_report.bat

This script can be used to automate the generation of weekly energy consumption reports.

For Windows deployments, the script can be scheduled using Windows Task Scheduler.

Security Considerations

For secure deployment:

Store database credentials securely.
Do not hard-code API keys in source files.
Store email credentials in environment variables.
Do not commit .env files to GitHub.
Do not store user passwords in plain text.
Use appropriate authentication and access-control mechanisms in production.

Add the following to .gitignore:

.env
*.env
__pycache__/
*.pyc
Future Development

Potential areas for future development include:

Real-time sensor data streaming
Additional anomaly detection algorithms
Advanced energy forecasting models
Expanded energy consumption analytics
Improved dashboard visualizations
Mobile-friendly monitoring
Automated model retraining
Additional notification channels
Integration with additional IoT energy-monitoring devices
Author

Wesley Omoke

GitHub: https://github.com/omoke664

License

This project is currently under development. Add the appropriate license information here.


This version will render properly on **GitHub**, including the tables, headings, code blocks, directory t
