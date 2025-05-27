import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from anomalies import (
    detect_statistical_anomalies,
    detect_consecutive_anomalies,
    detect_energy_spikes,
    detect_anomalies
)

class TestAnomalyDetection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test data and model"""
        # Generate synthetic test data
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='H')
        normal_consumption = np.random.normal(1000, 100, len(dates))
        
        # Add some anomalies
        cls.test_data = pd.DataFrame({
            'timestamp': dates,
            'energy_wh': normal_consumption
        })
        
        # Add spike anomalies
        spike_indices = [100, 200, 300]
        cls.test_data.loc[spike_indices, 'energy_wh'] *= 3
        
        # Add consecutive anomalies
        consecutive_indices = range(400, 410)
        cls.test_data.loc[consecutive_indices, 'energy_wh'] *= 2.5
        
        # Train Isolation Forest model
        cls.model = IsolationForest(
            contamination=0.02,
            random_state=42
        )
        cls.model.fit(cls.test_data[['energy_wh']].values)

    def test_statistical_anomaly_detection(self):
        """Test statistical anomaly detection"""
        # Run detection
        result_df = detect_statistical_anomalies(self.test_data.copy())
        
        # Verify results
        self.assertIn('statistical_anomaly', result_df.columns)
        self.assertIn('statistical_score', result_df.columns)
        self.assertTrue(result_df['statistical_anomaly'].dtype == bool)
        self.assertTrue(result_df['statistical_score'].dtype == float)
        
        # Check if known anomalies are detected
        self.assertTrue(result_df.loc[100, 'statistical_anomaly'])
        self.assertTrue(result_df.loc[200, 'statistical_anomaly'])
        self.assertTrue(result_df.loc[300, 'statistical_anomaly'])

    def test_consecutive_anomaly_detection(self):
        """Test consecutive anomaly detection"""
        # First run statistical detection
        df = detect_statistical_anomalies(self.test_data.copy())
        # Then run consecutive detection
        result_df = detect_consecutive_anomalies(df)
        
        # Verify results
        self.assertIn('consecutive_anomaly', result_df.columns)
        self.assertTrue(result_df['consecutive_anomaly'].dtype == bool)
        
        # Check if consecutive anomalies are detected
        self.assertTrue(result_df.loc[400:409, 'consecutive_anomaly'].all())

    def test_energy_spike_detection(self):
        """Test energy spike detection"""
        result_df = detect_energy_spikes(self.test_data.copy())
        
        # Verify results
        self.assertIn('energy_spike', result_df.columns)
        self.assertIn('spike_score', result_df.columns)
        self.assertTrue(result_df['energy_spike'].dtype == bool)
        self.assertTrue(result_df['spike_score'].dtype == float)
        
        # Check if known spikes are detected
        self.assertTrue(result_df.loc[100, 'energy_spike'])
        self.assertTrue(result_df.loc[200, 'energy_spike'])
        self.assertTrue(result_df.loc[300, 'energy_spike'])

    def test_isolation_forest_detection(self):
        """Test Isolation Forest anomaly detection"""
        result_df = detect_anomalies(self.test_data.copy(), self.model)
        
        # Verify results
        self.assertIn('anomaly', result_df.columns)
        self.assertIn('anomaly_score', result_df.columns)
        self.assertIn('severity', result_df.columns)
        self.assertTrue(result_df['anomaly'].dtype == int)
        self.assertTrue(result_df['anomaly_score'].dtype == float)
        self.assertTrue(result_df['severity'].dtype == object)
        
        # Check if known anomalies are detected
        self.assertEqual(result_df.loc[100, 'anomaly'], -1)
        self.assertEqual(result_df.loc[200, 'anomaly'], -1)
        self.assertEqual(result_df.loc[300, 'anomaly'], -1)
        
        # Verify severity levels
        self.assertIn(result_df.loc[100, 'severity'], ['high', 'medium', 'low'])
        self.assertIn(result_df.loc[200, 'severity'], ['high', 'medium', 'low'])
        self.assertIn(result_df.loc[300, 'severity'], ['high', 'medium', 'low'])

    def test_combined_detection(self):
        """Test combined anomaly detection methods"""
        # Run all detection methods
        df = detect_statistical_anomalies(self.test_data.copy())
        df = detect_consecutive_anomalies(df)
        df = detect_energy_spikes(df)
        df = detect_anomalies(df, self.model)
        
        # Verify all detection columns are present
        required_columns = [
            'statistical_anomaly',
            'consecutive_anomaly',
            'energy_spike',
            'anomaly',
            'severity'
        ]
        for col in required_columns:
            self.assertIn(col, df.columns)
        
        # Check if known anomalies are detected by at least one method
        anomaly_indices = [100, 200, 300] + list(range(400, 410))
        for idx in anomaly_indices:
            self.assertTrue(
                df.loc[idx, 'statistical_anomaly'] or
                df.loc[idx, 'consecutive_anomaly'] or
                df.loc[idx, 'energy_spike'] or
                df.loc[idx, 'anomaly'] == -1
            )

if __name__ == '__main__':
    unittest.main() 