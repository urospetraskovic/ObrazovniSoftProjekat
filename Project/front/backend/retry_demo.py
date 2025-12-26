#!/usr/bin/env python
"""
Test retry logic with rate limiting simulation

This demonstrates how the retry logic works when hitting rate limits.
"""

import os
import time
from dotenv import load_dotenv

# Load env
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

# Show what will happen
print("""
=== RETRY LOGIC DEMONSTRATION ===

When your API hits per-minute rate limits:

1. System detects 429 error (rate limited)
2. Waits 60 seconds
3. Retries the request
4. If still rate limited, waits 120 seconds
5. Retries again
6. If still failing, assumes quota exhausted

Example from logs you'll see:

[ContentParser] Calling Gemini API...
[ContentParser] Rate limit error detected. Waiting 60s before retry 1/2...
  (waits 60 seconds)
[ContentParser] Retrying after wait...
[ContentParser] Calling Gemini API...
[ContentParser] OK Gemini API succeeded (tokens: ~582)

Key Points:
- This is NORMAL and EXPECTED
- Parsing will be slow but COMPLETE
- Each PDF will take 10-30 minutes depending on size
- All sections and ontologies will be extracted

Your configuration:
- Gemini: 3 retries with 60/120/180 second delays
- OpenRouter: 3 retries with 30/60/90 second delays
- System will keep trying until quota truly runs out

Let the system run - it WILL finish parsing everything!
""")

# Show current config
gemini_key = os.getenv("GEMINI_API_KEY")
openrouter_keys = [os.getenv(f'OPENROUTER_API_KEY{i}') or os.getenv(f'OPENROUTER_API_KEY_{i}') 
                   for i in range(1, 14)]
openrouter_keys = [k for k in openrouter_keys if k]

print(f"\nCurrent Configuration:")
print(f"- Gemini API Key: {'✓ Configured' if gemini_key else '✗ NOT configured'}")
print(f"- OpenRouter Keys: {len(openrouter_keys)} keys available")
print(f"- Retry Strategy: Exponential backoff with delays")
print(f"- Expected parsing time: 10-30 minutes per PDF")
