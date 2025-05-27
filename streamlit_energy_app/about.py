import streamlit as st 



def about_page():
    st.title("About EMADS")
    
    st.markdown("""
        EMADS (Energy Monitoring & Anomaly Detection System) is a comprehensive platform
        for monitoring energy consumption and detecting anomalies in real-time.
    """)

    st.markdown(
        """
        **Energy Monitoring & Anomaly Detection System (EMADS)**  
        A Streamlit-powered web app that lets you track and analyze energy usage in your university hostel in real-time, detect anomalies, forecast future consumption, and generate actionable insights.

        ---
        #### 📊 Dashboard  
        - **Key Metrics**: Total, average, and peak kWh consumed, anomaly rate  
        - **Time Series Chart**: Interactive line plot of consumption over time  
        - **Daily Summary**: Per-day usage table and 7-day moving average  
        - **Weekday Breakdown**: Bar chart comparing each day of the week

        #### 🚨 Anomalies  
        - **Real-time Detection**: IsolationForest flags unusual consumption points  
        - **Visualization**: Consumption plot with anomaly markers  
        - **Details Table**: Timestamp, score, and flag for each anomaly

        #### 📈 Forecasting  
        - **ARIMA/Prophet Models**: Short-term load forecasting  
        - **Parameter Controls**: Choose model and horizon  
        - **Accuracy Metrics**: MAE & RMSE on test data

        #### 📊 Analytics  
        - **Aggregated Views**: Daily/weekly/monthly energy summaries  
        - **Distribution Plots**: Histograms & boxplots of consumption levels  
        - **Comparison Charts**: e.g. all Mondays vs. all Saturdays

        #### 📄 Reports  
        - **Exportable Reports**: CSV/PDF exports of energy data and anomalies  
        - **Scheduled Reports**: Weekly summary emailed to managers/admins

        #### 💡 Recommendations  
        - **Automated Tips**: Energy-saving advice based on usage patterns  
        - **Threshold Alerts**: Guidance when consumption crosses set limits

        #### ⚙️ Preferences  
        - **User Settings**: Default time-range, asset selection, alert thresholds  
        - **Profile**: View and update your user details

        #### 🛠️ User Management *(Admin only)*  
        - **CRUD Users**: Add, delete, enable/disable accounts  
        - **Role Assignment**: Grant admin, manager, or resident privileges  

        ---  
        **Contact & Support**  
        If you run into any issues or have ideas, reach out to your system administrator or open a GitHub issue in the project repo.
        """
    )