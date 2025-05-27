# anomaly_detector.py

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
import joblib
import os

class AnomalyDetector:
    def __init__(self):
        self.models = {
            'isolation_forest': None,
            'statistical': None
        }
        self.scaler = StandardScaler()
        self.model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
        os.makedirs(self.model_dir, exist_ok=True)
        
    def train_isolation_forest(self, df, contamination=0.1):
        """Train Isolation Forest model"""
        X = df[["energy_wh"]].values
        X_scaled = self.scaler.fit_transform(X)
        
        model = IsolationForest(
            n_estimators=100,
            contamination=contamination,
            random_state=42
        )
        model.fit(X_scaled)
        
        self.models['isolation_forest'] = model
        self._save_model('isolation_forest', model)
        self._save_scaler()
        
    def detect_anomalies(self, df, method='isolation_forest', threshold=0.5):
        """Detect anomalies using specified method"""
        if method == 'isolation_forest':
            return self._detect_using_isolation_forest(df)
        elif method == 'statistical':
            return self._detect_using_statistical(df, threshold)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def _detect_using_isolation_forest(self, df):
        """Detect anomalies using Isolation Forest"""
        if self.models['isolation_forest'] is None:
            self._load_model('isolation_forest')
        
        X = df[["energy_wh"]].values
        X_scaled = self.scaler.transform(X)
        
        # Get anomaly scores and predictions
        scores = self.models['isolation_forest'].decision_function(X_scaled)
        predictions = self.models['isolation_forest'].predict(X_scaled)
        
        # Create results DataFrame
        results = pd.DataFrame({
            'timestamp': df['timestamp'],
            'energy_wh': df['energy_wh'],
            'anomaly_score': scores,
            'is_anomaly': predictions == -1,
            'detection_method': 'isolation_forest'
        })
        
        return results
    
    def _detect_using_statistical(self, df, threshold=0.5):
        """Detect anomalies using statistical methods"""
        # Calculate rolling statistics
        window = 24  # 24-hour window
        df['rolling_mean'] = df['energy_wh'].rolling(window=window, center=True).mean()
        df['rolling_std'] = df['energy_wh'].rolling(window=window, center=True).std()
        
        # Calculate z-scores
        df['z_score'] = (df['energy_wh'] - df['rolling_mean']) / df['rolling_std']
        
        # Identify anomalies
        results = pd.DataFrame({
            'timestamp': df['timestamp'],
            'energy_wh': df['energy_wh'],
            'anomaly_score': abs(df['z_score']),
            'is_anomaly': abs(df['z_score']) > threshold,
            'detection_method': 'statistical'
        })
        
        return results
    
    def _save_model(self, name, model):
        """Save model to disk"""
        path = os.path.join(self.model_dir, f'{name}_model.joblib')
        joblib.dump(model, path)
    
    def _load_model(self, name):
        """Load model from disk"""
        path = os.path.join(self.model_dir, f'{name}_model.joblib')
        if os.path.exists(path):
            self.models[name] = joblib.load(path)
        else:
            raise FileNotFoundError(f"Model file not found: {path}")
    
    def _save_scaler(self):
        """Save scaler to disk"""
        path = os.path.join(self.model_dir, 'scaler.joblib')
        joblib.dump(self.scaler, path)
    
    def _load_scaler(self):
        """Load scaler from disk"""
        path = os.path.join(self.model_dir, 'scaler.joblib')
        if os.path.exists(path):
            self.scaler = joblib.load(path)
        else:
            raise FileNotFoundError(f"Scaler file not found: {path}")
    
    def get_anomaly_types(self):
        """Get list of available anomaly detection methods"""
        return list(self.models.keys())
