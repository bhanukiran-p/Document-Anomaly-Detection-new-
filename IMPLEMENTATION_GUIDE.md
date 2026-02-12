# Automated Model Retraining - Implementation Guide

## Overview
This guide provides step-by-step instructions to complete the automated model retraining system for on-demand documents.

## ✅ COMPLETED COMPONENTS

### 1. Configuration System
- **File**: `Backend/training/retraining_config.json`
- **Status**: ✅ Complete
- **Purpose**: Centralized configuration for all retraining parameters

### 2. Performance Tracking
- **File**: `Backend/training/model_performance_tracker.py`
- **Status**: ✅ Complete
- **Features**: Version management, rollback decisions, performance history

### 3. Core Retraining Logic
- **File**: `Backend/training/automated_retraining.py`
- **Status**: ✅ Base class complete
- **Features**: Data blending, ensemble training, versioned model saving

### 4. Dependencies & Configuration
- **Files**: `Backend/requirements.txt`, `Backend/config.py`
- **Status**: ✅ Complete
- **Added**: APScheduler 3.10.4, feature flags

---

## 🔄 REMAINING IMPLEMENTATION STEPS

### STEP 1: Add Document-Specific Retrainer Subclasses

**File to Edit**: `Backend/training/automated_retraining.py`

**What to Add**: Append the following 4 subclasses at the end of the file (after line 489):

<details>
<summary>PaystubModelRetrainer (Click to expand)</summary>

```python
class PaystubModelRetrainer(DocumentModelRetrainer):
    """Paystub-specific model retrainer"""

    def __init__(self):
        super().__init__('paystub')

    def generate_synthetic_data(self, n_samples: int) -> pd.DataFrame:
        """Generate synthetic paystub data - reuse logic from train_paystub_models.py"""
        import random

        data = []
        for i in range(n_samples):
            # Simplified version - for full implementation, copy from train_paystub_models.py lines 36-254
            # Generate features based on risk distribution
            category_rand = random.random()
            if category_rand < 0.4:
                target_min, target_max = 0, 30
                has_company = random.random() > 0.05
                has_employee = random.random() > 0.03
                gross = random.uniform(1000, 10000)
                net = random.uniform(500, gross * 0.9)
                # ... (see train_paystub_models.py for full logic)
            # ... rest of feature generation

            features = [
                1 if has_company else 0, 1 if has_employee else 0,
                # ... 18 features total
            ]
            data.append(features)

        feature_names = [
            'has_company', 'has_employee', 'has_gross', 'has_net', 'has_date',
            'gross_pay', 'net_pay', 'tax_error', 'text_quality', 'missing_fields_count',
            'has_federal_tax', 'has_state_tax', 'has_social_security', 'has_medicare',
            'total_tax_amount', 'tax_to_gross_ratio', 'net_to_gross_ratio',
            'deduction_percentage', 'risk_score'
        ]

        return pd.DataFrame(data, columns=feature_names)

    def fetch_real_data_from_database(self) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """Fetch real paystub data from Supabase with confidence filtering"""
        if not SUPABASE_AVAILABLE:
            return None, "Supabase client not available"

        try:
            supabase = get_supabase_client()

            # Load data quality config
            data_quality = self.config.get('data_quality', {})
            min_confidence = data_quality.get('min_confidence_score', 0.80)
            require_high_conf = data_quality.get('require_high_confidence_only', True)

            # Build query with confidence filtering
            query = supabase.table('paystubs').select('*')

            # Filter by recommendation type (exclude ESCALATE)
            query = query.in_('ai_recommendation', ['APPROVE', 'REJECT'])

            # Apply confidence filter if enabled
            if require_high_conf:
                confidence_field = data_quality.get('confidence_score_field', 'confidence_score')
                query = query.gte(confidence_field, min_confidence)
                logger.info(f"Applying confidence filter: {confidence_field} >= {min_confidence}")

            # Execute query
            response = query.order('created_at', desc=True).limit(10000).execute()

            if not response.data:
                return None, f"No high-confidence paystubs found (min_confidence={min_confidence})"

            # Convert to DataFrame
            df = pd.DataFrame(response.data)

            logger.info(f"Fetched {len(df)} high-confidence paystubs from database")
            logger.info(f"  APPROVE: {len(df[df['ai_recommendation']=='APPROVE'])}")
            logger.info(f"  REJECT: {len(df[df['ai_recommendation']=='REJECT'])}")

            if 'confidence_score' in df.columns:
                logger.info(f"  Avg confidence: {df['confidence_score'].mean():.3f}")

            # Map to risk scores for training
            df['risk_score'] = df['ai_recommendation'].map({
                'APPROVE': 15.0,  # Low risk (0-30 range)
                'REJECT': 85.0    # High risk (70-100 range)
            })

            # Extract features (simplified - needs full implementation)
            # For production, use actual PaystubFeatureExtractor
            # feature_extractor = PaystubFeatureExtractor()
            # features_df = feature_extractor.extract(df)

            return df, None

        except Exception as e:
            logger.error(f"Error fetching paystubs: {e}")
            return None, str(e)
```
</details>

**NOTE**: The other 3 subclasses (CheckModelRetrainer, MoneyOrderModelRetrainer, BankStatementModelRetrainer) follow the same pattern. Copy the structure above and adjust:
- Change class name and `super().__init__('check')` etc.
- Update `generate_synthetic_data()` to match the respective training script
- Update `fetch_real_data_from_database()` to query the correct table

**Shortcut**: For faster implementation, you can create minimal subclasses that just call the existing training scripts for synthetic data generation.

---

### STEP 2: Create Scheduler Module

**New File**: `Backend/scheduler/document_retraining_scheduler.py`

```python
"""
APScheduler-based Model Retraining Scheduler
Handles weekly scheduled retraining + on-demand API triggers
"""

import logging
import threading
from typing import Dict, Any, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: Optional[BackgroundScheduler] = None
_scheduler_lock = threading.Lock()


def get_scheduler() -> BackgroundScheduler:
    """Get or create the global scheduler instance"""
    global _scheduler

    with _scheduler_lock:
        if _scheduler is None:
            _scheduler = BackgroundScheduler(daemon=True)
        return _scheduler


def retrain_all_documents():
    """
    Scheduled job to retrain all enabled document types
    Runs weekly on Sunday at 2 AM
    """
    from training.retraining_config import load_config
    from training.automated_retraining import (
        PaystubModelRetrainer,
        CheckModelRetrainer,
        MoneyOrderModelRetrainer,
        BankStatementModelRetrainer
    )

    logger.info("="*70)
    logger.info("Starting scheduled model retraining for all document types")
    logger.info("="*70)

    config = load_config()
    doc_types = config['document_types']

    retrainer_classes = {
        'paystub': PaystubModelRetrainer,
        'check': CheckModelRetrainer,
        'money_order': MoneyOrderModelRetrainer,
        'bank_statement': BankStatementModelRetrainer
    }

    results = {}

    for doc_type, doc_config in doc_types.items():
        if not doc_config.get('enabled', True):
            logger.info(f"Skipping {doc_type} - disabled in config")
            continue

        logger.info(f"\n--- Retraining {doc_type} models ---")

        try:
            retrainer_class = retrainer_classes.get(doc_type)
            if retrainer_class is None:
                logger.error(f"No retrainer class found for {doc_type}")
                results[doc_type] = {'success': False, 'error': 'No retrainer class'}
                continue

            retrainer = retrainer_class()
            result = retrainer.retrain()
            results[doc_type] = result

            if result['success']:
                if result.get('activated'):
                    logger.info(f"✅ {doc_type} - Success (version {result['version_id']} activated)")
                else:
                    logger.warning(f"⚠️  {doc_type} - Trained but not activated ({result.get('reason')})")
            else:
                logger.error(f"❌ {doc_type} - Failed: {result.get('error')}")

        except Exception as e:
            logger.error(f"❌ {doc_type} - Exception: {e}", exc_info=True)
            results[doc_type] = {'success': False, 'error': str(e)}

    logger.info("\n" + "="*70)
    logger.info("Scheduled retraining completed")
    logger.info(f"Summary: {sum(1 for r in results.values() if r.get('success'))} / {len(results)} successful")
    logger.info("="*70 + "\n")

    return results


def trigger_manual_retraining(doc_type: str) -> Dict[str, Any]:
    """
    Trigger manual retraining for a specific document type

    Args:
        doc_type: Document type (paystub, check, money_order, bank_statement)

    Returns:
        Retraining result dictionary
    """
    from training.automated_retraining import (
        PaystubModelRetrainer,
        CheckModelRetrainer,
        MoneyOrderModelRetrainer,
        BankStatementModelRetrainer
    )

    logger.info(f"Manual retraining triggered for {doc_type}")

    retrainer_classes = {
        'paystub': PaystubModelRetrainer,
        'check': CheckModelRetrainer,
        'money_order': MoneyOrderModelRetrainer,
        'bank_statement': BankStatementModelRetrainer
    }

    retrainer_class = retrainer_classes.get(doc_type)
    if retrainer_class is None:
        return {
            'success': False,
            'error': f'Invalid document type: {doc_type}'
        }

    try:
        retrainer = retrainer_class()
        result = retrainer.retrain()
        return result
    except Exception as e:
        logger.error(f"Manual retraining failed for {doc_type}: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def start_scheduler():
    """
    Initialize and start the scheduler with weekly retraining job
    Call this once at application startup
    """
    try:
        from config import Config

        if not Config.ENABLE_AUTOMATED_RETRAINING:
            logger.info("Automated retraining is disabled (ENABLE_AUTOMATED_RETRAINING=false)")
            return

        # Load configuration
        import json
        with open(Config.RETRAINING_CONFIG_PATH, 'r') as f:
            config = json.load(f)

        global_settings = config['global_settings']

        if not global_settings.get('scheduled_retraining_enabled', True):
            logger.info("Scheduled retraining disabled in config")
            return

        scheduler = get_scheduler()

        # Schedule weekly retraining job
        day_of_week = global_settings.get('schedule_day_of_week', 'sun')
        hour = global_settings.get('schedule_hour', 2)
        minute = global_settings.get('schedule_minute', 0)

        scheduler.add_job(
            retrain_all_documents,
            CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute),
            id='weekly_document_retraining',
            name='Weekly Document Model Retraining',
            replace_existing=True
        )

        scheduler.start()

        logger.info("="*70)
        logger.info("📅 Automated retraining scheduler started")
        logger.info(f"Schedule: Every {day_of_week.upper()} at {hour:02d}:{minute:02d}")
        logger.info("="*70)

    except Exception as e:
        logger.error(f"Failed to start retraining scheduler: {e}", exc_info=True)


def stop_scheduler():
    """Stop the scheduler gracefully"""
    global _scheduler

    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        logger.info("Retraining scheduler stopped")


def get_scheduler_status() -> Dict[str, Any]:
    """Get current scheduler status and next run times"""
    scheduler = get_scheduler()

    if not scheduler.running:
        return {'running': False}

    jobs = scheduler.get_jobs()

    return {
        'running': True,
        'jobs': [
            {
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None
            }
            for job in jobs
        ]
    }
```

---

### STEP 3: Add Model Versioning to Fraud Detectors

**Files to Modify**:
1. `Backend/paystub/ml/paystub_fraud_detector.py`
2. `Backend/check/ml/check_fraud_detector.py`
3. `Backend/money_order/ml/money_order_fraud_detector.py`
4. `Backend/bank_statement/ml/bank_statement_fraud_detector.py`

**Changes to Make in Each File**:

Add these two methods to each fraud detector class:

```python
def _get_active_version_path(self, model_type: str) -> str:
    """
    Get path to currently active model version

    Args:
        model_type: Type of model (random_forest, xgboost, feature_scaler)

    Returns:
        Full path to active model file
    """
    models_dir = os.path.join(os.path.dirname(__file__), 'models')
    active_version_file = os.path.join(models_dir, 'ACTIVE_VERSION.txt')

    if os.path.exists(active_version_file):
        with open(active_version_file, 'r') as f:
            version_id = f.read().strip()

        # Versioned filename: paystub_random_forest_20250122_143052.pkl
        filename = f'{self.document_type}_{model_type}_{version_id}.pkl'
        logger.info(f"Using versioned model: {filename}")
    else:
        # Fallback to non-versioned (backward compatibility)
        filename = f'{self.document_type}_{model_type}.pkl'
        logger.info(f"ACTIVE_VERSION.txt not found, using non-versioned: {filename}")

    return os.path.join(models_dir, filename)

def reload_models(self):
    """
    Reload models from disk (hot-swap without restart)
    Call this after retraining to activate new model version
    """
    logger.info(f"Reloading {self.document_type} models...")
    self._load_models()
    logger.info(f"{self.document_type} models reloaded successfully")
```

Then modify the `_load_models()` method to use versioned paths:

**Before**:
```python
self.rf_model_path = os.path.join(self.models_dir, 'paystub_random_forest.pkl')
self.xgb_model_path = os.path.join(self.models_dir, 'paystub_xgboost.pkl')
self.scaler_path = os.path.join(self.models_dir, 'paystub_feature_scaler.pkl')
```

**After**:
```python
self.rf_model_path = self._get_active_version_path('random_forest')
self.xgb_model_path = self._get_active_version_path('xgboost')
self.scaler_path = self._get_active_version_path('feature_scaler')
```

---

### STEP 4: Update API Server

**File to Modify**: `Backend/api_server.py`

**Part A: Initialize Scheduler** (add after line 100, after Supabase client initialization)

```python
# Initialize automated retraining scheduler
try:
    from scheduler.document_retraining_scheduler import start_scheduler
    start_scheduler()
except Exception as e:
    logger.error(f"Failed to start retraining scheduler: {e}")
```

**Part B: Add Retraining API Endpoints** (add around line 1725, after existing endpoints)

```python
# ==================== AUTOMATED RETRAINING ENDPOINTS ====================

@app.route('/api/paystubs/retrain-model', methods=['POST'])
def retrain_paystub_model():
    """Trigger manual paystub model retraining (non-blocking)"""
    from scheduler.document_retraining_scheduler import trigger_manual_retraining

    def train_in_background():
        try:
            result = trigger_manual_retraining('paystub')
            logger.info(f"Paystub retraining result: {result}")
        except Exception as e:
            logger.error(f"Paystub retraining error: {e}", exc_info=True)

    thread = threading.Thread(target=train_in_background, daemon=True)
    thread.start()

    return jsonify({
        'success': True,
        'message': 'Paystub model retraining started in background',
        'status': 'processing'
    }), 202


@app.route('/api/checks/retrain-model', methods=['POST'])
def retrain_check_model():
    """Trigger manual check model retraining (non-blocking)"""
    from scheduler.document_retraining_scheduler import trigger_manual_retraining

    def train_in_background():
        try:
            result = trigger_manual_retraining('check')
            logger.info(f"Check retraining result: {result}")
        except Exception as e:
            logger.error(f"Check retraining error: {e}", exc_info=True)

    thread = threading.Thread(target=train_in_background, daemon=True)
    thread.start()

    return jsonify({
        'success': True,
        'message': 'Check model retraining started in background',
        'status': 'processing'
    }), 202


@app.route('/api/money-orders/retrain-model', methods=['POST'])
def retrain_money_order_model():
    """Trigger manual money order model retraining (non-blocking)"""
    from scheduler.document_retraining_scheduler import trigger_manual_retraining

    def train_in_background():
        try:
            result = trigger_manual_retraining('money_order')
            logger.info(f"Money order retraining result: {result}")
        except Exception as e:
            logger.error(f"Money order retraining error: {e}", exc_info=True)

    thread = threading.Thread(target=train_in_background, daemon=True)
    thread.start()

    return jsonify({
        'success': True,
        'message': 'Money order model retraining started in background',
        'status': 'processing'
    }), 202


@app.route('/api/bank-statements/retrain-model', methods=['POST'])
def retrain_bank_statement_model():
    """Trigger manual bank statement model retraining (non-blocking)"""
    from scheduler.document_retraining_scheduler import trigger_manual_retraining

    def train_in_background():
        try:
            result = trigger_manual_retraining('bank_statement')
            logger.info(f"Bank statement retraining result: {result}")
        except Exception as e:
            logger.error(f"Bank statement retraining error: {e}", exc_info=True)

    thread = threading.Thread(target=train_in_background, daemon=True)
    thread.start()

    return jsonify({
        'success': True,
        'message': 'Bank statement model retraining started in background',
        'status': 'processing'
    }), 202


@app.route('/api/retraining/status', methods=['GET'])
def get_retraining_status():
    """Get scheduler status and performance history for all document types"""
    from scheduler.document_retraining_scheduler import get_scheduler_status
    from training.model_performance_tracker import ModelPerformanceTracker

    try:
        scheduler_status = get_scheduler_status()

        # Get performance summaries for all doc types
        performance_summaries = {}
        for doc_type in ['paystub', 'check', 'money_order', 'bank_statement']:
            try:
                tracker = ModelPerformanceTracker(doc_type)
                performance_summaries[doc_type] = tracker.get_performance_summary()
            except Exception as e:
                logger.error(f"Error getting {doc_type} performance: {e}")
                performance_summaries[doc_type] = {'error': str(e)}

        return jsonify({
            'success': True,
            'scheduler': scheduler_status,
            'performance_history': performance_summaries
        }), 200

    except Exception as e:
        logger.error(f"Error getting retraining status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

**Part C: Add Scheduler Shutdown Hook** (add before `if __name__ == '__main__':`)

```python
# Graceful shutdown hook for scheduler
import atexit
@atexit.register
def shutdown_scheduler():
    try:
        from scheduler.document_retraining_scheduler import stop_scheduler
        stop_scheduler()
    except:
        pass
```

---

## 🧪 TESTING THE IMPLEMENTATION

### Manual Testing Steps:

1. **Start the Flask server**:
   ```bash
   cd Backend
   python api_server.py
   ```

2. **Check scheduler started**:
   Look for log message: "📅 Automated retraining scheduler started"

3. **Trigger manual retraining** (test with paystub first):
   ```bash
   curl -X POST http://localhost:5001/api/paystubs/retrain-model
   ```
   Should return: `{"success": true, "status": "processing"}`

4. **Check retraining status**:
   ```bash
   curl http://localhost:5001/api/retraining/status
   ```

5. **Verify versioned models created**:
   ```bash
   ls -la Backend/paystub/ml/models/
   # Should see files like: paystub_random_forest_20250122_143052.pkl
   ```

6. **Check ACTIVE_VERSION.txt**:
   ```bash
   cat Backend/paystub/ml/models/ACTIVE_VERSION.txt
   # Should contain timestamp like: 20250122_143052
   ```

7. **Verify performance history**:
   ```bash
   cat Backend/paystub/ml/models/performance_history.json
   # Should contain metrics for the retraining run
   ```

---

## 🚀 DEPLOYMENT CHECKLIST

Before deploying to production:

- [ ] Install APScheduler: `pip install apscheduler==3.10.4`
- [ ] Set environment variable: `ENABLE_AUTOMATED_RETRAINING=true`
- [ ] Verify retraining config file exists and is valid JSON
- [ ] Test manual retraining for each document type
- [ ] Verify scheduler shows next run time in status endpoint
- [ ] Check logs for any errors during scheduler startup
- [ ] Ensure Supabase database has sufficient data for real data mode
- [ ] Test rollback mechanism with intentionally bad model
- [ ] Monitor first scheduled retraining run (Sunday 2 AM)

---

## 📊 MONITORING & MAINTENANCE

### Key Log Messages to Monitor:

- ✅ `"Automated retraining scheduler started"` - Scheduler initialized
- ✅ `"Starting scheduled model retraining"` - Weekly job triggered
- ✅ `"✅ Retraining completed successfully"` - Retraining succeeded
- ⚠️  `"New model not activated due to performance drop"` - Rollback triggered
- ❌ `"Data validation failed"` - Insufficient/poor quality data

### Performance Metrics to Track:

- R² score trend over time
- Data source evolution (synthetic → hybrid → real)
- Training time per document type
- Rollback frequency
- Active version changes

### API Endpoints Summary:

```
POST /api/paystubs/retrain-model          - Manual paystub retraining
POST /api/checks/retrain-model            - Manual check retraining
POST /api/money-orders/retrain-model      - Manual money order retraining
POST /api/bank-statements/retrain-model   - Manual bank statement retraining
GET  /api/retraining/status               - Scheduler + performance status
```

---

## 🔧 TROUBLESHOOTING

### Issue: Scheduler not starting
**Solution**: Check `ENABLE_AUTOMATED_RETRAINING` is `true` in config

### Issue: Models not loading after retraining
**Solution**:
1. Check ACTIVE_VERSION.txt exists and contains valid timestamp
2. Verify versioned model files exist
3. Call fraud detector's `reload_models()` method

### Issue: Retraining fails with "Insufficient samples"
**Solution**: Lower `min_samples_for_training` in retraining_config.json or wait for more data

### Issue: All models use synthetic data
**Solution**: Normal if database has < 100 documents. Add more analyzed documents or lower `min_real_samples_for_hybrid`

---

## 📝 NOTES

- First retraining will create initial ACTIVE_VERSION.txt
- Models are backward compatible - will fall back to non-versioned files if ACTIVE_VERSION.txt missing
- Scheduler runs in background thread - non-blocking
- Old model versions automatically cleaned up (keeps last 5)
- Performance comparison prevents bad models from being activated
- Real-time transaction retraining continues to work independently

---

**Implementation Completion**: Follow Steps 1-4 above to finish the system.
**Estimated Time**: 2-4 hours (depending on thoroughness of subclass implementation)
