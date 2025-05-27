# Chapter 4: System Analysis and Design

## 4.1 System Overview

The Energy Monitoring and Anomaly Detection System (EMADS) is designed to enhance energy efficiency, safety, and sustainability in university residential halls. The system integrates three main components:
- **IoT Sensors** for real-time data collection
- **Machine Learning (ML) Module** for anomaly detection and energy forecasting
- **Human-Computer Interaction (HCI) Module** for visualization and user engagement

The ML component is central, providing actionable insights by analyzing time-series energy data, detecting anomalies, and forecasting future consumption. The system is modular, scalable, and designed for real-time operation.

---

## 4.2 System Architecture

The architecture consists of:
- **IoT Layer:** Sensors collect current and voltage data, calculate load, and transmit to the cloud database.
- **Data Storage:** Centralized MongoDB cloud database for real-time, scalable storage.
- **ML Module:** Processes data for anomaly detection (Isolation Forest) and forecasting (LSTM).
- **HCI Module:** Mobile/web interface for residents and facility managers to view insights, receive alerts, and interact with the system.

**Data Flow:**
1. Sensors → Cloud Database
2. ML Module fetches, preprocesses, and analyzes data
3. Results (anomalies, forecasts) → HCI Module for visualization and alerts

---

## 4.3 Design Methodology

### 4.3.1 Object-Oriented Design
- **Modularity:** Each function (data loading, preprocessing, detection, forecasting, output) is encapsulated in a class.
- **Reusability:** Common logic is abstracted for reuse.
- **Scalability:** New models or data sources can be integrated with minimal changes.
- **Collaboration:** Clear module boundaries support team development.

### 4.3.2 Comparison with Alternatives
- **Procedural:** Less maintainable for complex, evolving systems.
- **SOA:** More suited for distributed, loosely coupled systems; OOP is better for tightly integrated ML pipelines.

---

## 4.4 Machine Learning Component Design

### 4.4.1 Anomaly Detection Framework
- **Algorithm:** Isolation Forest (unsupervised, robust to noise, efficient for high-dimensional time series)
- **Workflow:**
  1. Preprocess data (clean, normalize, feature engineer)
  2. Train Isolation Forest on historical data
  3. Assign anomaly scores and labels (-1: anomaly, 1: normal)
  4. Trigger alerts for detected anomalies

### 4.4.2 Energy Forecasting Framework
- **Algorithm:** LSTM (Long Short-Term Memory) neural network
- **Workflow:**
  1. Preprocess and engineer features (hour, day, rolling averages, symbolic aSAX)
  2. Train LSTM on historical load data
  3. Predict next 24 hours of energy consumption
  4. Output forecasts for visualization and planning

---

## 4.5 Data Characteristics and Feature Engineering
- **Time-series data** (30-min intervals, kWh)
- **Features:** Hour of day, day of week, isWeekend, rolling averages, symbolic aSAX
- **Preprocessing:** Linear interpolation for missing values, IQR for outlier capping, Min-Max normalization

---

## 4.6 System Requirements

### 4.6.1 Functional Requirements
- Data ingestion (file/API)
- Automated preprocessing
- Anomaly detection (Isolation Forest)
- Energy forecasting (LSTM)
- Output generation (CSV/JSON)
- Integration with HCI and IoT modules

### 4.6.2 Non-Functional Requirements
- Real-time/near-real-time performance
- Scalability for multiple sensors
- Security (encryption, access control)
- Maintainability (modular, documented)
- Reliability and availability

---

## 4.7 Technology Stack
- **Python:** Main language
- **Libraries:** Pandas, NumPy, scikit-learn, TensorFlow, pyts, pymongo, Matplotlib, Seaborn
- **Tools:** VS Code, Google Colab, Git
- **Database:** MongoDB (cloud)
- **APIs:** RESTful endpoints for integration

---

## 4.8 Visual Models and UML Diagrams

### 4.8.1 ML Pipeline Diagram
![ML Pipeline Diagram](ml_pipeline_diagram.png)
*Figure: High-level data flow from IoT sensors through preprocessing, ML models, and output integration.*

### 4.8.2 Use Case Diagram
![Use Case Diagram](use_case_diagram.png)
*Figure: Main actors (ML engineer, facility manager, user) and their interactions with the system.*

### 4.8.3 Class Diagram
![Class Diagram](class_diagram.png)
*Figure: Object-oriented structure showing DataLoader, Preprocessor, AnomalyDetector, EnergyForecaster, OutputGenerator and their relationships.*

---

## 4.9 Feasibility Analysis and Risk Assessment

### 4.9.1 Technical Feasibility
- Uses robust, well-supported Python libraries
- Cloud-based training (Google Colab) for scalability
- Modular architecture for easy updates

### 4.9.2 Operational Feasibility
- Real-time processing for timely alerts
- Seamless integration with IoT and HCI modules
- Comprehensive documentation and training materials

### 4.9.3 Legal Feasibility
- Data privacy (anonymization, encryption, access control)
- Use of open-source tools to minimize legal risk

### 4.9.4 Risk Assessment and Mitigation
- **Data Quality:** Rigorous cleaning, interpolation, outlier detection
- **Model Performance:** Cross-validation, regular updates, monitoring
- **Integration:** Standardized formats, comprehensive testing
- **Security:** Encryption, MFA, RBAC, network whitelisting

---

## 4.10 Summary

The EMADS system is a robust, modular, and scalable solution for energy monitoring and anomaly detection in residential halls. Its design leverages state-of-the-art ML techniques, secure cloud infrastructure, and user-centered interfaces to deliver actionable insights and promote sustainable energy use.

---

## 4.11 UML Diagrams (Descriptions)

### ML Pipeline Diagram
- **Description:** Shows the flow from IoT sensors → Data Preprocessing (cleaning, normalization, aSAX) → ML Models (Isolation Forest, LSTM) → Output (alerts, forecasts) → HCI Module.

### Use Case Diagram
- **Description:** Actors: ML Engineer (model training, monitoring), Facility Manager (view alerts, reports), User/Resident (view usage, receive recommendations). Use cases: Data ingestion, anomaly detection, forecasting, output/report generation.

### Class Diagram
- **Description:**
  - `DataLoader`: Loads data from CSV, JSON, API
  - `TimeSeriesPreprocessor`: Cleans, normalizes, engineers features (aSAX)
  - `AnomalyDetector`: Trains and applies Isolation Forest
  - `EnergyForecaster`: Trains and applies LSTM
  - `OutputGenerator`: Exports results for HCI
  - Relationships: Preprocessor feeds both AnomalyDetector and EnergyForecaster; OutputGenerator integrates with HCI

---

*Note: Replace the UML diagram image links with actual diagrams generated using a UML tool or draw.io and export as PNGs to the docs directory for final submission.* 