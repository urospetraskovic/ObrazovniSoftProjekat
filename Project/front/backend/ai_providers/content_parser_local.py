# Local Ollama version of content_parser already exists as the main content_parser.py
# This is a reference - in production, copy content_parser.py here or import from it

from pathlib import Path
import sys

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the actual local content parser
from content_parser import (
    ContentParser, 
    content_parser
)

# Re-export for convenience
__all__ = ['ContentParser', 'content_parser']
