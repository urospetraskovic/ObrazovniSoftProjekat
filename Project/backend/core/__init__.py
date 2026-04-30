"""
Core AI Processing Package
Contains content parsing and quiz generation using local Ollama models
"""

from .content_parser import ContentParser, content_parser
from .quiz_generator import SoloQuizGeneratorLocal

__all__ = [
    'ContentParser',
    'content_parser',
    'SoloQuizGeneratorLocal'
]
