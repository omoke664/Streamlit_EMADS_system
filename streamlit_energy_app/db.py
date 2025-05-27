from dotenv import load_dotenv
from pymongo import MongoClient 
import streamlit as st
import pandas as pd 
import os

load_dotenv()

@st.cache_resource
def get_mongo_client():
    return MongoClient(os.getenv('MONGO_URI'))


def get_db():
    return get_mongo_client()[os.getenv("MONGO_DB")]

def get_user_collection():
    return get_db()[os.getenv("MONGO_USERS_COLLECTION", "users")]

def get_alerts_collection():
    return get_db()[os.getenv("MONGO_ALERTS_COLLECTION", "alerts")]

def get_messages_collection():
    return get_db()[os.getenv("MONGO_MESSAGES_COLLECTION", "messages")]

def get_communications_collection():
    return get_db()[os.getenv("MONGO_COMMUNICATIONS_COLLECTION", "communications")]

def get_energy_collection():
    """Get energy data collection"""
    return get_db()[os.getenv("MONGO_ENERGY_COLLECTION", "energy_data")]

@st.cache_data(ttl = 300)
def load_energy_data():
    """Load energy data from MongoDB and return as a DataFrame."""
    col = get_db()[os.getenv("MONGO_ENERGY_COLLECTION")]
    cursor = col.find({}, {"_id":0, "timestamp": 1, "energy_wh": 1})
    df = pd.DataFrame(list(cursor))
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop = True)
    return df 
