1. Project Structure & Dependencies
Directory Layout

graphql
Copy
Edit
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
Key Python Packages

streamlit

pymongo

passlib[bcrypt]

joblib

torch or tensorflow + keras (depending on LSTM implementation)

pandas, numpy

plotly

scikit-learn

2. Data Layer
MongoDB (via db.py)

Users collection: stores username, email, hashed_password, role, disabled, requested_role, approved, timestamps.

Energy collection: raw readings (timestamp, energy_wh).

Alerts & Messages collections.

Loaders

load_energy_data() → DataFrame, with timestamp → datetime64, energy_wh numeric.

get_user_collection() → CRUD for user accounts.

3. Authentication & Authorization
Registration (main.py or auth.py)

Collect username, email, first_name, last_name, password, role_request.

Hash password via passlib.

Insert new user with role='resident'; if role_request∈{manager,admin}, mark approved=False.

Login

Verify password; if (role_request∈{manager,admin} & ¬approved) ⇒ block; else set

python
Copy
Edit
st.session_state.user = {"username":…, "role":…}
Persist in-memory session.

Role-Based Routing

Sidebar menu built dynamically by session_state.user["role"].

Protected pages call require_login().

4. Dashboard Page
KPI Cards (via dashboard.py):

Total Energy (kWh) ← df.energy_wh.sum() / 1000

Average, Peak, Anomaly Rate (pull from latest anomaly stats).

Time-Series Plot

Line chart of energy over time.

Summaries

Daily totals, 7-day MA, weekday averages.

5. Anomaly Detection Page
Load Pretrained Isolation Forest (joblib.load('models/isolation_forest_model.joblib')).

Score & Flag new data:

python
Copy
Edit
preds = model.predict(df[['energy_wh']])
scores = model.decision_function(df[['energy_wh']])
df['is_anomaly'] = (preds == -1)
df['anomaly_score'] = scores
Metrics: total records, count and percent anomalies, plus longest run of consecutive anomalies.

Chart: overlay anomaly points in contrasting color.

Table: all rows with flags, timestamps, scores.

Model Description: parameter summary, algorithm overview.

6. Energy Forecasting Page (LSTM)
Load Pretrained LSTM

python
Copy
Edit
import joblib
model, scaler = joblib.load('models/lstm_model.pkl')
Prepare Data

Aggregate to daily totals in energy_wh.

Scale using loaded scaler.

Make Predictions

Create sliding windows for last window_size days → feed into model.predict().

Inverse-scale outputs to get yhat_wh.

Visualize

Plot historical vs. forecast (energy_wh) with Plotly.

Display MAE & RMSE computed over test split.

7. Analytics & Reports
Analytics Page:

Aggregations (weekly, monthly), distribution plots (histogram, boxplot), comparisons (e.g. weekdays vs. weekends).

Reports Page:

Export CSV/PDF of energy, anomalies, forecast.

Use st.download_button.

8. Recommendations
Rule-Based Tips: e.g. “Your peak usage occurs at X→ consider…”.

Severity levels based on thresholds.

9. Alerts & Notifications
Real-Time Monitoring (alerts.py)

Poll latest readings (e.g. every minute via cache of last timestamp).

If N consecutive anomalies (e.g. 2), generate alert.

In-App Alert Panel:

List unacknowledged alerts, mark as read.

Email Notifications (email_utils.py)

On alert generation, send_email(to=manager_emails, subject, body).

Place smtp.starttls() immediately after ehlo(), before login().

10. User Management & Communications
User Management (user_management.py)

List all users, filter by disabled flag.

Pending role requests: Approve/Reject.

Modify existing by username (not ObjectId).

In-App Messaging (communications.py)

Form to select recipient (first_name + last_name), compose message.

Save to Messages collection with timestamp.

Show incoming messages, mark read/unread.

On send, trigger send_email(recipient_email, …).

11. Preferences & About
Preferences: default date range, anomaly threshold, notification settings.

About: overview of EMADS, description of each section.

12. Deployment
Environment

Store MONGO_URI, SMTP creds in .env.

pip install -r requirements.txt.

Hosting

VM or Streamlit Cloud: open port 8501.

Ensure MongoDB is reachable (network allowlist).

Mobile Compatibility

Streamlit’s responsive layout; test on handset.

