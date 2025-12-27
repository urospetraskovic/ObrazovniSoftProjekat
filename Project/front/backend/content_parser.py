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
        """Extract sections from a single chunk of content with better prompts"""
        
        prompt = f"""You are an expert educational content analyst. Analyze this PART of a lesson and identify all distinct topics and sections.

LESSON: {lesson_title}
PART {chunk_num} OF {total_chunks}

CONTENT:
{chunk}

CRITICAL INSTRUCTIONS:
1. Identify ALL distinct topics, subtopics, and themes in this content
2. Each section should represent a specific concept or topic area
3. Be granular - prefer multiple focused sections over few large ones
4. Look for: definitions, processes, components, techniques, concepts
5. **ALL TITLES MUST BE IN ENGLISH** - translate from any other language
6. Do NOT use Serbian, Croatian, or any other language for section titles
7. Examples: "Definition of Process" NOT "Pojam Procesa", "Process States" NOT "Stanja Procesa"

OUTPUT FORMAT (JSON array):
[
  {{"title": "Specific Topic Name (IN ENGLISH)", "key_topics": ["keyword1", "keyword2", "keyword3"]}},
  {{"title": "Another Topic (IN ENGLISH)", "key_topics": ["keywordA", "keywordB"]}}
]

Return ONLY the JSON array. Find all distinct sections in this content. REMEMBER: ALL TITLES IN ENGLISH."""
        
        response = self._call_ollama(prompt, timeout=120)
        
        if not response:
            return []
        
        sections = self._extract_json_from_response(response)
        if isinstance(sections, list):
            return sections[:8]  # Allow up to 8 sections per chunk naturally
        return []
    
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
        Extract educational learning objects with balanced quality and memory.
        
        BALANCED: Extracts 5-8 learning objects per section.
        """
        # Use larger content preview for better context
        content_preview = section_content[:2000].strip()
        
        # Balanced prompt with better English instructions and focus on quality
        prompt = f"""You are an educational content expert. Extract 5-8 key learning objects from this educational content.

LESSON: {lesson_title}
SECTION: {section_title}

CONTENT:
{content_preview}

---

For each concept, provide (JSON array format):
- title: Clear concept name (3-8 words, MUST BE IN ENGLISH)
- type: One of [concept, definition, process, principle, component, technique]
- description: 2-3 sentence clear explanation (MUST BE IN ENGLISH)
- key_points: 1-3 important facts or details
- keywords: 2-5 related search terms (MUST BE IN ENGLISH)

IMPORTANT REQUIREMENTS:
1. Extract 4-8 distinct, important concepts
2. ALL OUTPUT MUST BE IN ENGLISH (translate if source is not English)
3. Each object must be unique and valuable for learning
4. Include all key concepts mentioned in the content
5. Return ONLY a valid JSON array, no other text

Example format:
[{{"title": "Concept Name", "type": "concept", "description": "Description here. More details about it.", "key_points": ["Point 1", "Point 2"], "keywords": ["key1", "key2", "key3"]}}]
"""
        
        print(f"[ContentParser] Extracting learning objects from: {section_title}")
        response = self._call_ollama(prompt, timeout=150)
        
        if not response:
            print("[ContentParser] No response from Ollama")
            return []
        
        objects = self._extract_json_from_response(response)
        if not isinstance(objects, list) or len(objects) == 0:
            print("[ContentParser] No objects extracted, trying simple extraction...")
            return self._extract_learning_objects_simple(section_content, section_title, lesson_title)
        
        # Validate and clean the objects (limit to 8 max)
        validated_objects = []
        for obj in objects[:8]:  # Hard limit to 8 objects
            if not obj.get('title'):
                continue
                
            validated = {
                'title': obj.get('title', 'Unknown')[:150],
                'type': obj.get('type', 'concept'),
                'description': obj.get('description', '')[:600],
                'key_points': obj.get('key_points', []) if isinstance(obj.get('key_points'), list) else [],
                'keywords': obj.get('keywords', [])[:6] if isinstance(obj.get('keywords'), list) else []
            }
            validated_objects.append(validated)
        
        print(f"[ContentParser] Extracted {len(validated_objects)} learning objects")
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
        
        NOTE: This is computationally intensive. Timeout is set to 900 seconds (15 minutes)
        for local Ollama models. Increase if needed for slower hardware.
        """
        if not learning_objects:
            print("[ContentParser] No learning objects to relate")
            return []
        
        # Build descriptions for ALL learning objects (not just first 15)
        lo_descriptions = []
        all_lo_titles = []
        
        for lo in learning_objects:  # Use ALL learning objects
            title = lo.get("title", lo.get("name", ""))
            desc = lo.get("description", "")[:80]  # Shorter desc to fit more LOs
            type_str = lo.get("type", lo.get("object_type", "concept"))
            lo_descriptions.append(f"- {title} ({type_str}): {desc}")
            all_lo_titles.append(title)
        
        lo_context = "\n".join(lo_descriptions[:50])  # Show first 50 in prompt
        
        # Enhanced prompt for TAXONOMIC HIERARCHY and rich ontology structure
        prompt = f"""You are an expert in educational ONTOLOGY and KNOWLEDGE REPRESENTATION. Your task is to create a RICH TAXONOMIC STRUCTURE from these learning objects.

LESSON: {lesson_title}

LEARNING OBJECTS ({len(all_lo_titles)} total, showing first 50):
{lo_context}

---

YOUR TASK: Create a COMPREHENSIVE ONTOLOGY with THREE types of relationships:

## 1. HIERARCHICAL/TAXONOMIC RELATIONSHIPS (MOST IMPORTANT!)
These create a proper class hierarchy (SubClassOf in OWL):
- part_of: "A is a component/part of B" (e.g., "CPU part_of Computer")
- is_type_of: "A is a specific type/kind of B" (e.g., "Virtual Memory is_type_of Memory Management")
- is_subclass_of: "A is a subcategory of B" (e.g., "Process Scheduling is_subclass_of Operating System Functions")

## 2. PREREQUISITE/LEARNING ORDER RELATIONSHIPS
These show learning dependencies:
- prerequisite: "A must be learned before B" 
- builds_upon: "A extends or elaborates on B"
- enables: "A makes B possible or meaningful"

## 3. SEMANTIC RELATIONSHIPS
These show meaningful connections:
- related_to: "A and B are connected concepts"
- contrasts_with: "A differs from B in important ways"
- implements: "A is a concrete implementation of B"
- uses: "A uses or applies B"
- defines: "A provides the definition for B"
- is_example_of: "A is an example of B"

---

CRITICAL INSTRUCTIONS:
1. CREATE AT LEAST 3-5 HIERARCHICAL (part_of, is_type_of, is_subclass_of) relationships - these are ESSENTIAL for ontology structure!
2. Find general/abstract concepts that can be PARENTS of more specific concepts
3. Use EXACT titles from the learning objects list
4. Each relationship needs source, target, type, and a clear description
5. Return as many relationships as you can find (15-40+ is typical for good coverage)

EXAMPLE OUTPUT:
[
  {{"source": "Process State", "target": "Process Management", "type": "part_of", "description": "Process state tracking is a component of overall process management"}},
  {{"source": "Ready State", "target": "Process State", "type": "is_type_of", "description": "Ready state is a specific type of process state"}},
  {{"source": "Context Switch", "target": "Process Scheduling", "type": "implements", "description": "Context switching implements the mechanism for process scheduling"}},
  {{"source": "Process Definition", "target": "Process State", "type": "prerequisite", "description": "Understanding what a process is must come before understanding its states"}}
]

Return ONLY a JSON array with relationships. Be comprehensive!"""
        
        print("[ContentParser] Extracting ontology relationships with TAXONOMIC HIERARCHY (this may take 5-15 minutes)...")
        print(f"[ContentParser] Analyzing {len(all_lo_titles)} learning objects for hierarchical connections...")
        response = self._call_ollama(prompt, timeout=900)  # 900 seconds = 15 minutes
        
        if not response:
            print("[ContentParser] WARNING: Ontology extraction timed out or failed")
            print("[ContentParser] This is normal for complex lessons - try re-parsing with more timeout if needed")
            return []
        
        relationships = self._extract_json_from_response(response)
        if not isinstance(relationships, list):
            return []
        
        # Validate relationships - ensure source and target exist in ANY learning object
        valid_relationships = []
        title_set = set(all_lo_titles)  # Use ALL titles, not just first 15
        
        # Create a mapping for fuzzy matching (normalized titles to original titles)
        normalized_to_original = {}
        for title in all_lo_titles:
            normalized = title.strip().lower()
            normalized_to_original[normalized] = title
        
        def clean_title(title):
            """Remove type metadata like (concept), (definition), etc"""
            # Remove anything in parentheses
            cleaned = re.sub(r'\s*\([^)]*\)\s*$', '', title).strip()
            return cleaned
        
        for rel in relationships:
            source = rel.get("source", "").strip()
            target = rel.get("target", "").strip()
            
            # Remove type metadata (concept), (definition), etc
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
                    # Update relationship with exact titles
                    rel["source"] = normalized_to_original[source_normalized]
                    rel["target"] = normalized_to_original[target_normalized]
                    if rel["source"] != rel["target"]:
                        valid_relationships.append(rel)
        
        print(f"[ContentParser] Found {len(valid_relationships)} valid relationships out of {len(relationships)} extracted")
        return valid_relationships
# Create global instance
content_parser = ContentParser()
