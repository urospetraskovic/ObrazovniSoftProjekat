"""
Content Parser Module
Extracts sections and learning objects from PDF lesson content using AI
"""

import os
import json
import re
import time
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import requests
from PyPDF2 import PdfReader
import google.generativeai as genai

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

# Initialize Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


class ContentParser:
    """
    Parses PDF lessons to extract structured content:
    - Sections (major topic divisions)
    - Learning Objects (specific concepts, definitions, procedures)
    """
    
    def __init__(self):
        """Initialize the content parser with API configuration"""
        # Gemini API (Primary)
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            # Use gemini-2.5-flash-lite for better free tier quota
            # Lighter version with more generous rate limits on free tier
            self.gemini_model = genai.GenerativeModel("gemini-2.5-flash-lite")
            print("[ContentParser] Gemini API: Using gemini-2.5-flash-lite (optimized for free tier)")
        else:
            self.gemini_model = None
            print("[ContentParser] Warning: Gemini API key not configured")
        
        # Groq API (Secondary fallback)
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if self.groq_api_key:
            print(f"[ContentParser] Groq API: Configured (key loaded)")
        else:
            print("[ContentParser] Warning: Groq API key not configured")
        
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
            os.getenv('OPENROUTER_API_KEY_11'),
            os.getenv('OPENROUTER_API_KEY_12'),
            os.getenv('OPENROUTER_API_KEY_13'),
        ]
        self.api_keys = [key for key in self.api_keys if key]
        
        # GitHub Models API token (fallback)
        self.github_token = os.getenv('GITHUB_TOKEN')
        
        if not self.api_keys:
            print("[ContentParser] Warning: No OpenRouter API keys configured (fallback).")
            self.api_keys = ['mock']
        else:
            print(f"[ContentParser] OpenRouter: {len(self.api_keys)} API keys loaded (fallback)")
        
        self.current_key_index = 0
        self.provider = "gemini"  # Primary provider
        self.exhausted_keys = set()  # Track which keys are exhausted
    
    def _retry_with_backoff(self, func, max_retries: int = 3, initial_delay: int = 1) -> Optional[Any]:
        """
        Retry a function with exponential backoff for rate limiting
        
        Args:
            func: Function to call that returns result or None on failure
            max_retries: Number of times to retry (default: 3)
            initial_delay: Initial delay in seconds (default: 1 for testing)
        
        Returns:
            Result from function or None if all retries fail
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                result = func()
                if result is not None:
                    return result
                
                # If result is None but no exception, it means rate limited
                if attempt < max_retries - 1:
                    delay = initial_delay * (attempt + 1)  # Exponential: 1s, 2s, 3s
                    print(f"[ContentParser] Rate limited. Waiting {delay}s before retry {attempt + 1}/{max_retries - 1}...")
                    time.sleep(delay)
                    print(f"[ContentParser] Retrying after wait...")
                    continue
                
            except Exception as e:
                last_error = e
                error_str = str(e)
                
                # Check if it's a rate limit error
                if "429" in error_str or "rate" in error_str.lower() or "quota" in error_str.lower():
                    if attempt < max_retries - 1:
                        delay = initial_delay * (attempt + 1)
                        print(f"[ContentParser] Rate limit error detected. Waiting {delay}s before retry {attempt + 1}/{max_retries - 1}...")
                        time.sleep(delay)
                        print(f"[ContentParser] Retrying after wait...")
                        continue
                    else:
                        print(f"[ContentParser] Rate limit persists after retries - quota may be exhausted")
                        return None
                
                # For other errors, don't retry
                print(f"[ContentParser] Non-recoverable error: {type(e).__name__}: {error_str[:100]}")
                return None
        
        print(f"[ContentParser] All retries exhausted")
        return None
    
    def extract_pdf_text(self, filepath: str) -> Dict[str, Any]:
        """
        Extract text from PDF file with page information
        
        Returns:
            {
                'full_text': str,
                'pages': [{'page_num': int, 'text': str}, ...]
            }
        """
        try:
            reader = PdfReader(filepath)
            pages = []
            full_text = ""
            
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                pages.append({
                    'page_num': page_num + 1,
                    'text': page_text
                })
                full_text += f"\n--- Page {page_num + 1} ---\n{page_text}"
            
            return {
                'full_text': full_text,
                'pages': pages,
                'page_count': len(pages)
            }
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    def _get_api_key(self):
        """Get current API key for OpenRouter"""
        if self.api_keys and self.api_keys[0] != 'mock':
            return self.api_keys[self.current_key_index]
        return None
    
    def _rotate_api_key(self):
        """Rotate to next API key"""
        if len(self.api_keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            print(f"[ContentParser] Rotated to API key {self.current_key_index + 1}")
    
    def _call_gemini_api(self, messages: List[Dict], max_tokens: int = 4000) -> Optional[str]:
        """Call Gemini API (Primary provider) with automatic retry on rate limits"""
        if not self.gemini_model:
            print("[ContentParser] ERROR: Gemini model not initialized! Check GEMINI_API_KEY in .env")
            return None
        
        def attempt_call():
            try:
                # Convert messages format to Gemini format
                prompt_text = ""
                for msg in messages:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    prompt_text += f"{role.upper()}: {content}\n\n"
                
                print("[ContentParser] Calling Gemini API...")
                response = self.gemini_model.generate_content(
                    prompt_text,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=max_tokens,
                        temperature=0.3
                    )
                )
                
                if response and response.text:
                    print(f"[ContentParser] OK Gemini API succeeded (tokens: ~{len(response.text.split())})")
                    return response.text
                else:
                    print("[ContentParser] Gemini returned empty response")
                    return None
                    
            except Exception as e:
                error_str = str(e)
                # Check if it's a quota error
                if "429" in error_str or "quota" in error_str.lower() or "ResourceExhausted" in str(type(e)):
                    print(f"[ContentParser] Rate limit/quota error detected: {error_str[:100]}")
                    raise  # Re-raise to trigger retry logic
                else:
                    print(f"[ContentParser] Gemini API FAILED: {type(e).__name__}: {error_str[:100]}")
                    return None  # Don't retry on non-rate-limit errors
        
        # Use retry logic for rate limits
        return self._retry_with_backoff(attempt_call, max_retries=3, initial_delay=1)
    
    def _call_openrouter_api(self, messages: List[Dict], max_tokens: int = 4000) -> Optional[str]:
        """Call OpenRouter API with retry on rate limits"""
        api_key = self._get_api_key()
        if not api_key:
            return None
        
        # Skip if this key is already known to be exhausted
        if api_key in self.exhausted_keys:
            self._rotate_api_key()
            return None
        
        def attempt_call():
            try:
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "http://localhost:3000",
                        "X-Title": "SOLO Quiz Generator"
                    },
                    json={
                        "model": "google/gemini-2.0-flash-001",
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": 0.3
                    },
                    timeout=1
                )
                
                # Only mark as exhausted if it's actually a quota error
                if response.status_code == 429 or response.status_code == 403:
                    print(f"[ContentParser] Key exhausted ({response.status_code}), rotating key")
                    self.exhausted_keys.add(api_key)
                    self._rotate_api_key()
                    if response.status_code == 429:
                        raise Exception("Rate limited")  # Trigger retry
                    return None
                
                # For other HTTP errors, don't mark as exhausted
                if response.status_code >= 400:
                    print(f"[ContentParser] OpenRouter HTTP {response.status_code}: {response.text[:100]}")
                    return None
                
                response.raise_for_status()
                data = response.json()
                return data['choices'][0]['message']['content']
                
            except requests.exceptions.Timeout:
                print(f"[ContentParser] OpenRouter timeout - network issue")
                self._rotate_api_key()
                raise  # Retry on timeout
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "rate" in error_str.lower():
                    print(f"[ContentParser] OpenRouter rate limit: {error_str[:100]}")
                    raise  # Retry on rate limit
                return None
        
        # Use retry logic for rate limits
        return self._retry_with_backoff(attempt_call, max_retries=3, initial_delay=1)
    
    def _call_github_api(self, messages: List[Dict], max_tokens: int = 4000) -> Optional[str]:
        """Call GitHub Models API as fallback"""
        if not self.github_token:
            return None
        
        try:
            response = requests.post(
                "https://models.inference.ai.azure.com/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.github_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o",
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": 0.3
                },
                timeout=1
            )
            
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
            
        except Exception as e:
            print(f"[ContentParser] GitHub Models error: {e}")
            return None
    
    def _call_groq_api(self, messages: List[Dict], max_tokens: int = 4000) -> Optional[str]:
        """Call Groq API as fallback"""
        if not self.groq_api_key:
            return None
        
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "mixtral-8x7b-32768",
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": 0.3
                },
                timeout=1
            )
            
            response.raise_for_status()
            data = response.json()
            print("[ContentParser] Groq API succeeded")
            return data['choices'][0]['message']['content']
            
        except Exception as e:
            print(f"[ContentParser] Groq API error: {e}")
            return None
    
    def _call_ai(self, messages: List[Dict], max_tokens: int = 4000) -> str:
        """
        Call AI API with fallback chain: Gemini (Primary) -> Groq -> GitHub Models -> OpenRouter
        Note: Gemini is primary provider and has NO daily limits like OpenRouter
        """
        # Try Gemini API first (Primary - NO daily quota limits)
        try:
            result = self._call_gemini_api(messages, max_tokens)
            if result:
                return result
        except Exception as e:
            print(f"[ContentParser] Gemini API error (not quota): {e}")
        
        # Try Groq as secondary (fast and reliable)
        print("[ContentParser] Gemini unavailable, trying Groq...")
        result = self._call_groq_api(messages, max_tokens)
        if result:
            print("[ContentParser] Using Groq API")
            return result
        
        # Try GitHub Models as tertiary (has generous free quota)
        print("[ContentParser] Groq unavailable, trying GitHub Models...")
        result = self._call_github_api(messages, max_tokens)
        if result:
            print("[ContentParser] Using GitHub Models API")
            return result
        
        # Only use OpenRouter as LAST resort to preserve daily limits
        print("[ContentParser] GitHub Models unavailable, falling back to OpenRouter...")
        result = self._call_openrouter_api(messages, max_tokens)
        if result:
            return result
        
        raise Exception("All API providers failed")
    
    def _extract_json_from_response(self, response: str) -> Any:
        """Extract JSON from AI response"""
        # Try to find JSON in code blocks
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass
        
        # Try to parse the whole response
        try:
            return json.loads(response)
        except:
            pass
        
        # Try to find JSON array or object
        for pattern in [r'\[[\s\S]*\]', r'\{[\s\S]*\}']:
            match = re.search(pattern, response)
            if match:
                try:
                    return json.loads(match.group(0))
                except:
                    continue
        
        raise Exception("Could not extract JSON from response")
    
    def parse_lesson_structure(self, content: str, lesson_title: str) -> List[Dict[str, Any]]:
        """
        Parse lesson content to extract sections and learning objects
        
        Args:
            content: Raw text content from PDF
            lesson_title: Title of the lesson
            
        Returns:
            List of sections with learning objects:
            [
                {
                    'title': 'Section Title',
                    'content': 'Full section text...',
                    'start_page': 1,
                    'end_page': 3,
                    'learning_objects': [
                        {
                            'title': 'Concept Name',
                            'content': 'Description...',
                            'object_type': 'concept|definition|procedure|example|principle',
                            'keywords': ['keyword1', 'keyword2']
                        }
                    ]
                }
            ]
        """
        print(f"[ContentParser] Parsing structure for: {lesson_title}")
        
        # First, identify sections
        sections_prompt = f"""Analyze this educational lesson content and identify the main SECTIONS (major topic divisions).

LESSON TITLE: {lesson_title}

CONTENT:
{content[:15000]}  # Limit to avoid token limits

YOUR TASK:
1. Identify 3-8 main sections/topics in this lesson
2. For each section, identify:
   - A clear title
   - The approximate page range (if page markers are visible like "--- Page X ---")
   - A brief summary of what the section covers

RESPOND WITH JSON ONLY:
```json
[
    {{
        "title": "Section Title",
        "start_page": 1,
        "end_page": 3,
        "summary": "Brief description of section content"
    }}
]
```

Identify sections based on logical topic divisions, headings, or natural content breaks."""

        messages = [
            {"role": "system", "content": "You are an expert at analyzing educational content and identifying logical structure. Always respond with valid JSON."},
            {"role": "user", "content": sections_prompt}
        ]
        
        try:
            response = self._call_ai(messages, max_tokens=2000)
            sections_info = self._extract_json_from_response(response)
            print(f"[ContentParser] Found {len(sections_info)} sections")
        except Exception as e:
            print(f"[ContentParser] Error identifying sections: {e}")
            # Fallback: treat entire content as one section
            sections_info = [{
                "title": lesson_title,
                "start_page": 1,
                "end_page": None,
                "summary": "Full lesson content"
            }]
        
        # Now parse each section for learning objects
        parsed_sections = []
        
        for section in sections_info:
            section_content = self._extract_section_content(content, section)
            
            if not section_content:
                section_content = content[:5000]  # Fallback
            
            learning_objects = self._extract_learning_objects(
                section_content, 
                section['title'],
                lesson_title
            )
            
            parsed_sections.append({
                'title': section['title'],
                'content': section_content,
                'start_page': section.get('start_page'),
                'end_page': section.get('end_page'),
                'summary': section.get('summary'),
                'learning_objects': learning_objects
            })
        
        return parsed_sections
    
    def _extract_section_content(self, full_content: str, section_info: Dict) -> str:
        """Extract content for a specific section based on page numbers or title"""
        start_page = section_info.get('start_page')
        end_page = section_info.get('end_page')
        
        if start_page and end_page:
            # Try to extract by page markers
            pattern = rf'--- Page {start_page} ---'
            start_match = re.search(pattern, full_content)
            
            if start_match:
                end_pattern = rf'--- Page {end_page + 1} ---'
                end_match = re.search(end_pattern, full_content)
                
                if end_match:
                    return full_content[start_match.start():end_match.start()]
                else:
                    return full_content[start_match.start():]
        
        # Fallback: try to find section by title
        title = section_info.get('title', '')
        if title:
            # Look for the title in content
            title_pattern = re.escape(title)
            match = re.search(title_pattern, full_content, re.IGNORECASE)
            if match:
                # Return content starting from title (limited length)
                return full_content[match.start():match.start() + 5000]
        
        return ""
    
    def _extract_learning_objects(self, section_content: str, section_title: str, lesson_title: str) -> List[Dict]:
        """Extract learning objects from a section"""
        
        prompt = f"""Analyze this SECTION from an educational lesson and extract LEARNING OBJECTS.

LESSON: {lesson_title}
SECTION: {section_title}

SECTION CONTENT:
{section_content[:8000]}

LEARNING OBJECTS are discrete units of knowledge that can be:
- CONCEPT: Abstract ideas or notions (e.g., "Virtual Memory", "Paging")
- DEFINITION: Precise definitions of terms
- PROCEDURE: Step-by-step processes or algorithms
- PRINCIPLE: Rules, laws, or fundamental truths
- EXAMPLE: Concrete illustrations of concepts
- FACT: Specific pieces of information

YOUR TASK:
Extract 2-6 learning objects from this section. For each:
1. Give it a clear, specific title
2. Provide the essential content/description
3. Classify its type
4. List 2-4 keywords

RESPOND WITH JSON ONLY:
```json
[
    {{
        "title": "Learning Object Title",
        "content": "Clear explanation of this learning object...",
        "object_type": "concept",
        "keywords": ["keyword1", "keyword2", "keyword3"]
    }}
]
```"""

        messages = [
            {"role": "system", "content": "You are an expert at educational content analysis. Extract specific, teachable learning objects. Always respond with valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self._call_ai(messages, max_tokens=2000)
            learning_objects = self._extract_json_from_response(response)
            print(f"[ContentParser] Extracted {len(learning_objects)} learning objects from '{section_title}'")
            return learning_objects
        except Exception as e:
            print(f"[ContentParser] Error extracting learning objects: {e}")
            return []

    def extract_ontology_relationships(self, content: str, learning_objects: List[Dict], lesson_title: str) -> List[Dict]:
        """
        Identify relationships between learning objects to form a domain ontology
        """
        lo_titles = [lo['title'] for lo in learning_objects]
        print(f"[ContentParser] Extracting ontology from {len(learning_objects)} LOs: {lo_titles}")
        
        prompt = f"""Analyze the relationships between these LEARNING OBJECTS from the lesson '{lesson_title}'.
        
LEARNING OBJECTS:
{json.dumps(lo_titles, indent=2)}

CONTENT SNIPPET:
{content[:10000]}

YOUR TASK:
Identify logical relationships between these concepts to form a DOMAIN ONTOLOGY.
Possible relationship types:
- prerequisite: Concept A must be understood before Concept B
- part_of: Concept A is a component or sub-topic of Concept B
- related_to: Concept A and Concept B are conceptually linked
- instance_of: Concept A is a specific example of Concept B

RESPOND WITH JSON ONLY:
```json
[
    {{
        "source": "Concept A Title",
        "target": "Concept B Title",
        "type": "prerequisite|part_of|related_to|instance_of",
        "description": "Brief explanation of why this relationship exists"
    }}
]
```"""

        messages = [
            {"role": "system", "content": "You are an expert in knowledge representation and ontology engineering. Identify meaningful relationships between educational concepts. Always respond with valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self._call_ai(messages, max_tokens=2000)
            print(f"[ContentParser] Ontology API response received: {response[:200]}...")
            relationships = self._extract_json_from_response(response)
            print(f"[ContentParser] Identified {len(relationships)} ontology relationships: {relationships}")
            return relationships
        except Exception as e:
            print(f"[ContentParser] Error extracting ontology relationships: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def generate_lesson_summary(self, content: str, lesson_title: str) -> str:
        """Generate a summary of the lesson content"""
        
        prompt = f"""Summarize this educational lesson in 2-3 paragraphs.

LESSON TITLE: {lesson_title}

CONTENT:
{content[:10000]}

Provide a clear, informative summary that captures:
1. The main topics covered
2. Key concepts students should understand
3. The importance/relevance of this material

Write in a professional, educational tone."""

        messages = [
            {"role": "system", "content": "You are an expert educator. Provide clear, helpful summaries."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            return self._call_ai(messages, max_tokens=500)
        except Exception as e:
            print(f"[ContentParser] Error generating summary: {e}")
            return ""


# Create global parser instance
content_parser = ContentParser()
