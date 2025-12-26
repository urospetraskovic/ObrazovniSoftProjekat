#!/usr/bin/env python
"""List available Gemini models"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load env
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

gemini_key = os.getenv("GEMINI_API_KEY")
if not gemini_key:
    print("ERROR: GEMINI_API_KEY not found")
    exit(1)

genai.configure(api_key=gemini_key)

print("Available Gemini models:")
print("=" * 60)

try:
    models = genai.list_models()
    for model in models:
        print(f"\nModel: {model.name}")
        print(f"  Display Name: {model.display_name}")
        print(f"  Description: {model.description}")
        if hasattr(model, 'supported_generation_methods'):
            print(f"  Methods: {model.supported_generation_methods}")
        print()
except Exception as e:
    print(f"Error listing models: {e}")
    import traceback
    traceback.print_exc()
