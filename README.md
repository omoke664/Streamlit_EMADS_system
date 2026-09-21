# Energy Monitoring and Anomaly Detection System (EMADS)

A comprehensive Streamlit-based web application designed to monitor energy consumption, detect usage anomalies, and forecast future energy demands for university hostels. The system integrates hardware sensor data with advanced machine learning models to provide real-time insights and automated reporting.

## Key Features

* **Interactive Dashboard (`dashboard.py`):** Real-time visualization of energy consumption metrics and trends.
* **Anomaly Detection (`anomalies.py`, `anomaly_detection/`):** Automatically identifies unusual energy spikes or drops using machine learning (Isolation Forest), helping to pinpoint hardware faults or energy wastage.
* **Energy Forecasting (`forecasting.py`, `lstm_network.py`, `prophet_forecast.py`):** Predicts future energy usage patterns utilizing LSTM networks and Facebook Prophet models.
* **Alerts & Notifications (`alerts.py`, `email_utils.py`):** Automated alerting system to notify administrators of detected anomalies or critical thresholds.
* **Analytics & Reporting (`analytics.py`, `reports.py`, `weekly_report.py`):** Generates detailed consumption analytics and automated weekly reports.
* **Secure Access (`auth.py`, `user_management.py`, `login.py`, `registration.py`):** Built-in user authentication, registration, and password management to secure the dashboard.

## Technology Stack

* **Frontend:** Streamlit
* **Machine Learning:** Isolation Forest (Anomaly Detection), LSTM, Prophet (Forecasting)
* **Hardware Integration:** Arduino sensors (Data collection)
* **Language:** Python

## Installation

1. Clone the repository:
   ```bash
   git clone [https://github.com/omoke664/Streamlit_EMADS_system.git](https://github.com/omoke664/Streamlit_EMADS_system.git)
   cd Streamlit_EMADS_system/streamlit_energy_app


2. Install the required dependencies:

Bash
pip install -r requirements.txt

3. Configure environment variables:

Create a .env file in the root directory and add any necessary database credentials, API keys, or email configurations required by db.py and email_utils.py.

Usage
Run the Streamlit application locally:

Markdown
# Energy Monitoring and Anomaly Detection System (EMADS)

A comprehensive Streamlit-based web application designed to monitor energy consumption, detect usage anomalies, and forecast future energy demands for university hostels. The system integrates hardware sensor data with advanced machine learning models to provide real-time insights and automated reporting.

## Key Features

* **Interactive Dashboard (`dashboard.py`):** Real-time visualization of energy consumption metrics and trends.
* **Anomaly Detection (`anomalies.py`, `anomaly_detection/`):** Automatically identifies unusual energy spikes or drops using machine learning (Isolation Forest), helping to pinpoint hardware faults or energy wastage.
* **Energy Forecasting (`forecasting.py`, `lstm_network.py`, `prophet_forecast.py`):** Predicts future energy usage patterns utilizing LSTM networks and Facebook Prophet models.
* **Alerts & Notifications (`alerts.py`, `email_utils.py`):** Automated alerting system to notify administrators of detected anomalies or critical thresholds.
* **Analytics & Reporting (`analytics.py`, `reports.py`, `weekly_report.py`):** Generates detailed consumption analytics and automated weekly reports.
* **Secure Access (`auth.py`, `user_management.py`, `login.py`, `registration.py`):** Built-in user authentication, registration, and password management to secure the dashboard.

## Technology Stack

* **Frontend:** Streamlit
* **Machine Learning:** Isolation Forest (Anomaly Detection), LSTM, Prophet (Forecasting)
* **Hardware Integration:** Arduino sensors (Data collection)
* **Language:** Python

## Installation

1. Clone the repository:
   ```bash
   git clone [https://github.com/omoke664/Streamlit_EMADS_system.git](https://github.com/omoke664/Streamlit_EMADS_system.git)
   cd Streamlit_EMADS_system/streamlit_energy_app
Install the required dependencies:

Bash
pip install -r requirements.txt
Configure environment variables:

Create a .env file in the root directory and add any necessary database credentials, API keys, or email configurations required by db.py and email_utils.py.

Usage
Run the Streamlit application locally:

Bash
streamlit run main.py
Navigate to http://localhost:8501 in your web browser to access the login page and dashboard.

Project Structure Highlights
anomaly_detection/ & new_models/: Contains the trained machine learning models for processing sensor data.

utils/: Helper functions for data processing and formatting.

assets/: Image assets and static files for the frontend UI.

run_weekly_report.bat: Batch script for automating the generation of weekly energy consumption reports.
