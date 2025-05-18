import streamlit as st 
from require_login import require_login 
from db import load_energy_data 



def recommendations_page():
    require_login()
    st.title("💡 Recommendations")

    # Load daily summary
    df = load_energy_data()
    if df.empty:
        st.warning("⚠️ No energy data available.")
        return

    # Daily totals
    daily = df.set_index("timestamp").resample("D")["energy_kwh"].sum()

    # Compute week-over-week change
    week_ago = daily.shift(7)
    pct_change = ((daily - week_ago) / week_ago) * 100

    st.subheader("Weekly Change in Daily Consumption")
    st.line_chart(pct_change, use_container_width=True)

    # Simple tip rules
    st.subheader("Auto‐Generated Tips")
    tips = []
    # 1) High peak day
    peak_day = daily.idxmax().date()
    tips.append({
        "severity": "High",
        "message": f"⚠️ {peak_day} had the highest consumption this period ({daily.max():.2f} kWh). Investigate unusual loads."
    })
    # 2) Increasing trend
    recent_change = pct_change.iloc[-1]
    if recent_change > 10:
        tips.append({
            "severity": "Medium",
            "message": f"🔺 Consumption up {recent_change:.1f}% vs. last week—encourage energy-saving behavior."
        })
    elif recent_change < -10:
        tips.append({
            "severity": "Low",
            "message": f"🔻 Consumption down {abs(recent_change):.1f}% vs. last week—good job on savings!"
        })
    else:
        tips.append({
            "severity": "Info",
            "message": "ℹ️ Consumption is stable week-over-week."
        })

    # 3) Night‐time usage
    # average usage 10pm–6am vs. daytime
    df["hour"] = df["timestamp"].dt.hour
    night = df[(df["hour"] >= 22) | (df["hour"] < 6)]["energy_kwh"].mean()
    day   = df[(df["hour"] >= 6) & (df["hour"] < 22)]["energy_kwh"].mean()
    if night > day * 0.5:
        tips.append({
            "severity": "Medium",
            "message": f"🌙 Night‐time usage ({night:.2f} kWh avg) is more than 50% of daytime—consider scheduling lights‐off automation."
        })

    # Display tips
    for tip in tips:
        if tip["severity"] == "High":
            st.error(tip["message"])
        elif tip["severity"] == "Medium":
            st.warning(tip["message"])
        else:
            st.info(tip["message"])
