streamlit_energy_app/
├── db.py                   # MongoDB connection & data loaders
├── auth.py                 # Password hashing & verification
├── email_utils.py          # SMTP helper
├── models/
│   ├── lstm_model.pkl      # Pretrained LSTM forecasting model
│   └── isolation_forest_model.joblib
├── pages/
│   ├── dashboard.py
│   ├── anomalies.py
│   ├── forecasting.py
│   ├── analytics.py
│   ├── reports.py
│   ├── recommendations.py
│   ├── preferences.py
│   ├── about.py
│   ├── user_management.py
│   └── communications.py
├── alerts.py               # Real-time anomaly monitor & notifier
└── main.py                 # Orchestrates routing & session_state
