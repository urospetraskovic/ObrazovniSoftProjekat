"""
Content Parser Module - Local Ollama Version
Extracts sections and learning objects from PDF lesson content using local LLM (Ollama)
"""

import os
import json
import re
import time
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from PyPDF2 import PdfReader
import requests

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

# Ollama Configuration
OLLAMA_BASE_URL = "http://127.0.0.1:11434"
OLLAMA_MODEL = "qwen2.5:14b-instruct-q4_K_M"  # High quality model for all tasks


class ContentParser:
    """
    Parses PDF lessons to extract structured content using local Ollama models:
    - Sections (major topic divisions)
    - Learning Objects (specific concepts, definitions, procedures)
    """
    
    def __init__(self):
        """Initialize the content parser with Ollama configuration"""
        self.ollama_base_url = OLLAMA_BASE_URL
        self.ollama_model = OLLAMA_MODEL
        self.provider = "ollama"
        
        print(f"[ContentParser] Initialized with Ollama (14B model for maximum quality)")
        print(f"[ContentParser] Model: {self.ollama_model}")
        print(f"[ContentParser] Server: {self.ollama_base_url}")
        
        # Test connection
        if not self._test_ollama_connection():
            print("[ContentParser] WARNING: Could not connect to Ollama server!")
            print(f"[ContentParser] Make sure Ollama is running on {self.ollama_base_url}")
    
    def _test_ollama_connection(self) -> bool:
        """Test if Ollama server is responding"""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"[ContentParser] Connection test failed: {e}")
            return False
    
    def _call_ollama(self, prompt: str, timeout: int = 300) -> Optional[str]:
        """
        Call Ollama API with the 14B model
        
        Args:
            prompt: The prompt to send to the model
            timeout: Timeout in seconds (default: 300 for quality)
        
        Returns:
            Generated text or None on error
        """
        try:
            url = f"{self.ollama_base_url}/api/generate"
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.7,
            }
            
            print(f"[ContentParser] Calling Ollama ({len(prompt)} chars prompt)...")
            response = requests.post(url, json=payload, timeout=timeout)
            
            if response.status_code == 200:
                data = response.json()
                result = data.get("response", "")
                print(f"[ContentParser] Ollama returned {len(result)} chars")
                if len(result) < 50:
                    print(f"[ContentParser] WARNING: Very short response: {result}")
                return result
            else:
                print(f"[ContentParser] Ollama error: {response.status_code}")
                print(f"[ContentParser] Response: {response.text[:200]}")
                return None
                
        except requests.Timeout:
            print(f"[ContentParser] Ollama request timed out after {timeout}s")
            return None
        except Exception as e:
            print(f"[ContentParser] Ollama error: {e}")
            return None
    
    def extract_pdf_text(self, filepath: str) -> Dict[str, Any]:
        """
        Extract text from PDF file
        
        Args:
            filepath: Path to PDF file
            
        Returns:
            Dictionary with 'content' and metadata
        """
        try:
            with open(filepath, 'rb') as file:
                pdf_reader = PdfReader(file)
                text_content = ""
                
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    text_content += f"\n--- Page {page_num + 1} ---\n{text}"
            
            return {
                "success": True,
                "content": text_content,
                "full_text": text_content,  # For app.py compatibility
                "pages": len(pdf_reader.pages),
                "filepath": filepath
            }
            
        except Exception as e:
            print(f"[ContentParser] PDF extraction error: {e}")
            return {
                "success": False,
                "error": str(e),
                "filepath": filepath
            }
    
    def parse_lesson_structure(self, content: str, lesson_title: str) -> List[Dict[str, Any]]:
        """
        Parse lesson content into sections with learning objects
        
        Args:
            content: Full lesson content
            lesson_title: Title of the lesson
            
        Returns:
            List of section dictionaries with learning objects
        """
        prompt = f"""Analyze the following lesson and identify main sections/topics. RESPOND IN ENGLISH ONLY.
        
Lesson: {lesson_title}
Content:
{content[:2000]}

Provide output as JSON array of sections with format (titles in ENGLISH):
[
  {{"section_number": 1, "title": "Section Title in English", "key_topics": ["topic1 in English", "topic2 in English"]}},
  ...
]

Return ONLY valid JSON array, no other text. All titles and topics must be in ENGLISH."""
        
        print("[ContentParser] Parsing lesson structure...")
        response = self._call_ollama(prompt)
        
        if not response:
            print("[ContentParser] Failed to parse structure")
            return [{"section_number": 1, "title": lesson_title, "key_topics": []}]
        
        sections = self._extract_json_from_response(response)
        if not isinstance(sections, list):
            return [{"section_number": 1, "title": lesson_title, "key_topics": []}]
        
        print(f"[ContentParser] Found {len(sections)} sections - now extracting learning objects for each...")
        
        # Now extract learning objects for each section
        for section in sections:
            section_title = section.get('title', f"Section {section.get('section_number', 1)}")
            key_topics = section.get('key_topics', [])
            
            # Build a focused prompt for this section
            section_keywords = " ".join(key_topics) if key_topics else section_title
            section_content = self._extract_section_content(content, section_keywords, section_title)
            
            # Extract learning objects for this section
            learning_objects = self._extract_learning_objects(
                section_content,
                section_title,
                lesson_title
            )
            
            section['learning_objects'] = learning_objects
            print(f"[ContentParser] Section '{section_title}': {len(learning_objects)} learning objects")
        
        return sections
    
    def _extract_json_from_response(self, response: str) -> Any:
        """Extract JSON from LLM response with detailed logging"""
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\[.*\]|\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
                print(f"[ContentParser] Successfully extracted JSON: {type(result).__name__}")
                return result
            else:
                print(f"[ContentParser] WARNING: No JSON found in response. Response preview: {response[:200]}")
        except json.JSONDecodeError as e:
            print(f"[ContentParser] JSON parse error: {e}")
            print(f"[ContentParser] Response preview: {response[:300]}")
        
        return None
    
    def _extract_section_content(self, full_content: str, keywords: str, section_title: str) -> str:
        """
        Extract relevant content for a section based on keywords
        
        Args:
            full_content: Full lesson content
            keywords: Keywords to search for
            section_title: Title of the section
            
        Returns:
            Extracted section content
        """
        # Simple approach: find content around keywords
        lines = full_content.split('\n')
        keyword_list = keywords.lower().split()
        
        relevant_lines = []
        for line in lines:
            line_lower = line.lower()
            if any(kw in line_lower for kw in keyword_list) or section_title.lower() in line_lower:
                relevant_lines.append(line)
        
        # If we found matching lines, use them. Otherwise use first part
        if relevant_lines:
            return '\n'.join(relevant_lines[:50])  # Limit to 50 lines
        
        return full_content[:1500]  # Fallback: use first 1500 chars
    
    def _extract_learning_objects(self, section_content: str, section_title: str, lesson_title: str) -> List[Dict]:
        """
        Extract learning objects with COMPREHENSIVE MULTI-PROMPT ENRICHMENT
        Prompt 1: Identify objects
        Prompt 2-N: Enrich each object with detailed descriptions, examples, key points
        """
        content_preview = section_content[:1500].strip()
        
        # PROMPT 1: Initial object identification
        prompt1 = f"""IDENTIFY LEARNING OBJECTS. RESPOND IN ENGLISH ONLY.

LESSON: {lesson_title}
SECTION: {section_title}

CONTENT:
{content_preview}

---

Extract 5-8 key learning objects (ALL IN ENGLISH):
[
  {{"title": "Object Name", "type": "concept", "keywords": ["kw1", "kw2", "kw3"]}}
]

Return ONLY JSON array with title, type, keywords."""
        
        print(f"[ContentParser] STEP 1: Identifying learning objects in: {section_title}")
        resp1 = self._call_ollama(prompt1, timeout=300)
        
        if not resp1:
            print("[ContentParser] No response from Ollama - step 1")
            return []
        
        initial_objects = self._extract_json_from_response(resp1)
        if not isinstance(initial_objects, list) or len(initial_objects) == 0:
            print(f"[ContentParser] Failed to extract initial objects")
            return []
        
        print(f"[ContentParser] Step 1 complete: Found {len(initial_objects)} objects to enrich")
        
        # PROMPT 2-N: ENRICH each object with detailed description
        enriched_objects = []
        for i, obj in enumerate(initial_objects):
            obj_title = obj.get('title', 'Unknown')
            obj_type = obj.get('type', 'concept')
            print(f"[ContentParser] STEP 2.{i+1}: Enriching '{obj_title}' ({obj_type})")
            
            # Get comprehensive definition
            prompt2 = f"""WRITE COMPREHENSIVE EXPLANATION. RESPOND IN ENGLISH ONLY.

LESSON: {lesson_title}
SECTION: {section_title}
CONCEPT: {obj_title}
TYPE: {obj_type}

CONTENT FROM MATERIAL:
{content_preview}

---

Write a CONCISE 1-2 sentence description using ONLY information from the material:
- What it is and its main purpose
- Key point from the material (no external knowledge)

Keep it brief and focused. Use terminology from the lesson material."""
            
            resp2 = self._call_ollama(prompt2, timeout=300)
            description = resp2.strip() if resp2 else "See content for details"
            print(f"[ContentParser]   Description length: {len(description)} chars")
            
            # Get detailed key points
            print(f"[ContentParser] STEP 3.{i+1}: Extracting key points for '{obj_title}'")
            prompt3 = f"""EXTRACT KEY POINTS. RESPOND IN ENGLISH.

CONCEPT: {obj_title}
DESCRIPTION: {description}

Extract 3-4 key points from the material that are most important:
["Point 1 - key detail from material", "Point 2 - key detail from material"]

Return ONLY JSON array of strings. Use only information from the provided text."""
            
            resp3 = self._call_ollama(prompt3, timeout=300)
            key_points = self._extract_json_from_response(resp3)
            if not isinstance(key_points, list):
                key_points = ["See content for key points"]
            print(f"[ContentParser]   Key points: {len(key_points)} extracted")
            
            # Get expanded keywords
            print(f"[ContentParser] STEP 4.{i+1}: Expanding keywords for '{obj_title}'")
            prompt4 = f"""EXTRACT KEYWORDS. RESPOND IN ENGLISH.

CONCEPT: {obj_title}
DESCRIPTION: {description}

Extract 3-5 relevant keywords and terms related to this concept that are mentioned in the material:
["keyword1", "keyword2", "keyword3"]

Return ONLY JSON array of strings. Use terminology from the lesson material."""
            
            resp4 = self._call_ollama(prompt4, timeout=300)
            keywords = self._extract_json_from_response(resp4)
            if not isinstance(keywords, list):
                keywords = obj.get('keywords', [])
            print(f"[ContentParser]   Keywords: {len(keywords)} extracted")
            
            # Build enriched object
            enriched = {
                'title': obj_title,
                'type': obj_type,
                'description': description,
                'key_points': key_points if isinstance(key_points, list) else ["See content for key points"],
                'keywords': keywords if isinstance(keywords, list) else obj.get('keywords', [])
            }
            
            enriched_objects.append(enriched)
        
        print(f"[ContentParser] ENRICHMENT COMPLETE: {len(enriched_objects)} learning objects fully enriched")
        return enriched_objects
    
    def extract_ontology_relationships(self, content: str, learning_objects: List[Dict], lesson_title: str) -> List[Dict]:
        """
        Extract COMPREHENSIVE relationships between learning objects using multiple prompts
        """
        if not learning_objects:
            print("[ContentParser] No learning objects to relate")
            return []
        
        lo_titles = [lo.get("title", lo.get("name", "")) for lo in learning_objects]
        all_relationships = []
        
        # First prompt: Prerequisites and dependencies
        print("[ContentParser] Analyzing prerequisite relationships...")
        prompt1 = f"""FIND PREREQUISITE RELATIONSHIPS. RESPOND IN ENGLISH.

LESSON: {lesson_title}
LEARNING OBJECTS: {', '.join(lo_titles[:15])}

Find which concepts are prerequisites for others. For each:
[
  {{"source": "Object A", "target": "Object B", "type": "prerequisite", "description": "Why A must be understood first"}}
]

Return ONLY JSON array."""
        
        resp1 = self._call_ollama(prompt1, timeout=300)
        if resp1:
            rels1 = self._extract_json_from_response(resp1)
            if isinstance(rels1, list):
                all_relationships.extend(rels1)
                print(f"[ContentParser] Found {len(rels1)} prerequisite relationships")
        
        # Second prompt: Related and related_to relationships
        print("[ContentParser] Analyzing related concepts...")
        prompt2 = f"""FIND RELATED CONCEPTS. RESPOND IN ENGLISH.

LESSON: {lesson_title}
OBJECTS: {', '.join(lo_titles[:15])}

Find concepts that are related, build upon each other, or explain each other:
[
  {{"source": "A", "target": "B", "type": "related", "description": "How they connect"}},
  {{"source": "A", "target": "C", "type": "builds_upon", "description": "How A builds on C"}},
  {{"source": "D", "target": "E", "type": "explains", "description": "How D explains E"}}
]

Return ONLY JSON array."""
        
        resp2 = self._call_ollama(prompt2, timeout=300)
        if resp2:
            rels2 = self._extract_json_from_response(resp2)
            if isinstance(rels2, list):
                all_relationships.extend(rels2)
                print(f"[ContentParser] Found {len(rels2)} related relationships")
        
        # Third prompt: Part-of and exemplification relationships
        print("[ContentParser] Analyzing hierarchical relationships...")
        prompt3 = f"""FIND HIERARCHICAL RELATIONSHIPS. RESPOND IN ENGLISH.

LESSON: {lesson_title}
OBJECTS: {', '.join(lo_titles[:15])}

Find part-of, instance-of, and exemplification relationships:
[
  {{"source": "Component", "target": "Whole", "type": "part_of", "description": "Why component is part of whole"}},
  {{"source": "Example", "target": "Concept", "type": "instance_of", "description": "How example illustrates concept"}},
  {{"source": "Concept", "target": "Example", "type": "exemplifies", "description": "Concept exemplified by example"}}
]

Return ONLY JSON array."""
        
        resp3 = self._call_ollama(prompt3, timeout=300)
        if resp3:
            rels3 = self._extract_json_from_response(resp3)
            if isinstance(rels3, list):
                all_relationships.extend(rels3)
                print(f"[ContentParser] Found {len(rels3)} hierarchical relationships")
        
        print(f"[ContentParser] Total relationships found: {len(all_relationships)}")
        return all_relationships
    
    def generate_lesson_summary(self, content: str, lesson_title: str) -> str:
        """
        Generate a comprehensive summary of the lesson
        
        Args:
            content: Full lesson content
            lesson_title: Title of the lesson
            
        Returns:
            Summary text
        """
        prompt = f"""TASK: Write a comprehensive summary of this lesson.

LESSON TITLE: {lesson_title}

CONTENT:
{content[:2500]}

INSTRUCTIONS:
Write a detailed 3-5 paragraph summary that covers:
1. Main topic and purpose of the lesson
2. Key concepts and important ideas
3. How these concepts relate to each other
4. Practical implications or applications
5. Main takeaways for students

Make it educational, clear, and informative."""
        
        print("[ContentParser] Generating summary...")
        summary = self._call_ollama(prompt, timeout=300)
        
        return summary or f"Summary of {lesson_title}"


# Create global instance
content_parser = ContentParser()
