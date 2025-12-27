"""
AI Providers Package
Provides different implementations of content parsing and question generation
- Local: Uses Ollama (no API keys needed, runs locally)
- Keys: Uses external APIs (Gemini, Groq, OpenRouter)
"""

# Local providers (Ollama-based)
from ai_providers.content_parser_local import ContentParser as ContentParserLocal
from ai_providers.quiz_generator_local import SoloQuizGeneratorLocal

# You can import Keys versions if needed:
# from ai_providers.quiz_generator_keys import SoloQuizGenerator as SoloQuizGeneratorKeys

__all__ = [
    'ContentParserLocal',
    'SoloQuizGeneratorLocal',
]
