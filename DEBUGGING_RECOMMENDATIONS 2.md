# Debugging Recommendation Matching

## Current Issue
Only 2 out of ~5 fraud patterns are showing recommendations when hovered:
- ✅ **Working**: Account takeover, Unusual amount
- ❌ **Not Working**: Velocity abuse, Transaction burst, Card-not-present risk, Night-time activity

## Diagnosis Steps

### Step 1: Check Backend Logs

When you run a real-time analysis, look for these log lines:

```
Requesting X recommendations for fraud types
Fraud types list:
1. Account takeover
   - Cases: XXX (XX.X% of all fraud)
   - Total Amount: $XXX.XX
   - Average Amount: $XXX.XX

2. Velocity abuse
   ...

AI generated X recommendations (expected Y)
```

**What to check:**
- How many fraud types are detected? (e.g., 5 types)
- How many recommendations did AI generate? (should match fraud type count)
- What are the EXACT fraud type names in the list?

### Step 2: Check Browser Console

Open browser console (F12) and look for:

```
=== FRAUD PATTERN MATCHING DEBUG ===
Frontend Fraud Patterns: ["Account takeover", "Velocity abuse", "Transaction burst", ...]
AI Recommendation Titles: ["CRITICAL: Account Takeover", "HIGH: Velocity Abuse", ...]
===================================
```

**What to check:**
- Do the frontend pattern names match the backend fraud type names?
- Do the AI recommendation titles include the fraud type names?

### Step 3: Check Matching Attempts

When you hover over a pattern, you should see:

```
Matching "Velocity abuse" against "HIGH: Velocity Abuse"
✓ MATCH (Tier 1 - exact): "velocity abuse" found in title/description

✅ FINAL: Matched "Velocity abuse" to "HIGH: Velocity Abuse"
```

Or if it fails:

```
Matching "Velocity abuse" against "CRITICAL: Account Takeover"
  - Word "velocity" found in title/description
  - Word "abuse" found in title/description
  - Match percentage: 100% (2/2 words)
✓ MATCH (Tier 3 - partial): 100% words matched

✅ FINAL: Matched "Velocity abuse" to "HIGH: Velocity Control"
```

**What to check:**
- Is the pattern name being matched correctly?
- Which tier is matching (or failing)?
- What is the actual recommendation title?

## Common Issues and Fixes

### Issue 1: AI Not Generating All Recommendations

**Symptom**: Backend logs show "AI generated 1 recommendations (expected 5)"

**Fix**: The backend has a fallback system that generates basic recommendations for missing types. Check if fallback is working.

**Location**: [realtime_agent.py:392-459](Backend/real_time/realtime_agent.py#L392-L459)

### Issue 2: Recommendation Titles Don't Match Pattern Names

**Symptom**:
- Frontend pattern: "Velocity abuse"
- AI title: "HIGH: Transaction Velocity Control"
- No common words → No match

**Fix**: The frontend has a 4-tier matching system with pattern variations. Check if variations are comprehensive enough.

**Location**: [RealTimeAnalysis.jsx:260-289](Frontend/src/pages/RealTimeAnalysis.jsx#L260-L289)

### Issue 3: Database Timeout During Training

**Symptom**:
```
Error fetching training data from database: statement timeout
```

**This is a separate issue** - doesn't affect recommendations, but prevents automatic model training.

**Temporary Fix**: Ignore this error - the system will use the existing trained model.

**Permanent Fix**: Optimize the database query or increase timeout limit.

## Expected Behavior

### Backend
1. Detects ALL fraud types in the dataset (e.g., 5 types)
2. Sends list of all fraud types to OpenAI
3. OpenAI generates 5 recommendations (one per fraud type)
4. If OpenAI generates fewer (e.g., 1), fallback system creates the remaining 4
5. Returns array of 5 recommendations to frontend

### Frontend
1. Receives 5 recommendations from backend
2. User hovers over "Velocity abuse" pattern
3. Searches through 5 recommendations for match
4. Tries 4 matching tiers:
   - Tier 1: Exact substring ("velocity abuse" in title)
   - Tier 2: Normalized ("velocityabuse" in title)
   - Tier 3: Partial words (2/2 words = 100%)
   - Tier 4: Reverse match (title words in pattern)
5. If any tier matches → Show popover
6. If no tier matches → Log to console, no popover

## Next Steps

Based on what you find in the logs:

### If AI is generating only 1 recommendation:
→ Check OpenAI API response and prompt
→ Verify fallback system is creating the other 4

### If AI is generating all 5 but titles don't match:
→ Add more pattern variations to frontend
→ Or update backend prompt to use exact fraud type names

### If frontend isn't receiving recommendations:
→ Check network tab (F12 → Network)
→ Look for `/api/analyze-real-time-transactions` response
→ Verify `agent_analysis.recommendations` array exists

## Quick Test

Run this in browser console after analysis completes:

```javascript
// Check if recommendations exist
console.log('Recommendations:', analysisResult?.agent_analysis?.recommendations);

// Check specific pattern
console.log('Velocity abuse match:', getRecommendationForPattern('Velocity abuse'));
```

---

**Last Updated**: 2025-12-15
**Status**: Debugging in progress
