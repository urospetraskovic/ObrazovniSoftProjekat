"""
Content Parser Module - Local Ollama Version
Extracts sections and learning objects from PDF lesson content using local LLM (Ollama)

MAXIMUM QUALITY VERSION:
- Multi-pass extraction for comprehensive section coverage
- No concern for API costs - running locally
- Splits content into chunks for thorough analysis
- Extracts MORE sections and learning objects
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
    
    MAXIMUM QUALITY APPROACH:
    - Splits content into smaller chunks
    - Does multiple passes over content
    - Extracts MORE sections (6-15 instead of 2-5)
    - No concern for time - quality is the priority
    """
    
    def __init__(self):
        """Initialize the content parser with Ollama configuration"""
        self.ollama_base_url = OLLAMA_BASE_URL
        self.ollama_model = OLLAMA_MODEL
        self.provider = "ollama"
        
        print(f"[ContentParser] Initialized with Ollama (14B model for maximum quality)")
        print(f"[ContentParser] Model: {self.ollama_model}")
        print(f"[ContentParser] Server: {self.ollama_base_url}")
        print(f"[ContentParser] Mode: MAXIMUM QUALITY - multi-pass extraction")
        
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
    
    def extract_pdf_text_from_stream(self, stream) -> Dict[str, Any]:
        """
        Extract text from PDF file stream (without saving to disk)
        
        Args:
            stream: File stream object
            
        Returns:
            Dictionary with 'content' and metadata
        """
        try:
            pdf_reader = PdfReader(stream)
            text_content = ""
            
            for page_num, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                text_content += f"\n--- Page {page_num + 1} ---\n{text}"
            
            return {
                "success": True,
                "content": text_content,
                "full_text": text_content,
                "pages": len(pdf_reader.pages),
                "filepath": None
            }
            
        except Exception as e:
            print(f"[ContentParser] PDF extraction error: {e}")
            return {
                "success": False,
                "error": str(e),
                "filepath": None
            }
    
    def parse_lesson_structure(self, content: str, lesson_title: str) -> List[Dict[str, Any]]:
        """
        Parse lesson content into sections with learning objects.
        
        OPTIMIZED FOR MEMORY: Single-pass analysis to reduce RAM usage.
        
        Args:
            content: Full lesson content
            lesson_title: Title of the lesson
            
        Returns:
            List of section dictionaries with learning objects
        """
        print(f"\n[ContentParser] === MEMORY-OPTIMIZED PARSING ===")
        print(f"[ContentParser] Content length: {len(content)} characters")
        
        # Split content into smaller chunks (reduced from 3000 to 2000 chars per chunk)
        chunks = self._split_content_into_chunks(content, chunk_size=2000, overlap=200)
        print(f"[ContentParser] Split into {len(chunks)} chunks (smaller chunks for memory efficiency)")
        
        all_sections = []
        
        # Single pass: Analyze each chunk for sections
        for i, chunk in enumerate(chunks):
            print(f"\n[ContentParser] --- Analyzing chunk {i+1}/{len(chunks)} ---")
            chunk_sections = self._extract_sections_from_chunk(chunk, lesson_title, i+1, len(chunks))
            if chunk_sections:
                all_sections.extend(chunk_sections)
                print(f"[ContentParser] Chunk {i+1}: Found {len(chunk_sections)} sections")
        
        # Merge and deduplicate sections
        print(f"\n[ContentParser] Merging {len(all_sections)} sections...")
        merged_sections = self._merge_similar_sections(all_sections)
        print(f"[ContentParser] After merge: {len(merged_sections)} unique sections")
        
        # Limit sections to reasonable amount (allow natural number, max 15 to prevent excessive sections)
        if len(merged_sections) > 15:
            print(f"[ContentParser] Limiting to 15 sections (was {len(merged_sections)}) - too many redundant sections")
            merged_sections = merged_sections[:15]
        
        # If too few sections, extract from full content once
        if len(merged_sections) < 2:
            print(f"[ContentParser] Too few sections, extracting from full content...")
            merged_sections = self._extract_comprehensive_sections(content[:5000], lesson_title)
        
        # Assign section numbers
        for i, section in enumerate(merged_sections):
            section['section_number'] = i + 1
            section['id'] = i + 1
        
        # Extract learning objects for each section
        print(f"\n[ContentParser] Extracting learning objects for {len(merged_sections)} sections...")
        for section in merged_sections:
            section_title = section.get('title', f"Section {section.get('section_number', 1)}")
            key_topics = section.get('key_topics', [])
            
            # Get content relevant to this section
            section_content = self._extract_section_content(content, " ".join(key_topics), section_title)
            
            # Extract learning objects (reduced from 5-12 to 3-6)
            learning_objects = self._extract_learning_objects(
                section_content,
                section_title,
                lesson_title
            )
            
            section['learning_objects'] = learning_objects
            print(f"[ContentParser] Section '{section_title}': {len(learning_objects)} learning objects")
        
        print(f"\n[ContentParser] === PARSING COMPLETE ===")
        print(f"[ContentParser] Total sections: {len(merged_sections)}")
        total_los = sum(len(s.get('learning_objects', [])) for s in merged_sections)
        print(f"[ContentParser] Total learning objects: {total_los}")
        
        return merged_sections
    
    def _split_content_into_chunks(self, content: str, chunk_size: int = 3000, overlap: int = 400) -> List[str]:
        """
        Split content into overlapping chunks for analysis.
        BALANCED: Larger chunks (3000 chars) for better extraction while avoiding huge frontload.
        """
        chunks = []
        content_len = len(content)
        
        if content_len <= chunk_size:
            return [content]
        
        # Allow more chunks for better extraction
        max_chunks = 10
        
        start = 0
        chunk_count = 0
        while start < content_len and chunk_count < max_chunks:
            end = min(start + chunk_size, content_len)
            chunk = content[start:end]
            
            # Try to end at a paragraph break for cleaner chunks
            if end < content_len:
                last_break = chunk.rfind('\n\n')
                if last_break > chunk_size // 2:
                    chunk = chunk[:last_break]
                    end = start + last_break
            
            chunks.append(chunk)
            start = end - overlap
            chunk_count += 1
            
            if start >= content_len:
                break
        
        return chunks
    
    def _extract_sections_from_chunk(self, chunk: str, lesson_title: str, chunk_num: int, total_chunks: int) -> List[Dict]:
        """Extract sections from a single chunk with ENHANCED multi-level analysis"""
        
        # LEVEL 1: Identify major sections
        prompt_l1 = f"""You are an expert educational content analyst. Analyze this PART of a lesson and identify ALL distinct topics and sections.

LESSON: {lesson_title}
PART {chunk_num} OF {total_chunks}

CONTENT:
{chunk}

CRITICAL INSTRUCTIONS:
1. Identify EVERY distinct topic, subtopic, and theme in this content
2. Be thorough and granular - identify 5-12 sections
3. Each section represents a specific concept, topic, or theme area
4. Look for: definitions, processes, components, techniques, concepts, relationships, examples
5. **ALL TITLES MUST BE IN ENGLISH** - translate from any other language
6. Include implicit topics, not just explicitly stated section headers
7. Look for patterns: "Introduction to X", "Types of Y", "Process of Z", "Characteristics of W"

OUTPUT FORMAT (JSON array):
[
  {{"title": "Specific Topic Name (IN ENGLISH)", "key_topics": ["keyword1", "keyword2", "keyword3"]}},
  {{"title": "Another Topic (IN ENGLISH)", "key_topics": ["keywordA", "keywordB"]}}
]

Return ONLY the JSON array with 5-12 sections. Find ALL distinct sections. REMEMBER: ALL TITLES IN ENGLISH."""
        
        print(f"[ContentParser] [SECTION EXTRACTION] Analyzing chunk {chunk_num}/{total_chunks}...")
        response_l1 = self._call_ollama(prompt_l1, timeout=150)
        sections = self._extract_json_from_response(response_l1) if response_l1 else []
        
        if not isinstance(sections, list):
            sections = []
        
        print(f"[ContentParser] Level 1 found {len(sections)} initial sections")
        
        # LEVEL 2: Validate and enrich sections with context
        if len(sections) > 0:
            sections_str = ", ".join([s.get('title', '') for s in sections[:10]])
            
            prompt_l2 = f"""Validate and enrich these sections identified from "{lesson_title}":

SECTIONS: {sections_str}

CONTENT SNIPPET:
{chunk[:1500]}

---

For each section, determine:
1. Importance level: [foundational, core, supporting, advanced]
2. Related_sections: Which other identified sections relate to this one
3. Learning_prerequisites: What must be known before understanding this
4. Subtopics: 2-4 subtopics or related concepts within this section

Return ONLY JSON array:
[{{"title": "SectionName", "importance": "...", "related_sections": [...], "learning_prerequisites": [...], "subtopics": [...]}}]"""
            
            response_l2 = self._call_ollama(prompt_l2, timeout=120)
            enriched = self._extract_json_from_response(response_l2) if response_l2 else {}
            
            if isinstance(enriched, list):
                for section in sections:
                    for enrich_data in enriched:
                        if enrich_data.get('title', '').lower() == section.get('title', '').lower():
                            section['importance'] = enrich_data.get('importance', 'core')
                            section['related_sections'] = enrich_data.get('related_sections', [])
                            section['learning_prerequisites'] = enrich_data.get('learning_prerequisites', [])
                            section['subtopics'] = enrich_data.get('subtopics', [])
                            break
            
            print(f"[ContentParser] Level 2 enriched sections with context")
        
        # LEVEL 3: Gap detection - look for missing sections
        if len(sections) < 4:
            print(f"[ContentParser] Level 3 gap detection - found only {len(sections)} sections, looking for more...")
            
            prompt_l3 = f"""This chunk appears to have limited sections. Are there any major topics or concepts NOT in this list?

IDENTIFIED: {", ".join([s.get('title', '') for s in sections])}

CONTENT:
{chunk[:2000]}

---

List any significant topics, concepts, or sections that should be added. Be thorough.

Return ONLY JSON:
{{"additional_sections": [{{\"title\": \"...\", \"key_topics\": [...]}}]}}"""
            
            response_l3 = self._call_ollama(prompt_l3, timeout=120)
            additional = self._extract_json_from_response(response_l3) if response_l3 else {}
            
            if isinstance(additional, dict) and additional.get('additional_sections'):
                for add_section in additional.get('additional_sections', [])[:3]:
                    if add_section.get('title'):
                        sections.append(add_section)
                
                print(f"[ContentParser] Level 3 added {len(additional.get('additional_sections', []))} missing sections")
        
        # Return all found sections (up to 12 per chunk naturally)
        return sections[:12]
    
    def _merge_similar_sections(self, sections: List[Dict]) -> List[Dict]:
        """Merge sections that are too similar to avoid duplication"""
        if not sections:
            return []
        
        merged = []
        used = set()
        
        for i, section in enumerate(sections):
            if i in used:
                continue
            
            title = section.get('title', '').lower()
            topics = set(t.lower() for t in section.get('key_topics', []))
            
            # Find similar sections to merge with
            similar_topics = list(section.get('key_topics', []))
            
            for j, other in enumerate(sections[i+1:], start=i+1):
                if j in used:
                    continue
                
                other_title = other.get('title', '').lower()
                other_topics = set(t.lower() for t in other.get('key_topics', []))
                
                # Check multiple similarity metrics
                # 1. Title word overlap
                title_words = set(title.split())
                other_title_words = set(other_title.split())
                
                title_similarity = 0.0
                if len(title_words) > 0 and len(other_title_words) > 0:
                    title_similarity = len(title_words.intersection(other_title_words)) / max(len(title_words), len(other_title_words))
                
                # 2. Topic overlap (if any topics are the same, likely duplicates)
                topic_similarity = 0.0
                if len(topics) > 0 and len(other_topics) > 0:
                    topic_similarity = len(topics.intersection(other_topics)) / min(len(topics), len(other_topics))
                
                # 3. Combined score (title similarity matters more)
                combined_score = (title_similarity * 0.7) + (topic_similarity * 0.3)
                
                # More aggressive merging: 50% combined similarity OR >70% title similarity
                should_merge = (combined_score > 0.5) or (title_similarity > 0.7) or (topic_similarity > 0.6)
                
                if should_merge:
                    used.add(j)
                    similar_topics.extend(other.get('key_topics', []))
                    print(f"[ContentParser] Merging similar sections (score={combined_score:.2f}):")
                    print(f"  - '{section.get('title')}' + '{other.get('title')}'")
            
            # Remove duplicate topics
            unique_topics = list(dict.fromkeys(similar_topics))
            
            merged.append({
                'title': section.get('title', ''),
                'key_topics': unique_topics[:10]  # Limit topics
            })
        
        print(f"[ContentParser] After merging: {len(merged)} sections (was {len(sections)})")
        return merged
    
    def _extract_comprehensive_sections(self, content: str, lesson_title: str) -> List[Dict]:
        """Fallback: Extract sections with comprehensive prompt"""
        
        prompt = f"""You are an expert educational content analyst. Extract ALL main topics and sections from this content.

LESSON: {lesson_title}

CONTENT:
{content[:6000]}

FIND AND LIST all distinct topics and sections. Include:
1. Major topic areas
2. Important subtopics
3. Key concepts and definitions
4. Processes and procedures
5. Components and elements

CRITICAL: **ALL SECTION TITLES MUST BE IN ENGLISH**
- Translate from Serbian, Croatian, or any other language
- Use clear English titles for all sections
- Examples: "Definition of Processes" NOT "Pojam Procesa", "Process Elements" NOT "Elementi Procesa"

JSON array format:
[
  {{"title": "Specific Topic Name (IN ENGLISH)", "key_topics": ["keyword1", "keyword2", "keyword3"]}},
  {{"title": "Another Topic (IN ENGLISH)", "key_topics": ["keywordA", "keywordB"]}}
]

Return ONLY the JSON array with 5-15 natural sections (only include if meaningful). ALL TITLES IN ENGLISH."""
        
        response = self._call_ollama(prompt, timeout=120)
        
        if not response:
            return [{"title": lesson_title, "key_topics": []}]
        
        sections = self._extract_json_from_response(response)
        if isinstance(sections, list) and len(sections) > 0:
            return sections[:15]  # Allow up to 15 sections naturally
        
        return [{"title": lesson_title, "key_topics": []}]
    
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
        Extract educational learning objects with ENHANCED QUALITY multi-pass analysis.
        
        ENHANCEMENT: Uses 3-pass extraction for comprehensive coverage:
        1. Primary extraction: Get main concepts
        2. Relationship analysis: Find connections and prerequisites
        3. Quality refinement: Ensure completeness and accuracy
        """
        content_preview = section_content[:3000].strip()  # Increased from 2000
        
        # PASS 1: Primary extraction with comprehensive prompt
        print(f"[ContentParser] [PASS 1] Extracting core learning objects from: {section_title}")
        prompt_pass1 = f"""You are an expert educational content analyst. Extract ALL key learning objects from this section.

LESSON: {lesson_title}
SECTION: {section_title}

CONTENT:
{content_preview}

---

EXTRACTION GUIDELINES:
1. Identify EVERY distinct concept, term, process, or principle mentioned
2. Extract only UNIQUE, VALUABLE objects - NO forced or duplicate concepts
3. Include: definitions, key concepts, processes, principles, examples, components
4. Look for implicit concepts, not just explicitly stated ones
5. Quality over quantity - better 4 excellent objects than 10 mediocre ones
6. ALL OUTPUT MUST BE IN ENGLISH (translate if needed)

For each object, provide:
- title: Clear name (3-8 words, IN ENGLISH)
- type: One of [concept, definition, process, principle, component, example, technique, structure]
- description: 2-4 sentences, comprehensive explanation
- key_points: 2-4 important facts or characteristics
- keywords: 3-6 related search terms (IN ENGLISH)

Return ONLY a valid JSON array with ALL distinct important objects (natural number, not forced):
[{{"title": "...", "type": "...", "description": "...", "key_points": [...], "keywords": [...]}}]"""
        
        response_pass1 = self._call_ollama(prompt_pass1, timeout=180)
        objects_pass1 = self._extract_json_from_response(response_pass1) if response_pass1 else []
        
        if not isinstance(objects_pass1, list):
            objects_pass1 = []
        
        print(f"[ContentParser] [PASS 1] Found {len(objects_pass1)} initial objects")
        
        # PASS 2: Relationship and context analysis
        print(f"[ContentParser] [PASS 2] Analyzing relationships and prerequisites...")
        if len(objects_pass1) > 0:
            titles_str = ", ".join([obj.get('title', '') for obj in objects_pass1[:10]])
            
            prompt_pass2 = f"""Analyze these concepts from "{section_title}" and enhance them with relationship information.

EXTRACTED CONCEPTS: {titles_str}

SECTION CONTENT:
{content_preview[:2000]}

---

For each concept listed, add:
1. Prerequisites: What concepts must be understood first
2. Related_concepts: Connected or similar concepts
3. Learning_outcomes: What should students be able to do after learning this
4. Common_misconceptions: Typical student misunderstandings (if applicable)
5. Real_world_applications: Practical uses or examples (if applicable)

Return ONLY a JSON array with enhanced details:
[{{"title": "ConceptName", "prerequisites": [...], "related_concepts": [...], "learning_outcomes": [...], "common_misconceptions": [...], "real_world_applications": [...]}}]"""
            
            response_pass2 = self._call_ollama(prompt_pass2, timeout=180)
            relationships = self._extract_json_from_response(response_pass2) if response_pass2 else {}
            
            # Merge relationship data into objects
            if isinstance(relationships, list):
                for obj in objects_pass1:
                    for rel_data in relationships:
                        if rel_data.get('title', '').lower() == obj.get('title', '').lower():
                            obj['prerequisites'] = rel_data.get('prerequisites', [])
                            obj['related_concepts'] = rel_data.get('related_concepts', [])
                            obj['learning_outcomes'] = rel_data.get('learning_outcomes', [])
                            obj['common_misconceptions'] = rel_data.get('common_misconceptions', [])
                            obj['real_world_applications'] = rel_data.get('real_world_applications', [])
                            break
        
        print(f"[ContentParser] [PASS 2] Enhanced with relationship data")
        
        # PASS 3: Quality check and gap filling
        print(f"[ContentParser] [PASS 3] Quality verification and gap analysis...")
        
        if len(objects_pass1) > 2:
            # Ask AI to identify any missing concepts
            prompt_pass3 = f"""Review the extracted concepts for "{section_title}" and identify ANY important concepts we missed.

EXTRACTED: {", ".join([obj.get('title', '') for obj in objects_pass1[:8]])}

ORIGINAL CONTENT:
{content_preview[:2500]}

---

Are there important concepts, definitions, or principles NOT in the extracted list? 
List any MISSING key concepts that should be included.

Return ONLY a JSON object with missing concepts (or empty array if complete):
{{"missing_concepts": [{{\"title\": \"...\", \"description\": \"...\", \"type\": \"...\"}}]}}"""
            
            response_pass3 = self._call_ollama(prompt_pass3, timeout=150)
            missing = self._extract_json_from_response(response_pass3) if response_pass3 else {}
            
            if isinstance(missing, dict) and missing.get('missing_concepts'):
                for missing_obj in missing.get('missing_concepts', [])[:3]:  # Add up to 3 missing
                    if missing_obj.get('title'):
                        objects_pass1.append({
                            'title': missing_obj.get('title', 'Unknown')[:150],
                            'type': missing_obj.get('type', 'concept'),
                            'description': missing_obj.get('description', '')[:600],
                            'key_points': [],
                            'keywords': []
                        })
            
            print(f"[ContentParser] [PASS 3] Added {len(missing.get('missing_concepts', []))} missing concepts")
        
        # Validate and clean all objects
        validated_objects = []
        seen_titles = set()
        
        for obj in objects_pass1:
            if not obj.get('title'):
                continue
            
            title_lower = obj.get('title', '').lower()
            if title_lower in seen_titles:
                continue
            seen_titles.add(title_lower)
            
            validated = {
                'title': obj.get('title', 'Unknown')[:150],
                'type': obj.get('type', 'concept'),
                'description': obj.get('description', '')[:600],
                'key_points': obj.get('key_points', []) if isinstance(obj.get('key_points'), list) else [],
                'keywords': obj.get('keywords', [])[:6] if isinstance(obj.get('keywords'), list) else [],
                'prerequisites': obj.get('prerequisites', []) if isinstance(obj.get('prerequisites'), list) else [],
                'related_concepts': obj.get('related_concepts', []) if isinstance(obj.get('related_concepts'), list) else [],
                'learning_outcomes': obj.get('learning_outcomes', []) if isinstance(obj.get('learning_outcomes'), list) else [],
            }
            validated_objects.append(validated)
        
        # Limit to 12 max (but keep all that were found)
        if len(validated_objects) > 12:
            validated_objects = validated_objects[:12]
        
        print(f"[ContentParser] [FINAL] Extracted {len(validated_objects)} high-quality learning objects (quality-focused extraction)")
        return validated_objects
    
    def _extract_learning_objects_simple(self, section_content: str, section_title: str, lesson_title: str) -> List[Dict]:
        """Simpler fallback for learning object extraction"""
        content_preview = section_content[:1500].strip()
        
        prompt = f"""Extract 5-8 key concepts from this educational content.

LESSON: {lesson_title}
SECTION: {section_title}

CONTENT:
{content_preview}

For each concept provide (JSON array):
- title: Concept name (MUST BE IN ENGLISH)
- type: One of [concept, definition, process, component]
- description: 2-3 sentence explanation (MUST BE IN ENGLISH)
- keywords: 3-4 related terms (MUST BE IN ENGLISH)

Extract 5-8 distinct concepts. Return ONLY JSON array."""
        
        response = self._call_ollama(prompt, timeout=120)
        if not response:
            return []
        
        objects = self._extract_json_from_response(response)
        if isinstance(objects, list):
            return [{'title': o.get('title', ''), 'type': o.get('type', 'concept'), 
                     'description': o.get('description', ''), 'key_points': o.get('key_points', []), 
                     'keywords': o.get('keywords', [])} for o in objects if o.get('title')][:8]
        return []
    
    def extract_ontology_relationships(self, content: str, learning_objects: List[Dict], lesson_title: str) -> List[Dict]:
        """
        Extract meaningful relationships between learning objects.
        Focus on quality educational connections WITH PROPER TAXONOMIC HIERARCHY.
        
        IMPROVED: Better fallback if AI extraction fails or times out.
        """
        if not learning_objects:
            print("[ContentParser] No learning objects to relate")
            return []
        
        # Build descriptions for ALL learning objects
        lo_descriptions = []
        all_lo_titles = []
        
        for lo in learning_objects:
            title = lo.get("title", lo.get("name", ""))
            desc = lo.get("description", "")[:80]
            type_str = lo.get("type", lo.get("object_type", "concept"))
            lo_descriptions.append(f"- {title} ({type_str}): {desc}")
            all_lo_titles.append(title)
        
        lo_context = "\n".join(lo_descriptions[:50])
        
        # Enhanced prompt for TAXONOMIC HIERARCHY and rich ontology structure
        prompt = f"""You are an expert in educational ONTOLOGY and KNOWLEDGE REPRESENTATION. Your task is to create a RICH TAXONOMIC STRUCTURE from these learning objects.

LESSON: {lesson_title}

LEARNING OBJECTS ({len(all_lo_titles)} total):
{lo_context}

---

YOUR TASK: Create a COMPREHENSIVE ONTOLOGY with THREE types of relationships:

## 1. HIERARCHICAL/TAXONOMIC RELATIONSHIPS (MOST IMPORTANT!)
These create a proper class hierarchy (SubClassOf in OWL):
- part_of: "A is a component/part of B"
- is_type_of: "A is a specific type/kind of B"
- is_subclass_of: "A is a subcategory of B"

## 2. PREREQUISITE/LEARNING ORDER RELATIONSHIPS
- prerequisite: "A must be learned before B"
- builds_upon: "A extends or elaborates on B"
- enables: "A makes B possible"

## 3. SEMANTIC RELATIONSHIPS
- related_to, contrasts_with, implements, uses, defines, is_example_of

---

CRITICAL REQUIREMENTS:
1. CREATE AT LEAST 3-5 HIERARCHICAL relationships - ESSENTIAL for ontology!
2. Use EXACT titles from the learning objects list
3. Each relationship needs: source, target, type, description
4. Return as many relationships as possible (15-40+ is normal)

EXAMPLE OUTPUT:
[
  {{"source": "A Concept", "target": "B Concept", "type": "part_of", "description": "A is part of B"}},
  {{"source": "Specific Term", "target": "General Term", "type": "is_type_of", "description": "Specific is a type of General"}}
]

Return ONLY valid JSON array. No markdown, no explanations."""
        
        print("[ContentParser] Extracting ontology relationships (15 minute timeout for comprehensive analysis)...")
        print(f"[ContentParser] Analyzing {len(all_lo_titles)} learning objects for hierarchical connections...")
        
        # Try to extract relationships with 15-minute timeout
        response = self._call_ollama(prompt, timeout=900)
        
        if not response:
            print("[ContentParser] WARNING: Ontology extraction timed out or failed")
            print("[ContentParser] Generating basic relationships from learning object structure...")
            # Return basic relationships based on learning object structure
            return self._generate_fallback_relationships(all_lo_titles, learning_objects)
        
        relationships = self._extract_json_from_response(response)
        if not isinstance(relationships, list) or len(relationships) == 0:
            print("[ContentParser] No relationships extracted from AI response")
            print("[ContentParser] Generating basic relationships from learning object structure...")
            return self._generate_fallback_relationships(all_lo_titles, learning_objects)
        
        valid_relationships = self._validate_relationships(relationships, all_lo_titles)
        print(f"[ContentParser] Found {len(valid_relationships)} valid relationships out of {len(relationships)} extracted")
        
        # If very few relationships, augment with fallback
        if len(valid_relationships) < 3:
            print("[ContentParser] Very few relationships found, augmenting with fallback relationships...")
            fallback = self._generate_fallback_relationships(all_lo_titles, learning_objects)
            valid_relationships.extend(fallback)
        
        return valid_relationships
    
    def _generate_fallback_relationships(self, all_lo_titles: List[str], learning_objects: List[Dict]) -> List[Dict]:
        """
        Generate basic relationships when AI extraction fails.
        Based on learning object types and ordering.
        """
        relationships = []
        
        # Strategy 1: Create prerequisites based on ordering
        for i in range(len(all_lo_titles) - 1):
            source = all_lo_titles[i]
            target = all_lo_titles[i + 1]
            if source and target and source != target:
                relationships.append({
                    "source": source,
                    "target": target,
                    "type": "prerequisite",
                    "description": f"{source} is typically learned before {target}"
                })
        
        # Strategy 2: Group by type and create hierarchies
        type_groups = {}
        for lo in learning_objects:
            obj_type = lo.get('type', lo.get('object_type', 'concept')).lower()
            if obj_type not in type_groups:
                type_groups[obj_type] = []
            type_groups[obj_type].append(lo.get('title', ''))
        
        # For each type group with multiple items, create part_of relationships
        for obj_type, titles in type_groups.items():
            if len(titles) > 1:
                # The first one is the parent/general concept
                parent = titles[0]
                for child in titles[1:]:
                    if parent and child and parent != child:
                        relationships.append({
                            "source": child,
                            "target": parent,
                            "type": "part_of",
                            "description": f"{child} is part of or related to {parent}"
                        })
        
        # Strategy 3: Create related_to for adjacent concepts
        for i in range(len(all_lo_titles)):
            for j in range(i + 1, min(i + 3, len(all_lo_titles))):
                source = all_lo_titles[i]
                target = all_lo_titles[j]
                if source and target and source != target:
                    # Check if this relationship doesn't already exist
                    exists = any(r['source'] == source and r['target'] == target for r in relationships)
                    if not exists:
                        relationships.append({
                            "source": source,
                            "target": target,
                            "type": "related_to",
                            "description": f"{source} is related to {target}"
                        })
        
        print(f"[ContentParser] Generated {len(relationships)} fallback relationships")
        return relationships
    
    def _validate_relationships(self, relationships: List[Dict], all_lo_titles: List[str]) -> List[Dict]:
        """Validate relationships and match against learning object titles"""
        valid_relationships = []
        title_set = set(all_lo_titles)
        
        # Create normalized mapping
        normalized_to_original = {}
        for title in all_lo_titles:
            normalized = title.strip().lower()
            normalized_to_original[normalized] = title
        
        def clean_title(title):
            """Remove type metadata like (concept), (definition), etc"""
            cleaned = re.sub(r'\s*\([^)]*\)\s*$', '', title).strip()
            return cleaned
        
        for rel in relationships:
            source = rel.get("source", "").strip()
            target = rel.get("target", "").strip()
            
            source_clean = clean_title(source)
            target_clean = clean_title(target)
            
            # Try exact match first
            if source_clean in title_set and target_clean in title_set and source_clean != target_clean:
                rel["source"] = source_clean
                rel["target"] = target_clean
                valid_relationships.append(rel)
            else:
                # Try fuzzy matching (normalized comparison)
                source_normalized = source_clean.lower()
                target_normalized = target_clean.lower()
                
                if source_normalized in normalized_to_original and target_normalized in normalized_to_original:
                    rel["source"] = normalized_to_original[source_normalized]
                    rel["target"] = normalized_to_original[target_normalized]
                    if rel["source"] != rel["target"]:
                        valid_relationships.append(rel)
        
        return valid_relationships
# Create global instance
content_parser = ContentParser()
