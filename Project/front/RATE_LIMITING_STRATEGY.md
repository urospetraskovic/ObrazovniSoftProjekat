# API Rate Limiting & Retry Strategy

## Overview
Your parser now includes **intelligent retry logic with exponential backoff** to handle Gemini's per-minute rate limits. The system will automatically wait and retry instead of failing.

## How It Works

### Rate Limit Detection
When an API call fails with a rate limit error (429, quota error, etc.):

1. **Detect**: Error is identified as rate-limit related
2. **Wait**: System pauses for 60 seconds
3. **Retry**: Attempts the call again
4. **Wait Again**: If still rate limited, waits another 60 seconds (120s total)
5. **Final Retry**: Attempts one more time
6. **Fail Gracefully**: If still failing, assumes quota is exhausted and falls back

### Retry Flow Diagram
```
API Call (Attempt 1)
    ↓
    ├─ Success? → Return result ✓
    │
    ├─ Rate Limit? → Wait 60s → Retry (Attempt 2)
    │                  ↓
    │              Success? → Return result ✓
    │              Rate Limit? → Wait 120s → Retry (Attempt 3)
    │                              ↓
    │                          Success? → Return result ✓
    │                          Rate Limit? → Quota exhausted → Fall back
    │
    ├─ Other Error? → Return None (don't retry)
```

## Configuration

### Gemini (Primary)
- **Max Retries**: 3 attempts
- **Initial Delay**: 60 seconds
- **Delays**: 60s → 120s → 180s
- **When to Wait**: Per-minute rate limits (429 errors)

### OpenRouter (Fallback)
- **Max Retries**: 3 attempts
- **Initial Delay**: 30 seconds (more forgiving)
- **Delays**: 30s → 60s → 90s
- **When to Wait**: Rate limit (429) or timeout errors

## Example Flow

```
[ContentParser] Calling Gemini API...
[ContentParser] Rate limit error detected. Waiting 60s before retry 1/2...
[ContentParser] Retrying after wait...
[ContentParser] Calling Gemini API...
[ContentParser] OK Gemini API succeeded

Result: Success after 60 second wait ✓
```

## What Gets Retried?

✅ **Rate Limit Errors (429)**
- These are recoverable - temporary limit on requests/minute
- System waits and retries

✅ **Quota Errors** 
- Daily quota limits
- System retries in case quota resets mid-request

✅ **Timeout Errors**
- Network timeouts
- Retried with delay to avoid overwhelming server

❌ **NOT Retried**
- Invalid API keys
- Bad request format
- Authentication failures
- These would fail repeatedly anyway

## Slow Processing is OK

⚠️ **Expected Behavior**:
- Parsing a single lesson may take 10-15 minutes
- Gemini will hit per-minute limits after a few API calls
- System will pause for 60 seconds and continue
- This is **completely normal and expected**

🎯 **Goal**: Parse the entire PDF and create all ontologies, even if it takes time

## Monitoring

Watch terminal output for:

```
[ContentParser] Calling Gemini API...
[ContentParser] Rate limit error detected. Waiting 60s before retry...
```

This means the system is working correctly - it's just pacing API calls to stay within per-minute limits.

## Key Changes

1. **Added `import time`** for delays
2. **Added `_retry_with_backoff()` method** - handles retry logic with exponential backoff
3. **Updated `_call_gemini_api()`** - now uses retry wrapper
4. **Updated `_call_openrouter_api()`** - now uses retry wrapper with 30s delays
5. **Intelligent error detection** - distinguishes rate limits from other errors

## No More Failures

Before:
```
[ContentParser] Rate limit error: 429
[API] Error extracting ontology relationships: All API providers failed
```

After:
```
[ContentParser] Rate limit error detected. Waiting 60s before retry...
[ContentParser] Retrying after wait...
[ContentParser] OK Gemini API succeeded ✓
```

## Benefits

✅ Complete parsing even with rate limits
✅ Automatic recovery from temporary errors
✅ Exponential backoff prevents hammering servers
✅ Progress shown in terminal (you can see it working)
✅ Works within Gemini's free tier limits
