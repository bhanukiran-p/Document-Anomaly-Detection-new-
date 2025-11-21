"""
Model Evaluator for Money Order Fraud Detection
Provides detailed metrics, visualizations, and performance analysis
"""

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    roc_curve, precision_recall_curve
)
from typing import Dict, Tuple, Optional


class ModelEvaluator:
    """
    Evaluate trained ML models with comprehensive metrics and analysis
    """

    def __init__(self):
        self.metrics = {}
        self.confusion_matrices = {}

    def evaluate_model(self, model, X_test: np.ndarray, y_test: np.ndarray,
                      model_name: str = "Model") -> Dict[str, float]:
        """
        Comprehensive model evaluation

        Args:
            model: Trained model with predict() and predict_proba() methods
            X_test: Test feature matrix
            y_test: True labels
            model_name: Name for the model

        Returns:
            Dictionary of metrics
        """
        print(f"\n{'='*60}")
        print(f"Evaluating {model_name}")
        print(f"{'='*60}")

        # Get predictions
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else None

        # Calculate metrics
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, zero_division=0),
            'recall': recall_score(y_test, y_pred, zero_division=0),
            'f1_score': f1_score(y_test, y_pred, zero_division=0),
            'specificity': self._calculate_specificity(y_test, y_pred)
        }

        if y_proba is not None:
            metrics['roc_auc'] = roc_auc_score(y_test, y_proba)

        # Display metrics
        print(f"\nPerformance Metrics:")
        print(f"  Accuracy:   {metrics['accuracy']:.4f}")
        print(f"  Precision:  {metrics['precision']:.4f} (fraud detection accuracy)")
        print(f"  Recall:     {metrics['recall']:.4f} (fraud catch rate)")
        print(f"  F1-Score:   {metrics['f1_score']:.4f}")
        print(f"  Specificity:{metrics['specificity']:.4f} (true negative rate)")
        if 'roc_auc' in metrics:
            print(f"  ROC-AUC:    {metrics['roc_auc']:.4f}")

        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        self.confusion_matrices[model_name] = cm

        print(f"\nConfusion Matrix:")
        print(f"                Predicted")
        print(f"              Legit  Fraud")
        print(f"  Actual Legit   {cm[0,0]:4d}   {cm[0,1]:4d}")
        print(f"         Fraud   {cm[1,0]:4d}   {cm[1,1]:4d}")

        # Calculate false positives and false negatives
        fp = cm[0, 1]  # Legitimate classified as fraud
        fn = cm[1, 0]  # Fraud classified as legitimate
        print(f"\nError Analysis:")
        print(f"  False Positives: {fp} (legitimate flagged as fraud)")
        print(f"  False Negatives: {fn} (fraud missed)")

        # Classification report
        print(f"\nDetailed Classification Report:")
        print(classification_report(y_test, y_pred, target_names=['Legitimate', 'Fraud']))

        # Store metrics
        self.metrics[model_name] = metrics

        return metrics

    def _calculate_specificity(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """
        Calculate specificity (true negative rate)

        Args:
            y_true: True labels
            y_pred: Predicted labels

        Returns:
            Specificity score
        """
        cm = confusion_matrix(y_true, y_pred)
        tn = cm[0, 0]
        fp = cm[0, 1]
        return tn / (tn + fp) if (tn + fp) > 0 else 0.0

    def compare_models(self, models_metrics: Dict[str, Dict[str, float]]):
        """
        Compare multiple models side-by-side

        Args:
            models_metrics: Dictionary of {model_name: metrics_dict}
        """
        print(f"\n{'='*60}")
        print("MODEL COMPARISON")
        print(f"{'='*60}\n")

        # Create comparison table
        metrics_to_compare = ['accuracy', 'precision', 'recall', 'f1_score', 'roc_auc']

        print(f"{'Metric':<15}", end='')
        for model_name in models_metrics.keys():
            print(f"{model_name:<15}", end='')
        print()
        print("-" * (15 + 15 * len(models_metrics)))

        for metric in metrics_to_compare:
            print(f"{metric.capitalize():<15}", end='')
            for model_name, metrics in models_metrics.items():
                if metric in metrics:
                    print(f"{metrics[metric]:<15.4f}", end='')
                else:
                    print(f"{'N/A':<15}", end='')
            print()

        # Identify best model for each metric
        print(f"\n{'Best Model by Metric:'}")
        for metric in metrics_to_compare:
            best_model = None
            best_score = -1
            for model_name, metrics in models_metrics.items():
                if metric in metrics and metrics[metric] > best_score:
                    best_score = metrics[metric]
                    best_model = model_name

            if best_model:
                print(f"  {metric.capitalize():<15}: {best_model} ({best_score:.4f})")

    def analyze_feature_importance(self, model, feature_names: list, top_n: int = 15):
        """
        Analyze and display feature importance

        Args:
            model: Trained model with feature_importances_ attribute
            feature_names: List of feature names
            top_n: Number of top features to display
        """
        if not hasattr(model, 'feature_importances_'):
            print("Model does not have feature_importances_ attribute")
            return

        print(f"\n{'='*60}")
        print(f"FEATURE IMPORTANCE ANALYSIS (Top {top_n})")
        print(f"{'='*60}\n")

        # Get feature importances
        importances = model.feature_importances_
        indices = np.argsort(importances)[::-1]

        # Display top features
        print(f"{'Rank':<6}{'Feature':<35}{'Importance':<12}")
        print("-" * 53)

        for i in range(min(top_n, len(feature_names))):
            idx = indices[i]
            print(f"{i+1:<6}{feature_names[idx]:<35}{importances[idx]:<12.4f}")

        # Group analysis
        print(f"\n{'Feature Category Analysis:'}")
        categories = {
            'Amount': ['amount_', 'suspicious_amount'],
            'Date': ['date_'],
            'Fields': ['missing_', 'field_', 'issuer_specific'],
            'Serial': ['serial_'],
            'Names/Address': ['name_', 'address_', 'signature_']
        }

        for category, keywords in categories.items():
            category_importance = sum(
                importances[i] for i, name in enumerate(feature_names)
                if any(kw in name for kw in keywords)
            )
            print(f"  {category:<20}: {category_importance:.4f}")

    def generate_report(self, model_name: str, metrics: Dict[str, float],
                       feature_names: Optional[list] = None,
                       model: Optional[object] = None) -> str:
        """
        Generate comprehensive evaluation report

        Args:
            model_name: Name of the model
            metrics: Dictionary of metrics
            feature_names: List of feature names (optional)
            model: Trained model (optional, for feature importance)

        Returns:
            Report string
        """
        report_lines = []
        report_lines.append("=" * 70)
        report_lines.append(f"FRAUD DETECTION MODEL EVALUATION REPORT - {model_name}")
        report_lines.append("=" * 70)
        report_lines.append("")

        # Performance Metrics
        report_lines.append("PERFORMANCE METRICS:")
        report_lines.append(f"  Accuracy:    {metrics.get('accuracy', 0):.4f} (overall correctness)")
        report_lines.append(f"  Precision:   {metrics.get('precision', 0):.4f} (fraud detection accuracy)")
        report_lines.append(f"  Recall:      {metrics.get('recall', 0):.4f} (fraud catch rate)")
        report_lines.append(f"  F1-Score:    {metrics.get('f1_score', 0):.4f} (balanced measure)")
        report_lines.append(f"  Specificity: {metrics.get('specificity', 0):.4f} (true negative rate)")
        if 'roc_auc' in metrics:
            report_lines.append(f"  ROC-AUC:     {metrics.get('roc_auc', 0):.4f} (discrimination ability)")
        report_lines.append("")

        # Model Quality Assessment
        report_lines.append("MODEL QUALITY ASSESSMENT:")
        accuracy = metrics.get('accuracy', 0)
        precision = metrics.get('precision', 0)
        recall = metrics.get('recall', 0)
        f1 = metrics.get('f1_score', 0)

        if accuracy >= 0.90 and precision >= 0.85 and recall >= 0.90:
            quality = "EXCELLENT ✓"
        elif accuracy >= 0.85 and precision >= 0.80 and recall >= 0.85:
            quality = "GOOD ✓"
        elif accuracy >= 0.80:
            quality = "ACCEPTABLE"
        else:
            quality = "NEEDS IMPROVEMENT"

        report_lines.append(f"  Overall Quality: {quality}")
        report_lines.append("")

        # Confusion Matrix
        if model_name in self.confusion_matrices:
            cm = self.confusion_matrices[model_name]
            report_lines.append("CONFUSION MATRIX:")
            report_lines.append(f"                  Predicted")
            report_lines.append(f"              Legitimate  Fraud")
            report_lines.append(f"  Actual Legit     {cm[0,0]:4d}     {cm[0,1]:4d}")
            report_lines.append(f"         Fraud     {cm[1,0]:4d}     {cm[1,1]:4d}")
            report_lines.append("")

        # Recommendations
        report_lines.append("RECOMMENDATIONS:")
        if recall < 0.85:
            report_lines.append("  ⚠ Low recall - Consider adjusting decision threshold to catch more fraud")
        if precision < 0.80:
            report_lines.append("  ⚠ Low precision - Too many false positives, refine features or model")
        if accuracy >= 0.90 and precision >= 0.85 and recall >= 0.90:
            report_lines.append("  ✓ Model meets all target metrics - Ready for production")

        report_lines.append("")
        report_lines.append("=" * 70)

        return "\n".join(report_lines)

    def evaluate_threshold_impact(self, y_true: np.ndarray, y_proba: np.ndarray,
                                  thresholds: list = [0.3, 0.4, 0.5, 0.6, 0.7]):
        """
        Analyze impact of different decision thresholds

        Args:
            y_true: True labels
            y_proba: Predicted probabilities
            thresholds: List of thresholds to test
        """
        print(f"\n{'='*60}")
        print("THRESHOLD SENSITIVITY ANALYSIS")
        print(f"{'='*60}\n")

        print(f"{'Threshold':<12}{'Accuracy':<12}{'Precision':<12}{'Recall':<12}{'F1-Score':<12}")
        print("-" * 60)

        for threshold in thresholds:
            y_pred = (y_proba >= threshold).astype(int)

            accuracy = accuracy_score(y_true, y_pred)
            precision = precision_score(y_true, y_pred, zero_division=0)
            recall = recall_score(y_true, y_pred, zero_division=0)
            f1 = f1_score(y_true, y_pred, zero_division=0)

            print(f"{threshold:<12.2f}{accuracy:<12.4f}{precision:<12.4f}{recall:<12.4f}{f1:<12.4f}")

        print(f"\nRecommendation:")
        print(f"  • Lower threshold (0.3-0.4): Higher recall, catches more fraud but more false positives")
        print(f"  • Higher threshold (0.6-0.7): Higher precision, fewer false alarms but might miss fraud")
        print(f"  • Default (0.5): Balanced approach")


# Convenience function
def evaluate_models(models_dict: Dict, X_test: np.ndarray, y_test: np.ndarray,
                   feature_names: Optional[list] = None):
    """
    Evaluate multiple models

    Args:
        models_dict: Dictionary of {model_name: model_object}
        X_test: Test feature matrix
        y_test: Test labels
        feature_names: List of feature names (optional)
    """
    evaluator = ModelEvaluator()

    # Evaluate each model
    all_metrics = {}
    for model_name, model in models_dict.items():
        metrics = evaluator.evaluate_model(model, X_test, y_test, model_name)
        all_metrics[model_name] = metrics

        # Feature importance if available
        if feature_names and hasattr(model, 'feature_importances_'):
            evaluator.analyze_feature_importance(model, feature_names)

    # Compare models
    if len(all_metrics) > 1:
        evaluator.compare_models(all_metrics)

    # Generate reports
    print(f"\n{'='*70}")
    print("EVALUATION REPORTS")
    print(f"{'='*70}\n")

    for model_name, metrics in all_metrics.items():
        report = evaluator.generate_report(
            model_name, metrics, feature_names,
            models_dict.get(model_name)
        )
        print(report)
        print()

    return evaluator
