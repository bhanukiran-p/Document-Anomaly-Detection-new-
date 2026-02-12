# Profanity Filtering Implementation

**Date:** December 2024  
**Status:** ✅ **IMPLEMENTED**

---

## ✅ What Was Added

### **Profanity Filtering Library**

**Library:** `better-profanity` (v0.7.0)

**Purpose:** Filter inappropriate language and profanity from LLM inputs

**Installation:**
```bash
pip install better-profanity==0.7.0
```

---

## 🔧 Implementation Details

### **1. Updated `InputGuard` Class**

**Location:** `Backend/real_time/guardrails.py`

**New Features:**

#### **Profanity Detection**
```python
# Check if text contains profanity (without censoring)
has_profanity = InputGuard.contains_profanity("inappropriate text")
# Returns: True/False
```

#### **Profanity Censoring**
```python
# Censor profanity automatically
clean_text = InputGuard.sanitize("inappropriate text", filter_profanity=True)
# Returns: "**** text" (censored)
```

#### **Automatic in Dictionary Sanitization**
```python
# Profanity filtering included in sanitize_dict
sanitized = InputGuard.sanitize_dict({
    'description': 'inappropriate content here'
}, filter_profanity=True)
# Profanity automatically censored
```

---

## 🛡️ How It Works

### **Step-by-Step Flow:**

```
1. Text input received
   ↓
2. Check if better-profanity is available
   ├─ If available: Initialize profanity filter
   └─ If not available: Skip profanity filtering (graceful fallback)
   ↓
3. Apply profanity filtering (if enabled)
   ├─ Detect profanity: contains_profanity()
   └─ Censor profanity: censor()
   ↓
4. Apply PII redaction (email, phone, SSN, credit card)
   ↓
5. Return sanitized text
```

---

## 📍 Integration Points

### **Already Integrated:**

All existing guardrail calls automatically include profanity filtering:

1. ✅ **Check Extractor** (`check/check_extractor.py`)
   ```python
   sanitized_data = InputGuard.sanitize_dict(data, filter_profanity=True)
   ```

2. ✅ **Check AI Agent** (`check/ai/check_fraud_analysis_agent.py`)
   ```python
   sanitized_extracted_data = InputGuard.sanitize_dict(extracted_data, filter_profanity=True)
   sanitized_customer_info = InputGuard.sanitize_dict(customer_info, filter_profanity=True)
   full_prompt = InputGuard.sanitize(full_prompt, filter_profanity=True)
   ```

3. ✅ **Money Order AI Agent** (`money_order/ai/fraud_analysis_agent.py`)
   ```python
   sanitized_extracted_data = InputGuard.sanitize_dict(extracted_data, filter_profanity=True)
   raw_ocr_text = InputGuard.sanitize(raw_text, filter_profanity=True)
   ```

---

## 🔍 Features

### **1. Graceful Fallback**

If `better-profanity` is not installed:
- ✅ Other guardrails continue to work
- ✅ No errors thrown
- ⚠️ Warning logged: "better-profanity not available. Profanity filtering disabled."

### **2. Automatic Initialization**

Profanity filter initializes automatically on first use:
```python
# First call initializes the filter
InputGuard.sanitize("test", filter_profanity=True)
# Subsequent calls use cached initialization
```

### **3. Configurable**

Can disable profanity filtering per call:
```python
# With profanity filtering
clean = InputGuard.sanitize(text, filter_profanity=True)

# Without profanity filtering (PII redaction still works)
clean = InputGuard.sanitize(text, filter_profanity=False)
```

---

## 📊 Example Usage

### **Before Profanity Filtering:**

```python
# ❌ Inappropriate content sent to LLM
text = "This document contains inappropriate language"
prompt = f"Analyze: {text}"
llm.invoke(prompt)  # Inappropriate content exposed
```

### **After Profanity Filtering:**

```python
# ✅ Inappropriate content filtered
from real_time.guardrails import InputGuard

text = "This document contains inappropriate language"
clean_text = InputGuard.sanitize(text, filter_profanity=True)
# Result: "This document contains **** language"

prompt = f"Analyze: {clean_text}"
llm.invoke(prompt)  # Safe!
```

---

## 🧪 Testing

### **Test Profanity Filtering:**

```bash
cd Backend
python -m utils.test_guardrails_integration
```

**Expected Output:**
```
✅ Profanity filtering working (if better-profanity installed)
   - Inappropriate content automatically censored
   - Can detect profanity without censoring
```

### **Manual Test:**

```python
from real_time.guardrails import InputGuard

# Test detection
has_profanity = InputGuard.contains_profanity("test text")
print(f"Contains profanity: {has_profanity}")

# Test censoring
clean = InputGuard.sanitize("test text", filter_profanity=True)
print(f"Censored: {clean}")
```

---

## 📦 Dependencies

### **Added to `requirements.txt`:**

```
better-profanity==0.7.0  # Profanity filtering and content moderation
```

### **Installation:**

```bash
pip install -r requirements.txt
# or
pip install better-profanity==0.7.0
```

---

## 🔒 Security Benefits

### **What It Protects Against:**

1. ✅ **Inappropriate Content** - Profanity automatically censored
2. ✅ **Offensive Language** - Filtered before reaching LLM
3. ✅ **Content Moderation** - Ensures professional outputs
4. ✅ **Compliance** - Helps meet content standards

---

## 📝 Summary

### **Profanity Filtering: ✅ IMPLEMENTED**

**What's Added:**
- ✅ `better-profanity` library integration
- ✅ Automatic profanity detection
- ✅ Automatic profanity censoring
- ✅ Graceful fallback if library not installed
- ✅ Integrated into all existing guardrail calls

**Where Applied:**
- ✅ Check analysis
- ✅ Check AI agent
- ✅ Money Order AI agent
- ✅ All dictionary sanitization

**Protection Level:**
- ✅ **Automatic** - No manual intervention needed
- ✅ **Configurable** - Can enable/disable per call
- ✅ **Safe** - Graceful fallback if library unavailable

---

## 🎯 Next Steps

### **To Enable Profanity Filtering:**

1. **Install the library:**
   ```bash
   pip install better-profanity==0.7.0
   ```

2. **Verify it's working:**
   ```bash
   cd Backend
   python -m utils.test_guardrails_integration
   ```

3. **Check logs:**
   Look for: `"Profanity filter initialized successfully"`

### **To Disable Profanity Filtering:**

Simply don't install `better-profanity`. The system will automatically skip profanity filtering and continue with other guardrails.

---

**Last Updated:** December 2024

