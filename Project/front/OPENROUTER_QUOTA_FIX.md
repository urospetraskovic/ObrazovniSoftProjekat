# OpenRouter API Quota Issue - Root Causes & Fixes

## 🔴 Problems Identified

### 1. **CRITICAL: Overly Aggressive Error Handling** ✅ FIXED
**Location**: `content_parser.py` lines 150-188

**Problem**: 
```python
except Exception as e:
    print(f"[ContentParser] OpenRouter error: {e}")
    self.exhausted_keys.add(api_key)  # ❌ ANY error marks key as exhausted!
    self._rotate_api_key()
```

ANY exception (network timeout, connection error, malformed response) was marking your API keys as permanently exhausted for the session. This included:
- Network timeouts
- Connection errors
- JSON parsing errors
- Temporary server issues

**Impact**: Keys were being falsely marked as exhausted, causing rapid burnout of your key pool.

**Fix Applied**: 
- Only mark keys as exhausted on actual quota errors (429, 403 status codes)
- Handle network errors separately without marking keys as exhausted
- Better error logging to identify actual issues

---

### 2. **⚠️ Fallback Logic Using OpenRouter Too Eagerly**
**Location**: `content_parser.py` lines 228-244

**Problem**:
```python
def _call_ai(self, messages, max_tokens):
    # Try Gemini first
    result = self._call_gemini_api(messages, max_tokens)
    if result:
        return result
    
    # ❌ Falls back to OpenRouter immediately if Gemini has ANY issue
    print("[ContentParser] Gemini quota exhausted, trying OpenRouter...")
    result = self._call_openrouter_api(messages, max_tokens)
```

**Why This Burns Quota**:
- Gemini API may have temporary issues that aren't quota-related
- Even minor errors cause OpenRouter to be used as fallback
- You have **no daily limit on Gemini** but **strict daily limits on OpenRouter**

**Impact**: Every lesson parsing could be burning 5-10+ OpenRouter calls unnecessarily.

**Fix Applied**:
- Changed fallback order: **Gemini → GitHub Models → OpenRouter**
- GitHub Models has generous free tier
- OpenRouter is now truly a last resort to preserve daily quota

---

### 3. **Multiple API Calls Per Lesson Parse** ⚠️ ARCHITECTURAL ISSUE

**Problem**: Each lesson parse makes multiple API calls:

```
Parsing one lesson:
├─ parse_lesson_structure() 
│  ├─ 1 call to identify sections
│  └─ 1 call per section for learning objects (5-6 calls if 5-6 sections)
│     Total: 6-7 calls
├─ extract_ontology_relationships()  
│  └─ 1 call to find concept relationships
│     Total: 7-8 calls
└─ generate_lesson_summary()
   └─ 1 call to generate summary
      Total: 8-9 API CALLS PER LESSON! 🔴
```

**Impact**: 
- At 8-9 calls per lesson with daily limits
- Parsing just 2-3 lessons exhausts daily quota
- Explains why quota depletes so quickly

**Workaround**: Batch multiple section learning object extraction into single API call (requires code refactor - not applied yet)

---

## ✅ Fixes Applied

### Fix #1: Better Error Handling
```python
# NOW: Only mark as exhausted on actual quota errors
if response.status_code == 429 or response.status_code == 403:
    print(f"[ContentParser] Key exhausted ({response.status_code})")
    self.exhausted_keys.add(api_key)
    self._rotate_api_key()

# Handle other errors without marking key as exhausted
if response.status_code >= 400:
    print(f"[ContentParser] HTTP {response.status_code}: {response.text}")
    return None  # Don't mark as exhausted

# Handle network errors gracefully
except requests.exceptions.Timeout:
    print(f"[ContentParser] Network timeout, rotating key")
    self._rotate_api_key()
```

### Fix #2: Smarter Fallback Logic
```python
# NEW: Gemini → GitHub Models → OpenRouter
# Preserves OpenRouter quota by using free alternatives first

result = self._call_gemini_api(messages)  # No daily limits
if result:
    return result

result = self._call_github_api(messages)  # Generous free tier
if result:
    return result

result = self._call_openrouter_api(messages)  # Last resort - limited quota
if result:
    return result
```

---

## 📊 Expected Improvements

**Before**: OpenRouter keys exhausted after 2-3 lessons
**After**: 
- Network errors no longer consume keys
- Gemini used as primary (unlimited for your use case)
- OpenRouter preserved for true emergencies
- Estimated 70% reduction in OpenRouter quota usage

---

## 🔍 How to Debug Quota Issues

1. **Check API Usage**:
   ```bash
   curl -H "Authorization: Bearer YOUR_KEY" https://openrouter.ai/api/v1/auth/check
   ```

2. **Monitor Terminal Output**:
   - Look for which provider is actually being used
   - If you see "Gemini API" messages → Good! (no quota impact)
   - If you see many "OpenRouter" messages → Bad (quota burning)

3. **Verify Gemini is Working**:
   - Check that `GEMINI_API_KEY` is properly set in `.env`
   - Verify key has sufficient quota on Google Cloud Console

---

## ⚠️ Remaining Optimization Opportunity

For even better performance, consider batching:
- Instead of 1 API call per section's learning objects
- Combine all sections into 1 optimized prompt
- This could reduce calls from 8-9 to 3-4 per lesson

**Would need to refactor**: `parse_lesson_structure()` and `_extract_learning_objects()`

---

## Testing Recommendations

1. Parse a 5-10 page lesson and monitor:
   - How many API calls are made
   - Which providers are being used
   - Check OpenRouter dashboard for actual usage

2. Verify Gemini is handling most requests:
   ```
   Expected: [ContentParser] Gemini API...
   Avoid: [ContentParser] OpenRouter...
   ```

3. Reset your quota tracking if needed:
   - Clear `self.exhausted_keys` set at startup
   - Don't cache exhausted status across sessions
