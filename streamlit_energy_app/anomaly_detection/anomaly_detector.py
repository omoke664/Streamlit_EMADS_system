# anomaly_detector.py

import pandas as pd
from sklearn.ensemble import IsolationForest

class AnomalyDetector:
    def __init__(self, n_estimators=100, contamination=0.01, random_state=42):
        self.model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            random_state=random_state
        )

    def fit(self, df: pd.DataFrame, feature_cols: list):
        self.feature_cols = feature_cols
        X = df[feature_cols].values
        self.model.fit(X)

    def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        X = df[self.feature_cols].values
        scores = self.model.decision_function(X)
        labels = self.model.predict(X)

        df = df.copy()
        df["anomaly_score"] = scores
        df["is_anomaly"] = labels == -1
        return df

    def fit_detect(self, df: pd.DataFrame, feature_cols: list) -> pd.DataFrame:
        self.fit(df, feature_cols)
        return self.detect(df)
