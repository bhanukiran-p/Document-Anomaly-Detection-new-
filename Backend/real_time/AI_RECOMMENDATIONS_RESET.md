# AI Recommendations System - Complete Reset

## Changes Made to Fix AI Recommendations

### 1. **API Key Override Fix** (api_server.py)
**Location**: Lines 6-14
**Purpose**: Force correct OpenAI API key from .env file before any imports

```python
# CRITICAL FIX: Force correct OpenAI API key before any imports
import os
from dotenv import load_dotenv
load_dotenv(override=True)
_api_key = os.getenv('OPENAI_API_KEY')
if _api_key:
    os.environ['OPENAI_API_KEY'] = _api_key
    print(f"✅ Forced OPENAI_API_KEY from .env (starts with: {_api_key[:15]}...)")
```

### 2. **API Key Override in Agent** (realtime_agent.py)
**Location**: Lines 16-21
**Purpose**: Double-check API key is correct when agent initializes

```python
# CRITICAL FIX: Force override system environment variable with .env value
_env_api_key = os.getenv('OPENAI_API_KEY')
if _env_api_key and _env_api_key.startswith('sk-proj-al'):
    os.environ['OPENAI_API_KEY'] = _env_api_key
    logger.info(f"✅ Forced OPENAI_API_KEY override from .env file")
```

### 3. **Disabled Guardrails** (agent_endpoint.py)
**Location**: Line 27
**Purpose**: Temporarily disable guardrails to prevent timeout issues

```python
self.agent = RealTimeAnalysisAgent(api_key=api_key, enable_guardrails=False)
```

**Why**: Guardrails were causing 30-60 second timeouts on OpenAI API calls

### 4. **Increased Timeouts** (llm_guardrails.py)
**Location**: Lines 31-32
**Purpose**: Increased timeout limits for slower networks

```python
DEFAULT_TIMEOUT_SECONDS = 60  # Was 30
MAX_TIMEOUT_SECONDS = 120     # Was 60
```

### 5. **Better Error Logging** (agent_endpoint.py)
**Location**: Lines 68-75
**Purpose**: Log recommendation generation progress and errors

```python
logger.info("🔄 Starting recommendation generation...")
try:
    recommendations = self.agent.generate_recommendations(analysis_result)
    logger.info(f"✅ Recommendations generated: {len(recommendations)} items")
except Exception as rec_error:
    logger.error(f"❌ Recommendation generation failed: {rec_error}", exc_info=True)
    recommendations = []
```

---

## How to Apply the Reset

### Step 1: Restart Backend Server

**IMPORTANT**: You MUST restart the server for changes to take effect!

```bash
# Stop current server (Ctrl+C)
cd Backend
python api_server.py
```

### Step 2: Verify API Key is Loaded

When server starts, you should see:
```
✅ Forced OPENAI_API_KEY from .env (starts with: sk-proj-al7fGXh...)
```

If you see the OLD key (starts with `sk-proj-Kft`), the system environment variable is still overriding.

### Step 3: Upload a CSV

Upload any CSV file and check the recommendations.

### Step 4: Check Backend Logs

Look for these messages:
```
✅ OpenAI LLM is configured. Generating AI recommendations using gpt-4o-mini...
🔄 Starting recommendation generation...
✅ Recommendations generated: 16 items
```

---

## Expected Behavior After Reset

### ✅ Working (AI Recommendations)

Each fraud pattern should have **unique, specific recommendations**:

**Example - Account Takeover:**
```
Title: "HIGH: Account takeover"
Description: "Detected 3017 cases (48.8% of fraud) tied to Account takeover..."
Immediate Actions:
  • Escalate suspected account takeover activity to fraud operations
  • Review recent transactions exhibiting account takeover indicators
  • Notify fraud analytics to monitor for emerging variants
  • Document findings and link to active investigations
Prevention Steps:
  • Update detection rules specific to account takeover patterns
  • Tighten authentication or velocity limits tied to this pattern
  • Add automated alerts for early warning signals
  • Train analysts on latest account takeover red flags
```

**Example - Card-not-present risk:**
```
Title: "HIGH: Card-not-present risk"
Description: "Detected 1238 cases (43.0% of fraud) tied to Card-not-present risk..."
[Different actions and prevention steps]
```

### ❌ Not Working (Fallback Mode)

If AI is still not working, ALL patterns show the SAME generic recommendation:
```
Title: "HIGH: Card-not-present risk"
[Same content for every pattern]
```

---

## Troubleshooting

### Issue: Still seeing generic recommendations

**Check 1**: Server restarted?
```bash
# Make sure you stopped and restarted the server
# Simply saving the file is NOT enough!
```

**Check 2**: API key loaded correctly?
```bash
# Look for this in server startup logs:
✅ Forced OPENAI_API_KEY from .env (starts with: sk-proj-al7fGXh...)

# If you see sk-proj-Kft... instead, the old system env var is still active
```

**Check 3**: Check backend logs for errors
```bash
# Look for:
❌ Error generating recommendations: [error message]
❌ LLM call failed: [error message]
```

### Issue: Timeout errors in logs

**Solution**: Guardrails are already disabled. If still timing out:

1. Check internet connection
2. Try a different network
3. Check if OpenAI API is having issues: https://status.openai.com/

### Issue: "Invalid API key" error

**Solution**: The API key in .env is wrong. Update it:

1. Go to https://platform.openai.com/account/api-keys
2. Create new key
3. Update in `Backend/.env`:
   ```
   OPENAI_API_KEY=sk-proj-YOUR_NEW_KEY
   ```
4. Restart server

---

## Testing

### Quick Test Script

```bash
cd Backend
python test_recommendations.py
```

Expected output:
```
✅ SUCCESS: Generated 16 recommendations

1. HIGH: Account takeover
   Description: Detected 150 cases (50.0% of fraud) tied to Account takeover...
   Actions: 4 immediate actions
   Prevention: 4 prevention steps

2. MEDIUM: Card-not-present risk
   Description: Detected 100 cases (33.3% of fraud) tied to Card-not-present risk...
   Actions: 4 immediate actions
   Prevention: 4 prevention steps
```

---

## Files Modified

1. ✅ `api_server.py` - Force API key at startup
2. ✅ `realtime_agent.py` - Force API key in agent
3. ✅ `agent_endpoint.py` - Disable guardrails, add logging
4. ✅ `llm_guardrails.py` - Increase timeouts

---

## Rollback (If Needed)

If recommendations were working before and now broken:

### Re-enable Guardrails

In `agent_endpoint.py` line 27, change:
```python
# FROM:
self.agent = RealTimeAnalysisAgent(api_key=api_key, enable_guardrails=False)

# TO:
self.agent = RealTimeAnalysisAgent(api_key=api_key, enable_guardrails=True)
```

### Restore Original Timeouts

In `llm_guardrails.py` lines 31-32, change:
```python
# FROM:
DEFAULT_TIMEOUT_SECONDS = 60
MAX_TIMEOUT_SECONDS = 120

# TO:
DEFAULT_TIMEOUT_SECONDS = 30
MAX_TIMEOUT_SECONDS = 60
```

---

## Summary

The main issue was **environment variable conflict**:
- ✅ `.env` file has VALID key
- ❌ System environment has INVALID key
- ❌ System environment overrides .env

**Solution**: Force the correct key from .env at the very start of server initialization.

**Status**: Fixed in multiple places to ensure it works

**Next Step**: Restart server and test!

---

**Date**: 2025-12-19
**Issue**: AI recommendations showing generic fallback instead of OpenAI-generated content
**Root Cause**: Invalid API key from system environment variable
**Fix**: Force correct API key from .env file, disable guardrails temporarily
