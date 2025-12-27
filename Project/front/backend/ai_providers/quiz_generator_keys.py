# This file has been moved to ai_providers folder
# Import from: from ai_providers.quiz_generator_keys import SoloQuizGenerator

import os
import json
import re
from datetime import datetime
from dotenv import load_dotenv
import requests
from typing import Dict, List, Any
import google.generativeai as genai

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

# Initialize Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class SoloQuizGenerator:
    """
    SOLO Taxonomy Quiz Generator - Uses External APIs (Gemini, Groq, OpenRouter)
    Generates educational quizzes from text content using SOLO taxonomy levels
    Supports multiple fallback providers
    """
    
    def __init__(self):
        """Initialize the quiz generator with API configuration"""
        # Gemini API (Primary)
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel("gemini-2.0-flash")
            print("[INIT] Gemini API: Primary provider loaded")
        else:
            self.gemini_model = None
            print("[INIT] Warning: Gemini API key not configured")
        
        # Groq API (Secondary fallback)
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if self.groq_api_key:
            print(f"[INIT] Groq API: Configured (key loaded)")
        else:
            print("[INIT] Warning: Groq API key not configured")
        
        # OpenRouter API keys (Fallback)
        self.api_keys = [
            os.getenv('OPENROUTER_API_KEY'),
            os.getenv('OPENROUTER_API_KEY_2'),
            os.getenv('OPENROUTER_API_KEY_3'),
            os.getenv('OPENROUTER_API_KEY_4'),
            os.getenv('OPENROUTER_API_KEY_5'),
            os.getenv('OPENROUTER_API_KEY_6'),
            os.getenv('OPENROUTER_API_KEY_7'),
            os.getenv('OPENROUTER_API_KEY_8'),
            os.getenv('OPENROUTER_API_KEY_9'),
        ]
        # Filter out None values
        self.api_keys = [key for key in self.api_keys if key]
        
        # GitHub Models API token (fallback)
        self.github_token = os.getenv('GITHUB_TOKEN')
        
        if not self.api_keys:
            print("[INIT] Warning: No OpenRouter API keys configured (fallback).")
            self.api_keys = ['mock']
        else:
            print(f"[INIT] OpenRouter: {len(self.api_keys)} API keys loaded (fallback)")
        
        if not self.github_token:
            print("[INIT] Warning: No GitHub token configured for fallback model.")
        else:
            print(f"[INIT] GitHub Models: Token loaded ({self.github_token[:30]}...)")
        
        self.current_key_index = 0
        self.provider = "gemini"  # Primary provider
        self.api_exhausted = False
        self._content_summary_cache = {}

# NOTE: The full SoloQuizGenerator implementation from the original file continues here
# This is just a reference stub - import from the full version in production
