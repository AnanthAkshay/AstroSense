"""
Fusion Combiner for ML + Physics Predictions
Combines machine learning and physics-based predictions with weighted fusion
"""
from typing import Dict, Any, List, Tuple
import numpy as np
from utils.logger import setup_logger

logger = setup_logger(__name__)


class FusionCombiner:
    """
    Combines ML predictions (60%) with physics rules (40%)
    Resolves conflicts using conservative estimates
    """
    
    def __init__(self, ml_weight: float = 0.6, physics_weight: float = 0.4):
        self.ml_weight = ml_weight
        self.physics_weight = physics_weight
        self.discrepancy_log: List[Dict] = []
        
        # Verify weights sum to 1.0
        assert abs(ml_weight + physics_weight - 1.0) < 0.01, \
            "Weights must sum to 1.0"
    
    def combine_predictions(
        self,
        ml_predictions: Dict[str, float],
        physics_predictions: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Combine ML and physics predictions with weighted fusion
        
        Args:
            ml_predictions: Predictions from ML model
            physics_predictions: Predictions from physics rules
            
        Returns:
            Combined predictions dictionary
        """
        combined = {}
        
        # Get all unique keys from both predictions
        all_keys = set(ml_predictions.keys()) | set(physics_predictions.keys())
        
        for key in all_keys:
            ml_val = ml_predictions.get(key, 0.0)
            physics_val = physics_predictions.get(key, 0.0)
            
            # Weighted combination: 60% ML + 40% Physics
            combined_val = (self.ml_weight * ml_val) + (self.physics_weight * physics_val)
            
            combined[key] = combined_val
            
            logger.debug(f"{key}: ML={ml_val:.2f}, Physics={physics_val:.2f}, "
                        f"Combined={combined_val:.2f}")
        
        logger.info(f"Combined {len(combined)} predictions using {self.ml_weight:.0%} ML "
                   f"+ {self.physics_weight:.0%} Physics")
        
        return combined
    
    def resolve_conflicts(
        self,
        ml_value: float,
        physics_value: float,
        field_name: str,
        threshold: float = 20.0
    ) -> Tuple[float, bool]:
        """
        Resolve conflicts between ML and physics predictions
        Uses conservative estimate (higher risk) when predictions differ significantly
        
        Args:
            ml_value: ML prediction value
            physics_value: Physics prediction value
            field_name: Name of the field being predicted
            threshold: Threshold for considering predictions conflicting (default: 20.0)
            
        Returns:
            Tuple of (resolved_value, is_conflict)
        """
        # Calculate difference
        diff = abs(ml_value - physics_value)
        
        # Check if predictions conflict (differ by more than threshold)
        is_conflict = diff > threshold
        
        if is_conflict:
            # Use conservative estimate (higher risk)
            resolved = max(ml_value, physics_value)
            
            # Log discrepancy
            discrepancy = {
                'field': field_name,
                'ml_value': ml_value,
                'physics_value': physics_value,
                'difference': diff,
                'resolved_value': resolved,
                'resolution': 'conservative'
            }
            self.discrepancy_log.append(discrepancy)
            
            logger.warning(f"Conflict detected for {field_name}: ML={ml_value:.2f}, "
                          f"Physics={physics_value:.2f}, diff={diff:.2f}. "
                          f"Using conservative estimate: {resolved:.2f}")
        else:
            # No significant conflict, use weighted combination
            resolved = (self.ml_weight * ml_value) + (self.physics_weight * physics_value)
        
        return resolved, is_conflict
    
    def fuse_with_conflict_resolution(
        self,
        ml_predictions: Dict[str, float],
        physics_predictions: Dict[str, float],
        conflict_threshold: float = 20.0
    ) -> Dict[str, Any]:
        """
        Fuse predictions with explicit conflict resolution
        
        Args:
            ml_predictions: ML model predictions
            physics_predictions: Physics rules predictions
            conflict_threshold: Threshold for conflict detection
            
        Returns:
            Dictionary with fused predictions and conflict information
        """
        fused = {}
        conflicts = {}
        
        all_keys = set(ml_predictions.keys()) | set(physics_predictions.keys())
        
        for key in all_keys:
            ml_val = ml_predictions.get(key, 0.0)
            physics_val = physics_predictions.get(key, 0.0)
            
            resolved_val, is_conflict = self.resolve_conflicts(
                ml_val, physics_val, key, conflict_threshold
            )
            
            fused[key] = resolved_val
            
            if is_conflict:
                conflicts[key] = {
                    'ml': ml_val,
                    'physics': physics_val,
                    'resolved': resolved_val
                }
        
        result = {
            'predictions': fused,
            'conflicts': conflicts,
            'num_conflicts': len(conflicts)
        }
        
        if conflicts:
            logger.info(f"Resolved {len(conflicts)} conflicts using conservative estimates")
        
        return result
    
    def get_prediction_confidence(
        self,
        ml_predictions: Dict[str, float],
        physics_predictions: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate confidence scores for fused predictions
        
        Higher confidence when ML and physics agree
        Lower confidence when they conflict
        
        Args:
            ml_predictions: ML predictions
            physics_predictions: Physics predictions
            
        Returns:
            Dictionary of confidence scores [0, 1] for each prediction
        """
        confidence = {}
        
        all_keys = set(ml_predictions.keys()) | set(physics_predictions.keys())
        
        for key in all_keys:
            ml_val = ml_predictions.get(key, 0.0)
            physics_val = physics_predictions.get(key, 0.0)
            
            # Calculate agreement (inverse of normalized difference)
            if ml_val == 0 and physics_val == 0:
                agreement = 1.0
            else:
                max_val = max(abs(ml_val), abs(physics_val), 1.0)
                diff = abs(ml_val - physics_val)
                agreement = 1.0 - min(diff / max_val, 1.0)
            
            # Confidence is high when predictions agree
            confidence[key] = agreement
        
        return confidence
    
    def get_discrepancy_summary(self) -> Dict[str, Any]:
        """
        Get summary of logged discrepancies
        
        Returns:
            Summary statistics of discrepancies
        """
        if not self.discrepancy_log:
            return {
                'total_discrepancies': 0,
                'fields_with_conflicts': [],
                'average_difference': 0.0
            }
        
        fields = [d['field'] for d in self.discrepancy_log]
        differences = [d['difference'] for d in self.discrepancy_log]
        
        summary = {
            'total_discrepancies': len(self.discrepancy_log),
            'fields_with_conflicts': list(set(fields)),
            'average_difference': np.mean(differences),
            'max_difference': np.max(differences),
            'recent_discrepancies': self.discrepancy_log[-10:]  # Last 10
        }
        
        return summary
    
    def clear_discrepancy_log(self):
        """Clear the discrepancy log"""
        self.discrepancy_log.clear()
        logger.info("Discrepancy log cleared")


# Global instance
fusion_combiner = FusionCombiner(ml_weight=0.6, physics_weight=0.4)
