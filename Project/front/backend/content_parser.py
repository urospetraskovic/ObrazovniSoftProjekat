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
        
        MAXIMUM QUALITY APPROACH:
        - Pass 1: Get high-level structure of entire document
        - Pass 2: Split content into chunks and extract detailed sections
        - Pass 3: Merge and deduplicate sections
        - Pass 4: Extract learning objects for each section
        
        Args:
            content: Full lesson content
            lesson_title: Title of the lesson
            
        Returns:
            List of section dictionaries with learning objects
        """
        print(f"\n[ContentParser] === MAXIMUM QUALITY PARSING ===")
        print(f"[ContentParser] Content length: {len(content)} characters")
        
        # Split content into chunks for thorough analysis
        chunks = self._split_content_into_chunks(content)
        print(f"[ContentParser] Split into {len(chunks)} chunks for analysis")
        
        all_sections = []
        
        # PASS 1: Analyze each chunk for sections
        for i, chunk in enumerate(chunks):
            print(f"\n[ContentParser] --- Analyzing chunk {i+1}/{len(chunks)} ---")
            chunk_sections = self._extract_sections_from_chunk(chunk, lesson_title, i+1, len(chunks))
            if chunk_sections:
                all_sections.extend(chunk_sections)
                print(f"[ContentParser] Chunk {i+1}: Found {len(chunk_sections)} sections")
        
        # PASS 2: Merge and deduplicate sections
        print(f"\n[ContentParser] Merging {len(all_sections)} raw sections...")
        merged_sections = self._merge_similar_sections(all_sections)
        print(f"[ContentParser] After merge: {len(merged_sections)} unique sections")
        
        # If we still have too few sections, try a fallback approach
        if len(merged_sections) < 3:
            print(f"[ContentParser] Too few sections, trying comprehensive analysis...")
            merged_sections = self._extract_comprehensive_sections(content, lesson_title)
        
        # Assign section numbers
        for i, section in enumerate(merged_sections):
            section['section_number'] = i + 1
            section['id'] = i + 1
        
        # PASS 3: Extract learning objects for each section
        print(f"\n[ContentParser] Extracting learning objects for {len(merged_sections)} sections...")
        for section in merged_sections:
            section_title = section.get('title', f"Section {section.get('section_number', 1)}")
            key_topics = section.get('key_topics', [])
            
            # Get content relevant to this section
            section_content = self._extract_section_content(content, " ".join(key_topics), section_title)
            
            # Extract learning objects
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
    
    def _split_content_into_chunks(self, content: str, chunk_size: int = 3000, overlap: int = 500) -> List[str]:
        """
        Split content into overlapping chunks for thorough analysis.
        Each chunk is analyzed separately to catch all sections.
        """
        chunks = []
        content_len = len(content)
        
        if content_len <= chunk_size:
            return [content]
        
        start = 0
        while start < content_len:
            end = min(start + chunk_size, content_len)
            chunk = content[start:end]
            
            # Try to end at a paragraph break for cleaner chunks
            if end < content_len:
                last_break = chunk.rfind('\n\n')
                if last_break > chunk_size // 2:
                    chunk = chunk[:last_break]
                    end = start + last_break
            
            chunks.append(chunk)
            start = end - overlap  # Overlap to catch sections at boundaries
            
            if start >= content_len:
                break
        
        return chunks
    
    def _extract_sections_from_chunk(self, chunk: str, lesson_title: str, chunk_num: int, total_chunks: int) -> List[Dict]:
        """Extract sections from a single chunk of content"""
        
        prompt = f"""You are an expert educational content analyst. Analyze this PART of a lesson and identify all distinct topics and sections.

LESSON TITLE: {lesson_title}
THIS IS PART {chunk_num} OF {total_chunks}

CONTENT:
{chunk}

INSTRUCTIONS:
1. Identify ALL distinct topics, subtopics, and themes in this content
2. Each section should represent a specific concept or subtopic
3. Be GRANULAR - prefer more smaller sections over fewer large ones
4. Look for: definitions, processes, components, techniques, examples, comparisons
5. ALL output must be in ENGLISH (translate if source is not English)

For example, if content discusses "Threads" and "Processes", create SEPARATE sections for:
- What are Threads
- Types of Threads
- Thread States
- Thread Synchronization
- What are Processes
- Process States
- Process vs Thread Comparison

OUTPUT FORMAT (JSON array):
[
  {{"title": "Specific Topic Title", "key_topics": ["keyword1", "keyword2", "keyword3"]}},
  {{"title": "Another Specific Topic", "key_topics": ["keywordA", "keywordB"]}}
]

Return ONLY the JSON array. Find as many distinct sections as exist in the content."""
        
        response = self._call_ollama(prompt, timeout=300)
        
        if not response:
            return []
        
        sections = self._extract_json_from_response(response)
        if isinstance(sections, list):
            return sections
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
                
                # Check if titles are very similar
                title_words = set(title.split())
                other_title_words = set(other_title.split())
                
                if len(title_words) > 0 and len(other_title_words) > 0:
                    word_overlap = len(title_words.intersection(other_title_words)) / max(len(title_words), len(other_title_words))
                    
                    # If very similar, merge
                    if word_overlap > 0.7:
                        used.add(j)
                        similar_topics.extend(other.get('key_topics', []))
            
            # Remove duplicate topics
            unique_topics = list(dict.fromkeys(similar_topics))
            
            merged.append({
                'title': section.get('title', ''),
                'key_topics': unique_topics[:10]  # Limit topics
            })
        
        return merged
    
    def _extract_comprehensive_sections(self, content: str, lesson_title: str) -> List[Dict]:
        """Fallback: Extract sections with a single comprehensive prompt"""
        
        prompt = f"""You are an expert educational content analyst. Analyze this ENTIRE lesson and extract ALL sections and subtopics.

LESSON TITLE: {lesson_title}

CONTENT:
{content[:6000]}

CRITICAL INSTRUCTIONS:
1. Find AT LEAST 5-10 distinct sections/topics
2. Be VERY GRANULAR - split large topics into smaller subtopics
3. Each concept, definition, process should be its own section
4. ALL output in ENGLISH

For a lesson about Operating Systems concepts, you might find:
- Process Definition
- Process States and Lifecycle
- Process Control Block (PCB)
- Context Switching
- Thread Definition
- User-level vs Kernel-level Threads
- Thread Synchronization Mechanisms
- Mutexes and Semaphores
- Deadlock Prevention
etc.

OUTPUT FORMAT (JSON array):
[
  {{"title": "Specific Topic Name", "key_topics": ["keyword1", "keyword2"]}},
  ...
]

Return ONLY the JSON array with at least 5 sections."""
        
        response = self._call_ollama(prompt, timeout=300)
        
        if not response:
            return [{"title": lesson_title, "key_topics": []}]
        
        sections = self._extract_json_from_response(response)
        if isinstance(sections, list) and len(sections) > 0:
            return sections
        
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
        Extract educational learning objects with rich, useful content.
        Uses expert knowledge to enhance explanations beyond just the source material.
        
        MAXIMUM QUALITY: Extracts 5-12 learning objects per section.
        """
        content_preview = section_content[:2500].strip()
        
        # Enhanced prompt for maximum quality extraction
        prompt = f"""You are an expert educator creating comprehensive study materials. Extract ALL key learning objects from this content.

LESSON: {lesson_title}
SECTION: {section_title}

SOURCE MATERIAL:
{content_preview}

---

CRITICAL INSTRUCTIONS:
1. Identify 5-12 distinct, important concepts that students must understand
2. EVERY definition, term, process, component mentioned should become a learning object
3. Each concept should be UNIQUE - no overlapping or repetitive entries
4. Write clear, educational descriptions that EXPLAIN the concept (not just define it)
5. You MAY use your expert knowledge to enhance explanations - don't limit yourself to only the source text
6. Include practical context: why is this important? how is it used?
7. ALL OUTPUT MUST BE IN ENGLISH (translate if source is in another language)

TYPES OF LEARNING OBJECTS TO EXTRACT:
- concept: Abstract ideas or theories (e.g., "Virtual Memory")
- definition: Precise meanings of terms (e.g., "What is a Process?")
- process: Step-by-step procedures (e.g., "Context Switching Steps")
- principle: Rules or laws (e.g., "Locality of Reference")
- component: Parts of a system (e.g., "Page Table Entry")
- technique: Methods or approaches (e.g., "Demand Paging")
- comparison: Differences between concepts (e.g., "Process vs Thread")

For each learning object provide:
- title: Clear, specific name (3-8 words)
- type: One of [concept, definition, process, principle, component, technique, comparison]
- description: 2-4 sentences explaining what it is, why it matters, and how it works
- key_points: 3-5 bullet points with specific, useful facts (not generic statements)
- keywords: 4-6 searchable terms

EXAMPLE OF GOOD OUTPUT:
{{
  "title": "Context Switching Mechanism",
  "type": "process",
  "description": "Context switching is the mechanism by which an OS saves the state of a running process and loads the state of another, enabling multitasking. This involves saving register values, program counter, and memory maps to the Process Control Block before switching to another process.",
  "key_points": ["Takes 1-1000 microseconds depending on hardware", "Triggered by interrupts, system calls, or time slice expiration", "Overhead increases with more processes", "Pure overhead - no useful work is done during switch"],
  "keywords": ["context switch", "process scheduling", "CPU state", "multitasking", "PCB"]
}}

EXAMPLE OF BAD OUTPUT (avoid this):
{{
  "title": "Process Management",
  "description": "Process management is important for the OS.",
  "key_points": ["Processes are managed", "The OS handles processes"]
}}

Return a JSON array with 5-12 learning objects. Be specific, comprehensive, and educational."""
        
        print(f"[ContentParser] Extracting learning objects from: {section_title}")
        response = self._call_ollama(prompt, timeout=300)
        
        if not response:
            print("[ContentParser] No response from Ollama")
            return []
        
        objects = self._extract_json_from_response(response)
        if not isinstance(objects, list) or len(objects) == 0:
            print("[ContentParser] No objects extracted, trying simpler prompt...")
            # Try a simpler fallback prompt
            return self._extract_learning_objects_simple(section_content, section_title, lesson_title)
        
        # Validate and clean the objects
        validated_objects = []
        for obj in objects:
            if not obj.get('title'):
                continue
                
            validated = {
                'title': obj.get('title', 'Unknown'),
                'type': obj.get('type', 'concept'),
                'description': obj.get('description', ''),
                'key_points': obj.get('key_points', []) if isinstance(obj.get('key_points'), list) else [],
                'keywords': obj.get('keywords', []) if isinstance(obj.get('keywords'), list) else []
            }
            validated_objects.append(validated)
        
        print(f"[ContentParser] Extracted {len(validated_objects)} learning objects")
        return validated_objects
    
    def _extract_learning_objects_simple(self, section_content: str, section_title: str, lesson_title: str) -> List[Dict]:
        """Simpler fallback for learning object extraction"""
        content_preview = section_content[:2000].strip()
        
        prompt = f"""Extract 3-5 key concepts from this educational content.

TOPIC: {section_title}

CONTENT:
{content_preview}

For each concept, provide:
- title: Name of the concept
- type: concept, definition, process, or component
- description: 1-2 sentence explanation
- keywords: 2-3 related terms

Return JSON array:
[{{"title": "...", "type": "...", "description": "...", "keywords": ["...", "..."]}}]"""
        
        response = self._call_ollama(prompt, timeout=120)
        if not response:
            return []
        
        objects = self._extract_json_from_response(response)
        if isinstance(objects, list):
            return [{'title': o.get('title', ''), 'type': o.get('type', 'concept'), 
                     'description': o.get('description', ''), 'key_points': [], 
                     'keywords': o.get('keywords', [])} for o in objects if o.get('title')]
        return []
    
    def extract_ontology_relationships(self, content: str, learning_objects: List[Dict], lesson_title: str) -> List[Dict]:
        """
        Extract meaningful relationships between learning objects.
        Focus on quality over quantity - only truly meaningful connections.
        """
        if not learning_objects:
            print("[ContentParser] No learning objects to relate")
            return []
        
        # Build a rich description of each learning object for context
        lo_descriptions = []
        for lo in learning_objects[:12]:  # Limit to avoid token overflow
            title = lo.get("title", lo.get("name", ""))
            desc = lo.get("description", "")[:100]
            lo_descriptions.append(f"- {title}: {desc}")
        
        lo_context = "\n".join(lo_descriptions)
        lo_titles = [lo.get("title", lo.get("name", "")) for lo in learning_objects[:12]]
        
        # Single comprehensive prompt for better relationships
        prompt = f"""You are an expert in knowledge representation. Analyze these learning objects and find meaningful relationships between them.

LESSON: {lesson_title}

LEARNING OBJECTS:
{lo_context}

---

INSTRUCTIONS:
1. Find 8-15 meaningful relationships between these concepts
2. Each relationship should be SPECIFIC and EDUCATIONAL
3. The description should explain WHY this relationship exists
4. Use ONLY the exact titles from the list above
5. ALL OUTPUT IN ENGLISH

RELATIONSHIP TYPES TO USE:
- prerequisite: A must be understood before B
- builds_upon: A extends or elaborates on B  
- part_of: A is a component or aspect of B
- related: A and B are connected concepts
- contrasts_with: A is different from B in important ways
- implements: A is a concrete implementation of B
- enables: A makes B possible

GOOD EXAMPLE:
{{"source": "Process Control Block", "target": "Context Switching", "type": "enables", "description": "The PCB stores process state information that makes context switching possible by preserving and restoring CPU registers"}}

BAD EXAMPLE (too vague):
{{"source": "Process", "target": "OS", "type": "related", "description": "They are related"}}

Return a JSON array of relationships. Focus on relationships that help students understand how concepts connect."""
        
        print("[ContentParser] Extracting ontology relationships...")
        response = self._call_ollama(prompt, timeout=300)
        
        if not response:
            print("[ContentParser] No response for relationships")
            return []
        
        relationships = self._extract_json_from_response(response)
        if not isinstance(relationships, list):
            return []
        
        # Validate relationships - ensure source and target exist
        valid_relationships = []
        title_set = set(lo_titles)
        
        for rel in relationships:
            source = rel.get("source", "")
            target = rel.get("target", "")
            
            # Check if both source and target are valid learning objects
            if source in title_set and target in title_set and source != target:
                valid_relationships.append(rel)
        
        print(f"[ContentParser] Found {len(valid_relationships)} valid relationships")
        return valid_relationships
    
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
