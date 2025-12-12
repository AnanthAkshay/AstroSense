"""
Synthetic Training Data Generator for Space Weather ML Model
Generates historical scenarios and injects synthetic anomalies
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from utils.logger import setup_logger

logger = setup_logger(__name__)


class SyntheticDataGenerator:
    """
    Generates synthetic space weather training data with labeled outcomes
    """
    
    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        self.data_points: List[Dict] = []
    
    def generate_normal_conditions(self, num_samples: int = 500) -> pd.DataFrame:
        """
        Generate normal space weather conditions
        
        Args:
            num_samples: Number of samples to generate
            
        Returns:
            DataFrame with normal conditions
        """
        logger.info(f"Generating {num_samples} normal condition samples")
        
        data = {
            'solar_wind_speed': np.random.normal(450, 80, num_samples).clip(250, 700),
            'bz_field': np.random.normal(0, 5, num_samples).clip(-20, 20),
            'kp_index': np.random.gamma(2, 1.5, num_samples).clip(0, 6),
            'proton_flux': np.random.lognormal(5, 2, num_samples).clip(1, 1000),
            'cme_speed': np.zeros(num_samples),  # No CME
            'flare_class_encoded': np.random.choice([0, 1, 2, 3], num_samples, p=[0.4, 0.3, 0.2, 0.1]),
            
            # Impact labels (low for normal conditions)
            'aviation_impact': np.random.uniform(0, 30, num_samples),
            'telecom_impact': np.random.uniform(0, 25, num_samples),
            'gps_drift': np.random.uniform(0, 40, num_samples),
            'power_grid_risk': np.random.randint(1, 4, num_samples),
            'satellite_drag_risk': np.random.randint(1, 4, num_samples)
        }
        
        return pd.DataFrame(data)
    
    def generate_moderate_storm(self, num_samples: int = 300) -> pd.DataFrame:
        """
        Generate moderate geomagnetic storm conditions
        
        Args:
            num_samples: Number of samples to generate
            
        Returns:
            DataFrame with moderate storm conditions
        """
        logger.info(f"Generating {num_samples} moderate storm samples")
        
        data = {
            'solar_wind_speed': np.random.normal(550, 100, num_samples).clip(400, 800),
            'bz_field': np.random.normal(-8, 6, num_samples).clip(-40, 10),
            'kp_index': np.random.normal(5, 1.5, num_samples).clip(4, 7),
            'proton_flux': np.random.lognormal(7, 2, num_samples).clip(100, 10000),
            'cme_speed': np.random.normal(600, 150, num_samples).clip(300, 1000),
            'flare_class_encoded': np.random.choice([2, 3, 4], num_samples, p=[0.3, 0.5, 0.2]),
            
            # Impact labels (moderate)
            'aviation_impact': np.random.uniform(30, 60, num_samples),
            'telecom_impact': np.random.uniform(25, 50, num_samples),
            'gps_drift': np.random.uniform(40, 100, num_samples),
            'power_grid_risk': np.random.randint(4, 7, num_samples),
            'satellite_drag_risk': np.random.randint(4, 7, num_samples)
        }
        
        return pd.DataFrame(data)
    
    def generate_severe_storm(self, num_samples: int = 150) -> pd.DataFrame:
        """
        Generate severe geomagnetic storm conditions
        
        Args:
            num_samples: Number of samples to generate
            
        Returns:
            DataFrame with severe storm conditions
        """
        logger.info(f"Generating {num_samples} severe storm samples")
        
        data = {
            'solar_wind_speed': np.random.normal(700, 120, num_samples).clip(600, 950),
            'bz_field': np.random.normal(-20, 10, num_samples).clip(-60, -5),
            'kp_index': np.random.normal(7, 1, num_samples).clip(6, 9),
            'proton_flux': np.random.lognormal(9, 2, num_samples).clip(1000, 100000),
            'cme_speed': np.random.normal(1200, 300, num_samples).clip(800, 2000),
            'flare_class_encoded': np.random.choice([4, 5], num_samples, p=[0.4, 0.6]),
            
            # Impact labels (severe)
            'aviation_impact': np.random.uniform(60, 95, num_samples),
            'telecom_impact': np.random.uniform(50, 85, num_samples),
            'gps_drift': np.random.uniform(100, 250, num_samples),
            'power_grid_risk': np.random.randint(7, 10, num_samples),
            'satellite_drag_risk': np.random.randint(7, 10, num_samples)
        }
        
        return pd.DataFrame(data)
    
    def inject_synthetic_anomalies(self, num_anomalies: int = 50) -> pd.DataFrame:
        """
        Generate synthetic anomalies for rare event training
        
        Args:
            num_anomalies: Number of anomalies to generate
            
        Returns:
            DataFrame with synthetic anomalies
        """
        logger.info(f"Injecting {num_anomalies} synthetic anomalies")
        
        anomalies = []
        
        for _ in range(num_anomalies):
            anomaly_type = np.random.choice(['high_cme', 'extreme_bz', 'kp_spike'])
            
            if anomaly_type == 'high_cme':
                # Artificial high-speed CME (> 1500 km/s)
                anomaly = {
                    'solar_wind_speed': np.random.uniform(750, 950),
                    'bz_field': np.random.uniform(-50, -15),
                    'kp_index': np.random.uniform(7, 9),
                    'proton_flux': np.random.uniform(10000, 500000),
                    'cme_speed': np.random.uniform(1500, 2500),  # Extreme CME
                    'flare_class_encoded': np.random.uniform(4.5, 5.9),
                    
                    'aviation_impact': np.random.uniform(85, 100),
                    'telecom_impact': np.random.uniform(75, 95),
                    'gps_drift': np.random.uniform(200, 400),
                    'power_grid_risk': np.random.randint(8, 11),
                    'satellite_drag_risk': np.random.randint(8, 11)
                }
            
            elif anomaly_type == 'extreme_bz':
                # Extreme negative Bz cluster (< -30 nT)
                anomaly = {
                    'solar_wind_speed': np.random.uniform(650, 850),
                    'bz_field': np.random.uniform(-80, -30),  # Extreme Bz
                    'kp_index': np.random.uniform(7.5, 9),
                    'proton_flux': np.random.uniform(5000, 200000),
                    'cme_speed': np.random.uniform(1000, 1800),
                    'flare_class_encoded': np.random.uniform(4, 5.5),
                    
                    'aviation_impact': np.random.uniform(80, 98),
                    'telecom_impact': np.random.uniform(70, 90),
                    'gps_drift': np.random.uniform(180, 350),
                    'power_grid_risk': np.random.randint(8, 11),
                    'satellite_drag_risk': np.random.randint(7, 10)
                }
            
            else:  # kp_spike
                # Sudden Kp spike (> 8)
                anomaly = {
                    'solar_wind_speed': np.random.uniform(700, 900),
                    'bz_field': np.random.uniform(-40, -10),
                    'kp_index': np.random.uniform(8, 9),  # Extreme Kp
                    'proton_flux': np.random.uniform(8000, 300000),
                    'cme_speed': np.random.uniform(1100, 2000),
                    'flare_class_encoded': np.random.uniform(4.2, 5.8),
                    
                    'aviation_impact': np.random.uniform(82, 99),
                    'telecom_impact': np.random.uniform(72, 92),
                    'gps_drift': np.random.uniform(190, 380),
                    'power_grid_risk': np.random.randint(8, 11),
                    'satellite_drag_risk': np.random.randint(8, 11)
                }
            
            anomalies.append(anomaly)
        
        return pd.DataFrame(anomalies)
    
    def generate_training_dataset(
        self,
        normal_samples: int = 500,
        moderate_samples: int = 300,
        severe_samples: int = 150,
        anomaly_samples: int = 50
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generate complete training dataset with all conditions
        
        Args:
            normal_samples: Number of normal condition samples
            moderate_samples: Number of moderate storm samples
            severe_samples: Number of severe storm samples
            anomaly_samples: Number of synthetic anomalies
            
        Returns:
            Tuple of (features_df, labels_df)
        """
        logger.info("Generating complete training dataset")
        
        # Generate all condition types
        normal_df = self.generate_normal_conditions(normal_samples)
        moderate_df = self.generate_moderate_storm(moderate_samples)
        severe_df = self.generate_severe_storm(severe_samples)
        anomaly_df = self.inject_synthetic_anomalies(anomaly_samples)
        
        # Combine all data
        full_df = pd.concat([normal_df, moderate_df, severe_df, anomaly_df], ignore_index=True)
        
        # Shuffle the dataset
        full_df = full_df.sample(frac=1, random_state=42).reset_index(drop=True)
        
        # Split features and labels
        feature_columns = [
            'solar_wind_speed', 'bz_field', 'kp_index', 'proton_flux',
            'cme_speed', 'flare_class_encoded'
        ]
        
        label_columns = [
            'aviation_impact', 'telecom_impact', 'gps_drift',
            'power_grid_risk', 'satellite_drag_risk'
        ]
        
        features = full_df[feature_columns]
        labels = full_df[label_columns]
        
        logger.info(f"Generated dataset: {len(full_df)} total samples")
        logger.info(f"Features shape: {features.shape}, Labels shape: {labels.shape}")
        
        return features, labels
    
    def create_train_val_test_split(
        self,
        features: pd.DataFrame,
        labels: pd.DataFrame,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Split data into train, validation, and test sets
        
        Args:
            features: Feature DataFrame
            labels: Label DataFrame
            train_ratio: Proportion for training
            val_ratio: Proportion for validation
            test_ratio: Proportion for testing
            
        Returns:
            Tuple of (X_train, X_val, X_test, y_train, y_val, y_test)
        """
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 0.01, \
            "Ratios must sum to 1.0"
        
        n = len(features)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))
        
        X_train = features.iloc[:train_end]
        X_val = features.iloc[train_end:val_end]
        X_test = features.iloc[val_end:]
        
        y_train = labels.iloc[:train_end]
        y_val = labels.iloc[train_end:val_end]
        y_test = labels.iloc[val_end:]
        
        logger.info(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
        
        return X_train, X_val, X_test, y_train, y_val, y_test
    
    def save_dataset(self, features: pd.DataFrame, labels: pd.DataFrame, filepath: str):
        """
        Save dataset to CSV file
        
        Args:
            features: Feature DataFrame
            labels: Label DataFrame
            filepath: Path to save file
        """
        combined = pd.concat([features, labels], axis=1)
        combined.to_csv(filepath, index=False)
        logger.info(f"Saved dataset to {filepath}")


if __name__ == "__main__":
    # Example usage
    generator = SyntheticDataGenerator()
    features, labels = generator.generate_training_dataset(
        normal_samples=500,
        moderate_samples=300,
        severe_samples=150,
        anomaly_samples=50
    )
    
    X_train, X_val, X_test, y_train, y_val, y_test = generator.create_train_val_test_split(
        features, labels
    )
    
    print(f"Training set: {X_train.shape}")
    print(f"Validation set: {X_val.shape}")
    print(f"Test set: {X_test.shape}")
