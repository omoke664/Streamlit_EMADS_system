import numpy as np
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score
from sklearn.ensemble import IsolationForest
import time
from typing import Dict, Tuple, List
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from anomalies import (
    detect_statistical_anomalies,
    detect_consecutive_anomalies,
    detect_energy_spikes,
    detect_anomalies
)

def calculate_detection_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Calculate precision, recall, and F1 score for anomaly detection.
    
    Args:
        y_true: True labels (1 for normal, -1 for anomaly)
        y_pred: Predicted labels (1 for normal, -1 for anomaly)
    
    Returns:
        Dictionary containing precision, recall, and F1 score
    """
    try:
        # Convert to binary (0 for normal, 1 for anomaly)
        y_true_binary = (y_true == -1).astype(int)
        y_pred_binary = (y_pred == -1).astype(int)
        
        metrics = {
            'precision': precision_score(y_true_binary, y_pred_binary),
            'recall': recall_score(y_true_binary, y_pred_binary),
            'f1_score': f1_score(y_true_binary, y_pred_binary)
        }
        
        return metrics
    except Exception as e:
        print(f"Error calculating detection metrics: {str(e)}")
        return {'precision': 0, 'recall': 0, 'f1_score': 0}

def calculate_false_positive_rate(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate false positive rate for anomaly detection.
    
    Args:
        y_true: True labels (1 for normal, -1 for anomaly)
        y_pred: Predicted labels (1 for normal, -1 for anomaly)
    
    Returns:
        False positive rate
    """
    try:
        # Convert to binary (0 for normal, 1 for anomaly)
        y_true_binary = (y_true == -1).astype(int)
        y_pred_binary = (y_pred == -1).astype(int)
        
        # Calculate false positives
        false_positives = np.sum((y_pred_binary == 1) & (y_true_binary == 0))
        total_negatives = np.sum(y_true_binary == 0)
        
        return false_positives / total_negatives if total_negatives > 0 else 0
    except Exception as e:
        print(f"Error calculating false positive rate: {str(e)}")
        return 0

def measure_processing_time(func, *args, **kwargs) -> float:
    """
    Measure processing time of a function.
    
    Args:
        func: Function to measure
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
    
    Returns:
        Processing time in seconds
    """
    try:
        start_time = time.time()
        func(*args, **kwargs)
        end_time = time.time()
        return end_time - start_time
    except Exception as e:
        print(f"Error measuring processing time: {str(e)}")
        return 0

def evaluate_anomaly_detection(
    test_data: pd.DataFrame,
    detection_functions: List[Tuple[callable, str]],
    true_anomalies: List[int]
) -> Dict[str, Dict[str, float]]:
    """
    Evaluate multiple anomaly detection methods.
    
    Args:
        test_data: DataFrame containing test data
        detection_functions: List of tuples (function, name)
        true_anomalies: List of indices where true anomalies exist
    
    Returns:
        Dictionary containing metrics for each detection method
    """
    results = {}
    
    try:
        # Create true labels array
        y_true = np.ones(len(test_data))
        y_true[true_anomalies] = -1
        
        for func, name in detection_functions:
            try:
                print(f"\nEvaluating {name} detection...")
                
                # Measure processing time
                processing_time = measure_processing_time(func, test_data.copy())
                
                # Get predictions
                result_df = func(test_data.copy())
                
                # Extract predictions based on the function's output format
                if name == 'Statistical':
                    y_pred = np.where(result_df['statistical_anomaly'], -1, 1)
                elif name == 'Consecutive':
                    # For consecutive detection, we need to run statistical first
                    stat_df = detect_statistical_anomalies(test_data.copy())
                    result_df = detect_consecutive_anomalies(stat_df)
                    y_pred = np.where(result_df['consecutive_anomaly'], -1, 1)
                elif name == 'Spike':
                    y_pred = np.where(result_df['energy_spike'], -1, 1)
                elif name == 'Isolation Forest':
                    y_pred = result_df['anomaly'].values
                else:
                    raise ValueError(f"Unknown detection method: {name}")
                
                # Calculate metrics
                metrics = calculate_detection_metrics(y_true, y_pred)
                fpr = calculate_false_positive_rate(y_true, y_pred)
                
                results[name] = {
                    **metrics,
                    'false_positive_rate': fpr,
                    'processing_time': processing_time / len(test_data)  # per data point
                }
                
                print(f"Completed {name} detection evaluation")
                print(f"Predictions shape: {y_pred.shape}")
                print(f"Number of anomalies detected: {np.sum(y_pred == -1)}")
                
            except Exception as e:
                print(f"Error evaluating {name} detection: {str(e)}")
                results[name] = {
                    'precision': 0,
                    'recall': 0,
                    'f1_score': 0,
                    'false_positive_rate': 0,
                    'processing_time': 0
                }
        
        return results
        
    except Exception as e:
        print(f"Error in evaluation: {str(e)}")
        return {}

def plot_metrics(results: Dict[str, Dict[str, float]], save_path: str = None):
    """
    Plot performance metrics for different detection methods.
    
    Args:
        results: Dictionary containing metrics for each method
        save_path: Optional path to save the plot
    """
    try:
        # Prepare data for plotting
        methods = list(results.keys())
        metrics = ['precision', 'recall', 'f1_score', 'false_positive_rate']
        
        # Create subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        axes = axes.ravel()
        
        for i, metric in enumerate(metrics):
            values = [results[method][metric] for method in methods]
            sns.barplot(x=methods, y=values, ax=axes[i])
            axes[i].set_title(f'{metric.replace("_", " ").title()}')
            axes[i].set_ylim(0, 1)
            plt.setp(axes[i].xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path)
        plt.show()
        
    except Exception as e:
        print(f"Error plotting metrics: {str(e)}")

def main():
    try:
        print("Starting anomaly detection evaluation...")
        
        # Create test data
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='h')
        normal_consumption = np.random.normal(1000, 100, len(dates))
        
        test_data = pd.DataFrame({
            'timestamp': dates,
            'energy_wh': normal_consumption
        })
        
        # Add spike anomalies
        spike_indices = [100, 200, 300]
        test_data.loc[spike_indices, 'energy_wh'] *= 3
        
        # Add consecutive anomalies
        consecutive_indices = range(400, 410)
        test_data.loc[consecutive_indices, 'energy_wh'] *= 2.5
        
        # Add some random noise to make detection more realistic
        noise = np.random.normal(0, 50, len(test_data))
        test_data['energy_wh'] += noise
        
        # Train Isolation Forest model
        model = IsolationForest(
            contamination=0.05,  # Increased contamination to detect more anomalies
            random_state=42,
            n_estimators=100
        )
        model.fit(test_data[['energy_wh']].values)
        
        # Define detection functions to evaluate
        detection_functions = [
            (detect_statistical_anomalies, 'Statistical'),
            (detect_consecutive_anomalies, 'Consecutive'),
            (detect_energy_spikes, 'Spike'),
            (lambda df: detect_anomalies(df, model), 'Isolation Forest')
        ]
        
        # Define true anomalies
        true_anomalies = [100, 200, 300] + list(range(400, 410))
        
        # Evaluate all methods
        results = evaluate_anomaly_detection(
            test_data,
            detection_functions,
            true_anomalies
        )
        
        # Print results
        print("\nAnomaly Detection Performance Metrics:")
        print("=====================================")
        for method, metrics in results.items():
            print(f"\n{method} Detection:")
            for metric, value in metrics.items():
                print(f"{metric.replace('_', ' ').title()}: {value:.3f}")
        
        # Plot results
        plot_metrics(results, 'anomaly_detection_metrics.png')
        
    except Exception as e:
        print(f"Error in main: {str(e)}")

if __name__ == '__main__':
    main() 