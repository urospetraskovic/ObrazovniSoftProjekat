"""
Quiz Generator - Local Ollama Model Version
Generates SOLO taxonomy-based quiz questions using local AI (no API keys needed)

MAXIMUM QUALITY VERSION:
- Uses comprehensive SOLO taxonomy prompts with detailed level definitions
- Multiple validation passes for question uniqueness
- Rich distractor guidance to avoid obvious wrong answers
- No concern for API costs - running locally
"""

import os
import json
import re
import requests
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

# Ollama Configuration
OLLAMA_BASE_URL = "http://127.0.0.1:11435"
OLLAMA_MODEL = "qwen2.5:14b-instruct-q4_K_M"


class SoloQuizGeneratorLocal:
    """
    SOLO Taxonomy Quiz Generator using Local Ollama Model
    Generates educational quizzes without requiring API keys
    
    MAXIMUM QUALITY APPROACH:
    - Uses the same comprehensive prompts as the API version
    - Tracks generated questions to avoid repetition
    - Does multiple passes to ensure question diversity
    """
    
    def __init__(self):
        """Initialize the quiz generator with Ollama configuration"""
        self.ollama_base_url = OLLAMA_BASE_URL
        self.ollama_model = OLLAMA_MODEL
        self.provider = "ollama_local"
        
        print(f"[QuizGenerator-Local] Initialized with Ollama (14B model)")
        print(f"[QuizGenerator-Local] Mode: MAXIMUM QUALITY (no API cost concerns)")
        
        # Test connection
        if not self._test_ollama_connection():
            print("[QuizGenerator-Local] WARNING: Could not connect to Ollama server!")
            print(f"[QuizGenerator-Local] Make sure Ollama is running on {self.ollama_base_url}")
        
        self.api_exhausted = False
        self._content_summary_cache = {}
        
        # Track generated questions to avoid duplicates
        self._generated_question_hashes: Set[str] = set()
        self._generated_question_texts: List[str] = []
    
    def _test_ollama_connection(self) -> bool:
        """Test if Ollama server is responding"""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"[QuizGenerator-Local] Connection test failed: {e}")
            return False
    
    def _get_question_hash(self, question_text: str) -> str:
        """Generate a hash for question deduplication"""
        # Normalize the question text
        normalized = question_text.lower().strip()
        # Remove punctuation for better matching
        normalized = re.sub(r'[^\w\s]', '', normalized)
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _is_question_unique(self, question_text: str, similarity_threshold: float = 0.7) -> bool:
        """
        Check if a question is sufficiently unique from already generated ones.
        Uses both hash matching and simple word overlap check.
        """
        if not question_text:
            return False
        
        # Check exact hash match
        q_hash = self._get_question_hash(question_text)
        if q_hash in self._generated_question_hashes:
            print(f"[QuizGenerator-Local] Duplicate question detected (hash match)")
            return False
        
        # Check word overlap with existing questions
        new_words = set(question_text.lower().split())
        for existing in self._generated_question_texts:
            existing_words = set(existing.lower().split())
            if len(new_words) == 0 or len(existing_words) == 0:
                continue
            
            overlap = len(new_words.intersection(existing_words))
            max_len = max(len(new_words), len(existing_words))
            similarity = overlap / max_len
            
            if similarity > similarity_threshold:
                print(f"[QuizGenerator-Local] Similar question detected ({similarity:.1%} overlap)")
                return False
        
        return True
    
    def _register_question(self, question_text: str):
        """Register a question as generated to avoid future duplicates"""
        self._generated_question_hashes.add(self._get_question_hash(question_text))
        self._generated_question_texts.append(question_text)
    
    def _call_ollama(self, prompt: str, timeout: int = 300) -> Optional[str]:
        """
        Call Ollama API with the 14B model
        
        Args:
            prompt: The prompt to send to the model
            timeout: Timeout in seconds
            
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
            
            print(f"[QuizGenerator-Local] Calling Ollama ({len(prompt)} chars prompt)...")
            response = requests.post(url, json=payload, timeout=timeout)
            
            if response.status_code == 200:
                data = response.json()
                result = data.get("response", "")
                print(f"[QuizGenerator-Local] Ollama returned {len(result)} chars")
                return result
            else:
                print(f"[QuizGenerator-Local] Ollama error: {response.status_code}")
                return None
                
        except requests.Timeout:
            print(f"[QuizGenerator-Local] Ollama request timed out after {timeout}s")
            return None
        except Exception as e:
            print(f"[QuizGenerator-Local] Ollama error: {e}")
            return None
    
    def generate_solo_questions(
        self,
        lessons_data: List[Dict[str, Any]],
        solo_levels: List[str],
        questions_per_level: int = 3,
        section_ids: List[int] = None,
        ontology_relationships: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate questions based on SOLO taxonomy levels from parsed lessons.
        NOW WITH ONTOLOGY SUPPORT: Uses domain knowledge relationships to enhance questions!
        
        Args:
            lessons_data: List of lesson dicts with sections and learning objects
            solo_levels: List of SOLO levels to generate questions for
            questions_per_level: Number of questions per SOLO level (max 2 for memory)
            section_ids: Optional list of specific section IDs to use
            ontology_relationships: Optional domain ontology relationships for enhanced context
            
        Returns:
            List of question dicts ready for database storage
        """
        print(f"\n[SOLO-Local] Starting MEMORY-OPTIMIZED question generation")
        print(f"[SOLO-Local] Lessons: {len(lessons_data)}, Levels: {solo_levels}")
        
        # Store ontology relationships for use in all question generators
        self.ontology_relationships = ontology_relationships or []
        if self.ontology_relationships:
            print(f"[SOLO-Local] ✓ Using {len(self.ontology_relationships)} ontology relationships to enhance questions")
        
        # Honor requested questions per level (no artificial cap - running locally)
        # The user can request whatever they want, we'll generate it
        print(f"[SOLO-Local] Questions per level: {questions_per_level}")
        
        # Reset question tracking for this generation session
        self._generated_question_hashes.clear()
        self._generated_question_texts.clear()
        
        generated_questions = []
        primary_lesson = lessons_data[0] if lessons_data else None
        
        if not primary_lesson:
            raise ValueError("At least one lesson is required")
        
        # Skip content summary generation to save memory
        content_summary = ""
        
        for level in solo_levels:
            print(f"\n[SOLO-Local] Generating {questions_per_level} {level} questions...")
            
            level_questions = 0
            max_attempts = questions_per_level * 2  # Allow up to 2x attempts for uniqueness
            attempts = 0
            
            while level_questions < questions_per_level and attempts < max_attempts:
                attempts += 1
                
                try:
                    # Use different learning object for each attempt to encourage diversity
                    lo_offset = attempts - 1
                    
                    if level == 'unistructural':
                        question = self._generate_unistructural_question(
                            primary_lesson, section_ids, content_summary, lo_offset
                        )
                    elif level == 'multistructural':
                        question = self._generate_multistructural_question(
                            primary_lesson, section_ids, content_summary, lo_offset
                        )
                    elif level == 'relational':
                        question = self._generate_relational_question(
                            primary_lesson, section_ids, content_summary
                        )
                    elif level == 'extended_abstract':
                        # For extended abstract, use both lessons if available
                        secondary_lesson = lessons_data[1] if len(lessons_data) > 1 else None
                        question = self._generate_extended_abstract_question(
                            primary_lesson, content_summary, secondary_lesson
                        )
                    else:
                        question = None
                    
                    if question and self._is_question_unique(question.get('question_text', '')):
                        question['solo_level'] = level
                        generated_questions.append(question)
                        self._register_question(question.get('question_text', ''))
                        level_questions += 1
                        print(f"[SOLO-Local] ✓ Generated {level} question {level_questions}/{questions_per_level}")
                    elif question:
                        print(f"[SOLO-Local] ✗ Question rejected (not unique), retrying...")
                    
                except Exception as e:
                    print(f"[SOLO-Local] Error generating {level} question: {e}")
            
            if level_questions < questions_per_level:
                print(f"[SOLO-Local] Generated {level_questions}/{questions_per_level} {level} questions")
        
        print(f"\n[SOLO-Local] Total questions generated: {len(generated_questions)}")
        return generated_questions
    
    def _build_ontology_context(self, learning_objects: List[Dict] = None) -> str:
        """
        Build ontology context from domain relationships.
        Shows prerequisites, hierarchies, and semantic connections.
        """
        if not self.ontology_relationships:
            return ""
        
        # Filter relationships relevant to the learning objects if provided
        relevant_rels = self.ontology_relationships
        if learning_objects:
            lo_titles = {lo.get('title', '') for lo in learning_objects}
            relevant_rels = [
                r for r in self.ontology_relationships
                if r.get('source_title', '') in lo_titles or r.get('target_title', '') in lo_titles
            ]
        
        if not relevant_rels:
            return ""
        
        # Build a formatted ontology context
        ontology_lines = ["DOMAIN ONTOLOGY (concept relationships):"]
        
        # Group by relationship type
        rels_by_type = {}
        for rel in relevant_rels[:20]:  # Limit to top 20 to keep it concise
            rel_type = rel.get('relationship_type', 'related_to')
            if rel_type not in rels_by_type:
                rels_by_type[rel_type] = []
            rels_by_type[rel_type].append(rel)
        
        # Format relationships
        for rel_type, rels in sorted(rels_by_type.items()):
            ontology_lines.append(f"\n{rel_type.upper().replace('_', ' ')}:")
            for rel in rels[:5]:  # Max 5 per type
                source = rel.get('source_title', '')
                target = rel.get('target_title', '')
                desc = rel.get('description', '')
                ontology_lines.append(f"  • {source} → {target}")
                if desc:
                    ontology_lines.append(f"    ({desc[:80]})")
        
        return "\n".join(ontology_lines)
    
    def _generate_content_summary(self, lesson: Dict[str, Any]) -> str:
        """Generate a summary of the lesson content for higher-order questions"""
        lesson_title = lesson.get('title', 'Lesson')
        
        # Collect all content
        all_content = []
        for section in lesson.get('sections', []):
            all_content.append(f"## {section.get('title', '')}")
            for lo in section.get('learning_objects', []):
                all_content.append(f"- {lo.get('title', '')}: {lo.get('description', '')[:200]}")
        
        content_text = "\n".join(all_content)[:3000]
        
        prompt = f"""Summarize the key concepts, themes, and relationships in this educational content.

LESSON: {lesson_title}

CONTENT:
{content_text}

Write a 3-4 paragraph summary focusing on:
1. Main concepts and how they relate
2. Key principles that can be applied
3. Important distinctions between concepts

Be concise but comprehensive."""
        
        print("[SOLO-Local] Generating content summary for higher-order questions...")
        summary = self._call_ollama(prompt, timeout=120)
        return summary or ""
    
    def _generate_unistructural_question(
        self,
        lesson: Dict[str, Any],
        section_ids: List[int] = None,
        content_summary: str = "",
        lo_offset: int = 0
    ) -> Dict[str, Any]:
        """
        Generate UNISTRUCTURAL question from LEARNING OBJECTS
        
        Uses comprehensive SOLO taxonomy definitions and detailed distractor guidance.
        """
        
        lesson_title = lesson.get('title', 'Lesson')
        sections = lesson.get('sections', [])
        
        if section_ids:
            sections = [s for s in sections if s.get('id') in section_ids]
        
        # Collect all learning objects
        learning_objects = []
        for section in sections:
            for lo in section.get('learning_objects', []):
                learning_objects.append({
                    'title': lo.get('title', ''),
                    'description': lo.get('description', ''),
                    'type': lo.get('type', 'concept'),
                    'keywords': lo.get('keywords', []),
                    'key_points': lo.get('key_points', [])
                })
        
        if not learning_objects:
            return None
        
        # Pick a learning object based on offset for diversity
        lo_index = lo_offset % len(learning_objects)
        lo = learning_objects[lo_index]
        
        # Build rich content from the learning object
        lo_content = f"""Title: {lo['title']}
Type: {lo['type']}
Description: {lo['description']}
Keywords: {', '.join(lo.get('keywords', []))}
Key Points: {'; '.join(lo.get('key_points', [])[:3])}"""
        
        # Comprehensive prompt from quiz_generator.py
        prompt = f"""Create a UNISTRUCTURAL level question about '{lesson_title}'.

LEARNING OBJECT:
{lo_content}

UNISTRUCTURAL LEVEL DEFINITION:
At this stage, the learner gets to know just a single relevant aspect of a task or subject; the student gets a basic understanding of a concept or task. Therefore, a student is able to make easy and apparent connections, but he or she does not have any idea how significant that information be or not. In addition, the students' response indicates a concrete understanding of the task, but it focuses on only one relevant aspect.

TASK: Create a question that tests knowledge of ONE specific fact/concept. Student should identify or name a single element directly stated in the content.

CRITICAL INSTRUCTIONS FOR DISTRACTORS:
- **DO NOT** create obviously wrong options that can be eliminated by common sense
- **DO** create plausible but INCORRECT options that:
  * Are related to the topic but refer to WRONG specifics
  * Sound similar to correct answer but are incorrect variants
  * Common misconceptions that students might hold
  * Related but different concepts from the content
- Example BAD distractor: "The moon is made of cheese" 
- Example GOOD distractor: "Neptune" (instead of "Uranus") - students who didn't read carefully pick this
- Make students actually think about the specific detail, not guess

Requirements:
- Focus on ONE isolated aspect only
- No connections to other concepts required
- ALL TEXT IN ENGLISH
- Question < 250 chars
- 4 MC options (A-D), one correct
- 3 distractors must be PLAUSIBLE and require reading comprehension to eliminate
- Explanation < 250 chars

Return ONLY JSON: {{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ...", "explanation": "..."}}"""
        
        response = self._call_ollama(prompt, timeout=300)
        if not response:
            return None
        
        question_data = self._parse_question_response(response)
        if question_data:
            return {
                'question_text': question_data.get('question', ''),
                'question_type': 'multiple_choice',
                'options': question_data.get('options', []),
                'correct_answer': question_data.get('correct_answer', ''),
                'correct_option_index': self._find_correct_index(
                    question_data.get('options', []),
                    question_data.get('correct_answer', '')
                ),
                'explanation': question_data.get('explanation', ''),
                'bloom_level': 'remember'
            }
        return None
    
    def _generate_multistructural_question(
        self,
        lesson: Dict[str, Any],
        section_ids: List[int] = None,
        content_summary: str = "",
        lo_offset: int = 0
    ) -> Dict[str, Any]:
        """
        Generate MULTISTRUCTURAL question from SECTIONS
        
        Uses comprehensive SOLO taxonomy definitions and detailed distractor guidance.
        """
        
        lesson_title = lesson.get('title', 'Lesson')
        sections = lesson.get('sections', [])
        
        if section_ids:
            sections = [s for s in sections if s.get('id') in section_ids]
        
        if not sections:
            return None
        
        # Pick a section based on offset for diversity
        section_index = lo_offset % len(sections)
        section = sections[section_index]
        
        section_title = section.get('title', '')
        
        # Build comprehensive content from all learning objects in section
        los_content = []
        for lo in section.get('learning_objects', [])[:6]:
            los_content.append(f"- {lo.get('title', '')}: {lo.get('description', '')[:150]}")
            if lo.get('key_points'):
                for point in lo.get('key_points', [])[:2]:
                    los_content.append(f"  • {point}")
        
        content = "\n".join(los_content)
        
        # Add ontology context if available
        ontology_context = self._build_ontology_context(section.get('learning_objects', []))
        ontology_section = f"\n\n{ontology_context}" if ontology_context else ""
        
        # Comprehensive prompt from quiz_generator.py
        prompt = f"""Create a MULTISTRUCTURAL level question about '{lesson_title}'.

SECTION: {section_title}

CONTENT:
{content}{ontology_section}

MULTISTRUCTURAL LEVEL DEFINITION:
At this stage, students gain an understanding of numerous relevant independent aspects. Despite understanding the relationship between different aspects, its relationship to the whole remains unclear. Suppose the teacher is teaching about several topics and ideas, the students can make varied connections, but they fail to understand the significance of the whole. The students' responses are based on relevant aspects, but their responses are handled independently.

TASK: Create a question that tests knowledge of MULTIPLE separate facts/features. Student should list or identify several independent elements WITHOUT explaining how they connect.

CRITICAL INSTRUCTIONS FOR DISTRACTORS:
- **DO NOT** create obviously wrong options that can be eliminated by common sense
- **DO** create plausible but INCORRECT combinations that:
  * Mix some correct items with 1-2 WRONG items
  * Include correct items in wrong contexts
  * Reorder/rearrange items incorrectly
  * Include related but not-mentioned aspects from content
  * Common student misconceptions about the topic
- Example BAD distractor: "Bananas, dinosaurs, computers" (obviously unrelated)
- Example GOOD distractor: "DNA, RNA, proteins" (related to biology, but wrong combination for this specific question)
- Make students verify EACH item, not just recognize keywords

Requirements:
- Multiple items or aspects, but handled independently
- Don't require showing relationships between items
- ALL TEXT IN ENGLISH
- Question < 250 chars
- 4 MC options (A-D), one correct
- 3 distractors must combine PLAUSIBLE elements that seem correct at first glance
- Explanation < 250 chars

Return ONLY JSON: {{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ...", "explanation": "..."}}"""
        
        response = self._call_ollama(prompt, timeout=300)
        if not response:
            return None
        
        question_data = self._parse_question_response(response)
        if question_data:
            return {
                'question_text': question_data.get('question', ''),
                'question_type': 'multiple_choice',
                'options': question_data.get('options', []),
                'correct_answer': question_data.get('correct_answer', ''),
                'correct_option_index': self._find_correct_index(
                    question_data.get('options', []),
                    question_data.get('correct_answer', '')
                ),
                'explanation': question_data.get('explanation', ''),
                'bloom_level': 'understand'
            }
        return None
    
    def _generate_relational_question(
        self,
        lesson: Dict[str, Any],
        section_ids: List[int] = None,
        content_summary: str = ""
    ) -> Dict[str, Any]:
        """
        Generate RELATIONAL question from SECTIONS + LEARNING OBJECTS
        
        Uses comprehensive SOLO taxonomy definitions and detailed distractor guidance.
        Requires understanding of relationships between concepts.
        """
        
        lesson_title = lesson.get('title', 'Lesson')
        sections = lesson.get('sections', [])
        
        if section_ids:
            sections = [s for s in sections if s.get('id') in section_ids]
        
        if not sections:
            return None
        
        # Build comprehensive content with relationships visible
        content_parts = []
        for section in sections[:4]:
            section_title = section.get('title', '')
            content_parts.append(f"### {section_title}")
            for lo in section.get('learning_objects', [])[:5]:
                content_parts.append(f"- {lo.get('title', '')}: {lo.get('description', '')[:200]}")
                # Include key points for more context
                for point in lo.get('key_points', [])[:2]:
                    content_parts.append(f"  • {point}")
        
        combined_content = "\n".join(content_parts)[:3000]
        
        # Add ontology relationships for structure understanding
        ontology_context = self._build_ontology_context([
            lo for section in sections for lo in section.get('learning_objects', [])
        ])
        ontology_section = f"\n\n{ontology_context}" if ontology_context else ""
        
        # Add summary section for higher-order understanding
        summary_section = ""
        if content_summary:
            summary_section = f"\n\nCONTENT SUMMARY (key themes and relationships):\n{content_summary[:1000]}\n"
        
        # Comprehensive prompt from quiz_generator.py
        prompt = f"""Create a RELATIONAL level question about '{lesson_title}'.

CONTENT:
{combined_content}{ontology_section}{summary_section}

RELATIONAL LEVEL DEFINITION:
This stage relates to aspects of knowledge combining to form a structure. By this stage, the student is able to understand the importance of different parts in relation to the whole. They are able to connect concepts and ideas, so it provides a coherent knowledge of the whole thing. Moreover, the students' response indicates an understanding of the task by combining all the parts, and they can demonstrate how each part contributes to the whole.

TASK: Create a question that tests understanding of HOW parts CONNECT and work TOGETHER. Use both the detailed content, domain ontology AND the summary to identify key relationships. Student should explain relationships, patterns, or cause-effect between elements. Shows deep integrated understanding.

CRITICAL INSTRUCTIONS FOR DISTRACTORS:
- **DO NOT** create obviously wrong options that can be eliminated without thinking
- **DO** create CHALLENGING distractors that:
  * Seem logical if you only understand PART of the relationship
  * Require understanding the FULL integrated picture to reject
  * Include partially correct connections (correct concepts, wrong relationship)
  * Reverse causes and effects (plausible but backwards)
  * Connect concepts that ARE related but in wrong ways
  * Address a DIFFERENT relationship that also exists in the content
- Example BAD distractor: "Because trees don't exist" (obviously wrong)
- Example GOOD distractor: "Because temperature increases while gas pressure also increases" (confuses correlation with the actual causal mechanism)
- Distractors should reflect REAL misconceptions about how things relate

Requirements:
- Ask about relationships, connections, or cause-effect WITHIN the content
- Use the summary to understand the broader context and key themes
- Require understanding of how parts fit together into a coherent whole
- Student must show how different elements relate to each other
- ALL TEXT IN ENGLISH
- Question < 250 chars
- 4 MC options (A-D), one correct
- 3 distractors must be CHALLENGING and reflect real misconceptions
- Explanation < 250 chars

Return ONLY JSON: {{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ...", "explanation": "..."}}"""
        
        response = self._call_ollama(prompt, timeout=300)
        if not response:
            return None
        
        question_data = self._parse_question_response(response)
        if question_data:
            return {
                'question_text': question_data.get('question', ''),
                'question_type': 'multiple_choice',
                'options': question_data.get('options', []),
                'correct_answer': question_data.get('correct_answer', ''),
                'correct_option_index': self._find_correct_index(
                    question_data.get('options', []),
                    question_data.get('correct_answer', '')
                ),
                'explanation': question_data.get('explanation', ''),
                'bloom_level': 'analyze'
            }
        return None
    
    def _generate_extended_abstract_question(
        self,
        lesson: Dict[str, Any],
        content_summary: str = "",
        secondary_lesson: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate EXTENDED ABSTRACT question requiring synthesis and cross-lesson application
        
        Uses comprehensive SOLO taxonomy definitions and detailed distractor guidance.
        For maximum effectiveness, combines concepts from TWO lessons to test transfer of knowledge.
        Requires applying learned concepts to NEW situations that synthesize both topics.
        """
        
        lesson_title = lesson.get('title', 'Lesson')
        
        # Get key concepts from primary lesson
        concepts_primary = []
        for section in lesson.get('sections', []):
            section_title = section.get('title', '')
            for lo in section.get('learning_objects', [])[:4]:
                concepts_primary.append(f"- {lo.get('title', '')}: {lo.get('description', '')[:150]}")
        
        concepts_text = "\n".join(concepts_primary[:15])
        
        # Get concepts from secondary lesson if provided
        concepts_secondary_text = ""
        secondary_title = ""
        if secondary_lesson:
            secondary_title = secondary_lesson.get('title', 'Lesson 2')
            concepts_secondary = []
            for section in secondary_lesson.get('sections', []):
                for lo in section.get('learning_objects', [])[:4]:
                    concepts_secondary.append(f"- {lo.get('title', '')}: {lo.get('description', '')[:150]}")
            secondary_concepts = "\n".join(concepts_secondary[:15])
            concepts_secondary_text = f"\n\nSECONDARY TOPIC ({secondary_title}) CONCEPTS:\n{secondary_concepts}"
        
        # Add summary section for higher-order understanding
        summary_section = ""
        if content_summary:
            summary_section = f"\n\nCONTENT SUMMARY (key themes and relationships):\n{content_summary[:1000]}\n"
        
        # Comprehensive prompt with EXPLICIT INSTRUCTIONS for combining 2 lessons
        if secondary_lesson:
            combine_instruction = f"""CRITICAL - COMBINE 2 TOPICS:
You MUST create a question that connects and combines concepts from BOTH '{lesson_title}' AND '{secondary_title}'.
The question should show how these two topics relate to each other, influence each other, or can be applied together.
Example: If lesson 1 is about Process Management and lesson 2 is about Virtual Memory, ask how processes interact with virtual memory.
The student MUST demonstrate understanding of BOTH topics to answer correctly."""
        else:
            combine_instruction = "Create a question that generalizes principles to NEW contexts not directly mentioned in the content."
        
        prompt = f"""Create an EXTENDED ABSTRACT level question{' combining 2 lessons' if secondary_lesson else ''}.

PRIMARY TOPIC ({lesson_title}) CONCEPTS:
{concepts_text}{concepts_secondary_text}{summary_section}

{combine_instruction}

EXTENDED ABSTRACT LEVEL DEFINITION:
By this level, students are able to make connections within the provided task, and they also create connections beyond that. They develop the ability to transfer and generalise the concepts and principles from one subject area into a particular domain. Therefore, the students' response indicates that they can conceptualise beyond the level of what has been taught. They are able to propose new concepts and ideas depending on their understanding of the task or subject taught.

TASK: Create a question that requires:
- Understanding core principles from {'both topics' if secondary_lesson else 'the lesson'}
- {'Combining/relating these 2 independent concepts' if secondary_lesson else 'Applying this knowledge to'} to a NEW context NOT directly mentioned in the content
- Student must synthesize and generalize to demonstrate mastery

CRITICAL INSTRUCTIONS FOR DISTRACTORS:
- **DO NOT** create obviously wrong options
- **DO** create TRICKY distractors that:
  * Look correct if you misunderstand which principle applies
  * Correctly apply a DIFFERENT but related principle
  * Misapply knowledge from {'the wrong lesson' if secondary_lesson else 'the content'}
  * Follow logically from the content but reach wrong conclusion
  * Represent COMMON OVERGENERALIZATIONS of the principles
  * Apply the principle to SIMILAR but wrong context
- Example BAD distractor: "Blue elephants" (nonsense)
- Example GOOD distractor: "You should increase speed" (correct for acceleration problem, wrong for this momentum problem - different principle)
- Distractors should be SOPHISTICATED errors that test deep understanding

Requirements:
- {'Demonstrate understanding of relationship between both topics' if secondary_lesson else 'Identify transferable concepts and principles'}
- Create a scenario that requires applying/synthesizing knowledge to a NEW situation
- Scenario should NOT be directly mentioned in the provided content
- Requires student to conceptualize beyond what was taught
- Student must demonstrate ability to TRANSFER knowledge across {'domains' if secondary_lesson else 'contexts'}
- ALL TEXT IN ENGLISH
- Question < 300 chars
- 4 MC options (A-D), one correct
- 3 distractors must be CHALLENGING: plausible applications of WRONG principles or MISAPPLICATIONS
- Explanation < 250 chars, showing how both topics connect {'(if applicable)' if secondary_lesson else ''}

Return ONLY JSON: {{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ...", "explanation": "..."}}"""
        
        response = self._call_ollama(prompt, timeout=300)
        if not response:
            return None
        
        question_data = self._parse_question_response(response)
        if question_data:
            return {
                'question_text': question_data.get('question', ''),
                'question_type': 'multiple_choice',
                'options': question_data.get('options', []),
                'correct_answer': question_data.get('correct_answer', ''),
                'correct_option_index': self._find_correct_index(
                    question_data.get('options', []),
                    question_data.get('correct_answer', '')
                ),
                'explanation': question_data.get('explanation', ''),
                'bloom_level': 'create'
            }
        return None
    
    def _parse_question_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse API response to extract question data"""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return None
        except json.JSONDecodeError:
            return None
    
    def _find_correct_index(self, options: List[str], correct_answer: str) -> int:
        """Find the index of the correct answer in options list"""
        if not options or not correct_answer:
            return 0
        
        for i, opt in enumerate(options):
            if opt == correct_answer:
                return i
        
        # Try matching by letter prefix
        correct_letter = correct_answer[0].upper() if correct_answer else 'A'
        for i, opt in enumerate(options):
            if opt.startswith(correct_letter):
                return i
        
        return 0


# Create global instance
quiz_generator_local = SoloQuizGeneratorLocal()
