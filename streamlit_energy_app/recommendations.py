import streamlit as st 
from require_login import require_login 
from db import load_energy_data 
import plotly.graph_objects as go



def recommendations_page():
    require_login()
    st.title("Recommendations")
    st.markdown("""
        This page provides personalized energy-saving recommendations based on your consumption patterns.
        Recommendations are generated using machine learning and expert knowledge.
    """)

    # Load energy data
    df = load_energy_data()
    if df.empty:
        st.warning("No energy data available.")
        return

    # Calculate daily consumption
    daily_consumption = df.set_index('timestamp').resample('D')['energy_wh'].sum().reset_index()
    
    # Generate recommendations
    recommendations = []
    
    # 1) Peak consumption day
    peak_day = daily_consumption.loc[daily_consumption['energy_wh'].idxmax(), 'timestamp'].strftime('%Y-%m-%d')
    daily = daily_consumption['energy_wh']
    recommendations.append({
        "type": "Peak Consumption",
        "message": f"{peak_day} had the highest consumption this period ({daily.max():.2f} kWh). Investigate unusual loads."
    })
    
    # 2) Week-over-week change
    recent_avg = daily_consumption['energy_wh'].tail(7).mean()
    prev_avg = daily_consumption['energy_wh'].tail(14).head(7).mean()
    recent_change = ((recent_avg - prev_avg) / prev_avg) * 100
    
    if abs(recent_change) > 5:
        if recent_change > 0:
            recommendations.append({
                "type": "Consumption Trend",
                "message": f"Consumption up {recent_change:.1f}% vs. last week—encourage energy-saving behavior."
            })
        else:
            recommendations.append({
                "type": "Consumption Trend",
                "message": f"Consumption down {abs(recent_change):.1f}% vs. last week—good job on savings!"
            })
    else:
        recommendations.append({
            "type": "Consumption Trend",
            "message": "Consumption is stable week-over-week."
        })
    
    # 3) Night-time usage
    df['hour'] = df['timestamp'].dt.hour
    night_usage = df[df['hour'].between(22, 5)]['energy_wh'].mean()
    day_usage = df[df['hour'].between(6, 21)]['energy_wh'].mean()
    
    if night_usage > day_usage * 0.5:
        recommendations.append({
            "type": "Night Usage",
            "message": f"Night-time usage ({night_usage:.2f} kWh avg) is more than 50% of daytime—consider scheduling lights-off automation."
        })
    
    # Display recommendations
    st.subheader("Auto-Generated Tips")
    for rec in recommendations:
        st.info(f"{rec['type']}: {rec['message']}")
    
    # Display consumption patterns
    st.subheader("Consumption Patterns")
    
    # Daily consumption plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily_consumption['timestamp'],
        y=daily_consumption['energy_wh'],
        mode='lines+markers',
        name='Daily Consumption'
    ))
    
    fig.update_layout(
        title='Daily Energy Consumption',
        xaxis_title='Date',
        yaxis_title='Energy (Wh)',
        height=400,
        showlegend=True,
        template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Hourly consumption heatmap
    hourly_consumption = df.pivot_table(
        values='energy_wh',
        index=df['timestamp'].dt.hour,
        columns=df['timestamp'].dt.date,
        aggfunc='mean'
    )
    
    fig = go.Figure(data=go.Heatmap(
        z=hourly_consumption.values,
        x=hourly_consumption.columns,
        y=hourly_consumption.index,
        colorscale='Viridis'
    ))
    
    fig.update_layout(
        title='Hourly Energy Consumption Heatmap',
        xaxis_title='Date',
        yaxis_title='Hour of Day',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
