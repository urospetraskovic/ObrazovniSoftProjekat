#!/usr/bin/env python
"""Test if Gemini API is working"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load env
env_path = os.path.join(os.path.dirname(__file__), '.env')
print(f"Loading .env from: {env_path}")
load_dotenv(env_path)

# Get key
gemini_key = os.getenv("GEMINI_API_KEY")
print(f"GEMINI_API_KEY loaded: {bool(gemini_key)}")
if gemini_key:
    print(f"Key length: {len(gemini_key)}")
    print(f"Key first 20 chars: {gemini_key[:20]}...")

if not gemini_key:
    print("[ERROR] GEMINI_API_KEY not found in .env")
    exit(1)

# Configure
try:
    genai.configure(api_key=gemini_key)
    print("[OK] Gemini configured successfully")
except Exception as e:
    print(f"[ERROR] Failed to configure: {e}")
    exit(1)

# Create model
try:
    model = genai.GenerativeModel("gemini-2.5-flash-lite")
    print("[OK] Model created (gemini-2.5-flash-lite)")
except Exception as e:
    print(f"[ERROR] Failed to create model: {e}")
    exit(1)

# Test API call
try:
    print("\nTesting API call...")
    response = model.generate_content("Say 'Gemini API is working!'")
    print("[OK] API call successful!")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"[ERROR] API call failed: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n[SUCCESS] All Gemini API tests passed!")
