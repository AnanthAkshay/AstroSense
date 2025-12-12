"""
Random Forest Model Trainer for Space Weather Impact Prediction
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib
import json
from typing import Dict, Tuple, Optional
from datetime import datetime
from pathlib import Path
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ModelTrainer:
    """
    Trains Random Forest models for space weather impact prediction
    """
    
    def __init__(self, model_dir: str = "./ml_models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.model: Optional[RandomForestRegressor] = None
        self.model_metadata: Dict = {}
        self.feature_importance: Dict = {}
    
    def create_model(
        self,
        n_estimators: int = 100,
        max_depth: Optional[int] = 20,
        min_samples_split: int = 5,
        min_samples_leaf: int = 2,
        random_state: int = 42
    ) -> RandomForestRegressor:
        """
        Create Random Forest Regressor with optimal hyperparameters
        
        Args:
            n_estimators: Number of trees in the forest
            max_depth: Maximum depth of trees
            min_samples_split: Minimum samples required to split
            min_samples_leaf: Minimum samples required at leaf node
            random_state: Random seed for reproducibility
            
        Returns:
            Configured RandomForestRegressor
        """
        logger.info(f"Creating Random Forest model with {n_estimators} estimators")
        
        model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
            random_state=random_state,
            n_jobs=-1,  # Use all CPU cores
            verbose=1
        )
        
        self.model = model
        return model
    
    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.DataFrame,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.DataFrame] = None
    ) -> Dict[str, float]:
        """
        Train the Random Forest model
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features (optional)
            y_val: Validation labels (optional)
            
        Returns:
            Dictionary of training metrics
        """
        if self.model is None:
            self.create_model()
        
        logger.info(f"Training on {len(X_train)} samples")
        
        # Verify minimum data requirement
        if len(X_train) < 1000:
            logger.warning(f"Training with {len(X_train)} samples (< 1000 recommended)")
        
        # Train the model
        self.model.fit(X_train, y_train)
        
        # Calculate training metrics
        y_train_pred = self.model.predict(X_train)
        train_mse = mean_squared_error(y_train, y_train_pred)
        train_r2 = r2_score(y_train, y_train_pred)
        train_mae = mean_absolute_error(y_train, y_train_pred)
        
        metrics = {
            'train_mse': float(train_mse),
            'train_r2': float(train_r2),
            'train_mae': float(train_mae),
            'n_samples': len(X_train)
        }
        
        logger.info(f"Training MSE: {train_mse:.4f}, R²: {train_r2:.4f}, MAE: {train_mae:.4f}")
        
        # Validation metrics if provided
        if X_val is not None and y_val is not None:
            y_val_pred = self.model.predict(X_val)
            val_mse = mean_squared_error(y_val, y_val_pred)
            val_r2 = r2_score(y_val, y_val_pred)
            val_mae = mean_absolute_error(y_val, y_val_pred)
            
            metrics.update({
                'val_mse': float(val_mse),
                'val_r2': float(val_r2),
                'val_mae': float(val_mae)
            })
            
            logger.info(f"Validation MSE: {val_mse:.4f}, R²: {val_r2:.4f}, MAE: {val_mae:.4f}")
            
            # Check if validation accuracy meets 75% threshold (R² >= 0.75)
            if val_r2 >= 0.75:
                logger.info(f"✓ Model meets 75% accuracy threshold (R² = {val_r2:.2%})")
            else:
                logger.warning(f"✗ Model below 75% accuracy threshold (R² = {val_r2:.2%})")
        
        # Calculate feature importance
        self.calculate_feature_importance(X_train.columns)
        
        return metrics
    
    def cross_validate(
        self,
        X: pd.DataFrame,
        y: pd.DataFrame,
        cv: int = 5
    ) -> Dict[str, float]:
        """
        Perform cross-validation for model selection
        
        Args:
            X: Features
            y: Labels
            cv: Number of cross-validation folds
            
        Returns:
            Dictionary of cross-validation scores
        """
        if self.model is None:
            self.create_model()
        
        logger.info(f"Performing {cv}-fold cross-validation")
        
        # Cross-validation for R² score
        cv_scores = cross_val_score(
            self.model, X, y,
            cv=cv,
            scoring='r2',
            n_jobs=-1
        )
        
        # Cross-validation for MSE
        cv_mse = -cross_val_score(
            self.model, X, y,
            cv=cv,
            scoring='neg_mean_squared_error',
            n_jobs=-1
        )
        
        results = {
            'cv_r2_mean': float(cv_scores.mean()),
            'cv_r2_std': float(cv_scores.std()),
            'cv_mse_mean': float(cv_mse.mean()),
            'cv_mse_std': float(cv_mse.std())
        }
        
        logger.info(f"CV R² = {results['cv_r2_mean']:.4f} ± {results['cv_r2_std']:.4f}")
        logger.info(f"CV MSE = {results['cv_mse_mean']:.4f} ± {results['cv_mse_std']:.4f}")
        
        return results
    
    def calculate_feature_importance(self, feature_names: list):
        """
        Calculate and store feature importance
        
        Args:
            feature_names: List of feature names
        """
        if self.model is None:
            logger.warning("Model not trained yet")
            return
        
        importances = self.model.feature_importances_
        
        self.feature_importance = {
            name: float(importance)
            for name, importance in zip(feature_names, importances)
        }
        
        # Sort by importance
        sorted_importance = sorted(
            self.feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        logger.info("Feature Importance (top 5):")
        for name, importance in sorted_importance[:5]:
            logger.info(f"  {name}: {importance:.4f}")
    
    def save_model(
        self,
        version: str = "1.0.0",
        metrics: Optional[Dict] = None
    ) -> str:
        """
        Save trained model with versioning metadata
        
        Args:
            version: Model version string
            metrics: Training metrics to save
            
        Returns:
            Path to saved model file
        """
        if self.model is None:
            raise ValueError("No model to save. Train a model first.")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_filename = f"random_forest_v{version}_{timestamp}.pkl"
        model_path = self.model_dir / model_filename
        
        # Save model
        joblib.dump(self.model, model_path)
        logger.info(f"Model saved to {model_path}")
        
        # Create metadata
        self.model_metadata = {
            'version': version,
            'timestamp': timestamp,
            'model_type': 'RandomForestRegressor',
            'n_estimators': self.model.n_estimators,
            'max_depth': self.model.max_depth,
            'feature_importance': self.feature_importance,
            'metrics': metrics or {},
            'model_file': model_filename
        }
        
        # Save metadata
        metadata_path = self.model_dir / f"metadata_v{version}_{timestamp}.json"
        with open(metadata_path, 'w') as f:
            json.dump(self.model_metadata, f, indent=2)
        
        logger.info(f"Metadata saved to {metadata_path}")
        
        return str(model_path)
    
    def load_model(self, model_path: str) -> RandomForestRegressor:
        """
        Load a trained model from disk
        
        Args:
            model_path: Path to model file
            
        Returns:
            Loaded RandomForestRegressor
        """
        logger.info(f"Loading model from {model_path}")
        
        self.model = joblib.load(model_path)
        
        # Try to load metadata
        metadata_path = model_path.replace('.pkl', '_metadata.json')
        if Path(metadata_path).exists():
            with open(metadata_path, 'r') as f:
                self.model_metadata = json.load(f)
            logger.info(f"Loaded metadata: version {self.model_metadata.get('version')}")
        
        return self.model
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions using trained model
        
        Args:
            X: Feature DataFrame
            
        Returns:
            Predictions array
        """
        if self.model is None:
            raise ValueError("No model loaded. Train or load a model first.")
        
        predictions = self.model.predict(X)
        return predictions
    
    def evaluate(
        self,
        X_test: pd.DataFrame,
        y_test: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Evaluate model on test set
        
        Args:
            X_test: Test features
            y_test: Test labels
            
        Returns:
            Dictionary of evaluation metrics
        """
        if self.model is None:
            raise ValueError("No model loaded. Train or load a model first.")
        
        logger.info(f"Evaluating on {len(X_test)} test samples")
        
        y_pred = self.model.predict(X_test)
        
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        
        # Calculate per-output metrics
        per_output_metrics = {}
        for i, col in enumerate(y_test.columns):
            col_mse = mean_squared_error(y_test.iloc[:, i], y_pred[:, i])
            col_r2 = r2_score(y_test.iloc[:, i], y_pred[:, i])
            per_output_metrics[col] = {
                'mse': float(col_mse),
                'r2': float(col_r2)
            }
        
        metrics = {
            'test_mse': float(mse),
            'test_r2': float(r2),
            'test_mae': float(mae),
            'per_output': per_output_metrics
        }
        
        logger.info(f"Test MSE: {mse:.4f}, R²: {r2:.4f}, MAE: {mae:.4f}")
        
        return metrics


if __name__ == "__main__":
    # Example usage
    from ml.synthetic_data_generator import SyntheticDataGenerator
    
    # Generate training data
    generator = SyntheticDataGenerator()
    features, labels = generator.generate_training_dataset()
    
    X_train, X_val, X_test, y_train, y_val, y_test = generator.create_train_val_test_split(
        features, labels
    )
    
    # Train model
    trainer = ModelTrainer()
    trainer.create_model(n_estimators=100)
    
    # Cross-validation
    cv_results = trainer.cross_validate(X_train, y_train, cv=5)
    
    # Train
    train_metrics = trainer.train(X_train, y_train, X_val, y_val)
    
    # Evaluate
    test_metrics = trainer.evaluate(X_test, y_test)
    
    # Save
    model_path = trainer.save_model(version="1.0.0", metrics=test_metrics)
    
    print(f"Model saved to: {model_path}")
    print(f"Test R²: {test_metrics['test_r2']:.4f}")
