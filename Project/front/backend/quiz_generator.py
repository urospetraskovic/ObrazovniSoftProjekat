import os
import json
import re
from datetime import datetime
from dotenv import load_dotenv
import requests
from typing import Dict, List, Any

load_dotenv()

class SoloQuizGenerator:
    """
    SOLO Taxonomy Quiz Generator
    Generates educational quizzes from text content using SOLO taxonomy levels
    """
    
    def __init__(self):
        """Initialize the quiz generator with API configuration"""
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
        
        if not self.api_keys:
            print("Warning: No API keys configured. Using mock responses.")
            self.api_keys = ['mock']
        
        self.current_key_index = 0
        self.provider = "openrouter"
    
    def generate_quiz(self, content: str, filename: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main method to generate quiz from content
        
        Args:
            content: Text content to generate quiz from
            filename: Name of the uploaded file
            config: Optional configuration dict with keys:
                - total_questions: int or None (None = let model decide)
                - question_mode: 'auto' or 'manual'
                - solo_distribution: dict with level percentages or None
                - distribution_mode: 'auto' or 'manual'
                - use_smart_chunking: bool (default: True)
            
        Returns:
            Dictionary containing quiz data with chapters and questions
        """
        try:
            # Use smart chunking by default
            chapters = self._split_into_chapters_smart(content, config)
            
            # Determine config
            if config is None:
                config = {}
            
            # Determine total questions
            if config.get('question_mode') == 'auto' or config.get('total_questions') is None:
                # Auto mode: calculate based on content length and chapters
                # More intelligent calculation: base on content length + chapter count
                content_length = len(content)
                chapter_count = len(chapters)
                
                # Base calculation: roughly 1 question per 500 characters, min 5 per chapter
                questions_by_length = max(5, content_length // 500)
                questions_by_chapters = chapter_count * 5
                
                # Use the higher of the two to avoid too few questions for continuous text
                total_questions = max(questions_by_length, questions_by_chapters)
                # Cap at reasonable max (100 questions)
                total_questions = min(total_questions, 100)
                
                question_mode = 'auto'
            else:
                total_questions = config.get('total_questions', len(chapters) * 5)
                question_mode = 'manual'
            
            # Determine SOLO distribution
            if config.get('distribution_mode') == 'auto' or config.get('solo_distribution') is None:
                # Auto mode: use balanced distribution (5 SOLO levels)
                solo_distribution = {
                    'prestructural': 0.10,
                    'unistructural': 0.15,
                    'multistructural': 0.30,
                    'relational': 0.30,
                    'extended_abstract': 0.15
                }
                distribution_mode = 'auto'
            else:
                solo_distribution = config.get('solo_distribution', {
                    'prestructural': 0.10,
                    'unistructural': 0.15,
                    'multistructural': 0.30,
                    'relational': 0.30,
                    'extended_abstract': 0.15
                })
                distribution_mode = 'manual'
            
            quiz_data = {
                'metadata': {
                    'filename': filename,
                    'generated_at': datetime.now().isoformat(),
                    'total_chapters': len(chapters),
                    'total_questions': 0,
                    'question_mode': question_mode,
                    'distribution_mode': distribution_mode,
                    'config': config
                },
                'chapters': []
            }
            
            questions_generated = 0
            questions_per_chapter = max(1, total_questions // len(chapters)) if chapters else 5
            
            # Generate questions for each chapter
            for idx, chapter_content in enumerate(chapters):
                if questions_generated >= total_questions:
                    break
                    
                # Calculate remaining questions for this chapter
                remaining = total_questions - questions_generated
                chapter_question_count = min(questions_per_chapter, remaining)
                
                chapter_data = self._process_chapter_smart(
                    chapter_content, 
                    idx + 1,
                    chapter_question_count,
                    solo_distribution
                )
                if chapter_data:
                    quiz_data['chapters'].append(chapter_data)
                    questions_generated += len(chapter_data.get('questions', []))
                    quiz_data['metadata']['total_questions'] = questions_generated
            
            return quiz_data
            
        except Exception as e:
            print(f"Error in generate_quiz: {str(e)}")
            raise
    
    def _split_into_chapters_smart(self, content: str, config: Dict[str, Any] = None) -> List[str]:
        """
        Intelligently split content into chapters using multiple strategies
        
        Args:
            content: Full text content
            config: Configuration dict with chunking preferences
            
        Returns:
            List of chapter contents
        """
        if config is None:
            config = {}
        
        use_smart = config.get('use_smart_chunking', True)
        
        if not use_smart:
            # Fall back to original method
            return self._split_into_chapters(content)
        
        # Strategy 1: Try to find existing chapter markers
        chapter_pattern = r'CHAPTER\s+\d+:|={2,}.*?={2,}|\n[A-Z][A-Z\s]+\n(?=[A-Z])'
        parts = re.split(chapter_pattern, content)
        chapters = [part.strip() for part in parts if part.strip() and len(part.strip()) > 200]
        
        # If found good chapters, use them
        if len(chapters) >= 2:
            return chapters[:15]
        
        # Strategy 2: Split by paragraph breaks (multiple newlines)
        paragraphs = re.split(r'\n\s*\n+', content)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        # Group paragraphs into semantic chunks
        if len(paragraphs) > 5:
            chapters = self._group_by_semantic_similarity(paragraphs)
            if chapters:
                return chapters[:15]
        
        # Strategy 3: Split by word count (roughly equal chunks)
        if len(paragraphs) > 1:
            return self._split_by_content_length(content, target_chunks=5)
        
        # Fallback: Return whole content as single chapter
        return [content]
    
    def _group_by_semantic_similarity(self, paragraphs: List[str]) -> List[str]:
        """
        Group paragraphs into semantic chunks based on content length and breaks
        
        Args:
            paragraphs: List of paragraph strings
            
        Returns:
            List of grouped content chunks
        """
        chapters = []
        current_chunk = ""
        target_length = 800  # characters per chunk
        
        for para in paragraphs:
            if len(current_chunk) + len(para) < target_length:
                current_chunk += " " + para if current_chunk else para
            else:
                if current_chunk:
                    chapters.append(current_chunk)
                current_chunk = para
        
        if current_chunk:
            chapters.append(current_chunk)
        
        return [ch for ch in chapters if len(ch) > 200]
    
    def _split_by_content_length(self, content: str, target_chunks: int = 5) -> List[str]:
        """
        Split content into approximately equal-sized chunks
        
        Args:
            content: Full text content
            target_chunks: Target number of chunks
            
        Returns:
            List of content chunks
        """
        words = content.split()
        words_per_chunk = max(100, len(words) // target_chunks)
        
        chapters = []
        for i in range(0, len(words), words_per_chunk):
            chunk = ' '.join(words[i:i+words_per_chunk])
            if len(chunk) > 100:
                chapters.append(chunk)
        
        return chapters[:15]
    
    def _process_chapter(self, chapter_content: str, chapter_num: int) -> Dict[str, Any]:
        """
        Process a single chapter and generate questions (legacy method)
        
        Args:
            chapter_content: Text content of the chapter
            chapter_num: Chapter number
            
        Returns:
            Dictionary containing chapter data with questions
        """
        return self._process_chapter_smart(chapter_content, chapter_num, 5, {
            'prestructural': 0.15,
            'multistructural': 0.35,
            'relational': 0.35,
            'extended_abstract': 0.15
        })
    
    def _process_chapter_smart(
        self, 
        chapter_content: str, 
        chapter_num: int,
        target_questions: int = 4,
        solo_distribution: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Process a single chapter and generate configurable number of questions
        
        Args:
            chapter_content: Text content of the chapter
            chapter_num: Chapter number
            target_questions: Target number of questions for this chapter
            solo_distribution: Distribution of SOLO levels
            
        Returns:
            Dictionary containing chapter data with questions
        """
        if solo_distribution is None:
            solo_distribution = {
                'prestructural': 0.10,
                'unistructural': 0.15,
                'multistructural': 0.25,
                'relational': 0.30,
                'extended_abstract': 0.20
            }
        
        try:
            # Extract chapter title (first line or first sentence max 80 chars)
            lines = chapter_content.split('\n')
            title = lines[0].strip() if lines else f"Chapter {chapter_num}"
            
            # Limit title length to 80 characters
            if len(title) > 80:
                # Find first sentence boundary
                sentences = title.split('. ')
                title = sentences[0]
                if len(title) > 80:
                    title = title[:77] + '...'
            
            chapter_data = {
                'chapter_number': chapter_num,
                'title': title,
                'content_preview': chapter_content[:150] + '...',
                'questions': []
            }
            
            # Calculate questions per level based on distribution (all 5 SOLO levels)
            solo_levels = ['prestructural', 'unistructural', 'multistructural', 'relational', 'extended_abstract']
            questions_per_level = {}
            
            for level in solo_levels:
                count = max(1, round(target_questions * solo_distribution.get(level, 0.25)))
                questions_per_level[level] = count
            
            # Generate questions for each SOLO level
            for level in solo_levels:
                for _ in range(questions_per_level[level]):
                    question = self._generate_question(chapter_content, level, title)
                    if question:
                        chapter_data['questions'].append({
                            'solo_level': level,
                            'question_data': question
                        })
            
            return chapter_data if chapter_data['questions'] else None
            
        except Exception as e:
            print(f"Error processing chapter {chapter_num}: {str(e)}")
            return None
    
    def _generate_question(self, content: str, level: str, context: str) -> Dict[str, Any]:
        """
        Generate a single question at specified SOLO level
        
        Args:
            content: Chapter content
            level: SOLO taxonomy level
            context: Chapter context/title
            
        Returns:
            Dictionary with question data
        """
        try:
            if self.api_keys[0] == 'mock':
                print(f"Using mock questions (no API keys configured)")
                return self._generate_mock_question(content, level, context)
            
            # Call API to generate question
            prompt = self._build_prompt(content, level, context)
            response = self._call_api(prompt)
            
            if response:
                parsed = self._parse_question_response(response)
                if parsed:
                    return parsed
                else:
                    print(f"Failed to parse API response for {level}. Response: {response[:100]}")
                    return self._generate_mock_question(content, level, context)
            else:
                print(f"API returned None for {level} question. Using mock.")
                return self._generate_mock_question(content, level, context)
                
        except Exception as e:
            print(f"Error generating {level} question: {str(e)}")
            return self._generate_mock_question(content, level, context)
    
    def _build_prompt(self, content: str, level: str, context: str) -> str:
        """Build prompt for API request with complete SOLO taxonomy definitions"""
        
        solo_definitions = """
SOLO TAXONOMY - COMPREHENSIVE LEVEL DEFINITIONS (Based on Biggs & Collis):

1. PRESTRUCTURAL (Surface Learning - Quantitative):
   Definition: Student doesn't understand the topic or has never encountered it. Responses simply miss the point and show little evidence of relevant learning.
   
   Characteristics:
   - Student may respond with "I don't know"
   - Gives irrelevant comments that are off-topic
   - Provides factually inaccurate information
   - May parrot what they're "supposed to say" without understanding
   - Long responses that sound impressive but don't answer the question
   
   Question Examples:
   - "What is X?" (basic recall, no comprehension needed)
   - "Define Y in one word"
   - "Which of these is an example of Z?"
   
   Key Point: Test if student has encountered the term/concept at all, not whether they understand it.

2. UNISTRUCTURAL (Surface Learning - Quantitative):
   Definition: Student understands only ONE or TWO elements of the task but misses many important parts needed for true understanding. Knowledge remains at terminology level.
   
   Characteristics:
   - Can identify and name a few things
   - Knows some relevant terms but can't explain them in depth
   - Can follow simple procedures that were explicitly taught
   - Gives vague or general answers
   - Missing critical components of full understanding
   
   Question Examples:
   - "What is the main characteristic of X?"
   - "Name the process that does Y"
   - "Which term describes Z?"
   
   Key Point: Student focuses on ONE aspect but ignores other important elements. Like a single puzzle piece in isolation.

3. MULTISTRUCTURAL (Surface Learning - Quantitative):
   Definition: Student has acquired lots of knowledge but can't put it together yet. Knowledge remains at the level of remembering, memorizing, and listing. Surface-level understanding - like having all Ikea furniture pieces spread on the floor but not knowing how to assemble them.
   
   Characteristics:
   - Can list multiple facts, components, or characteristics
   - Knowledge remains fragmented and disconnected
   - Cannot see relationships between parts
   - Cannot apply concepts in new or innovative ways
   - Heavy focus on memorization and enumeration
   - Assessment is primarily quantitative (counting facts)
   
   Question Examples:
   - "List the components of X"
   - "What are the characteristics of Y?"
   - "Name all the factors involved in Z"
   - "Which of these are features of X?" (lists multiple independent items)
   
   Key Point: Student knows many separate pieces but cannot connect them. No systemic thinking yet.

4. RELATIONAL (Deep Learning - Qualitative):
   Definition: Student sees how parts of a topic fit together. A QUALITATIVE CHANGE occurs - no longer just listing facts but understanding the integrated whole. First level showing deep understanding.
   
   Characteristics:
   - Can identify patterns and connections
   - Explains how parts link together into a coherent system
   - Can compare and contrast different elements
   - Views topic from multiple perspectives
   - Uses systemic and theoretical modeling
   - Understands cause-and-effect relationships
   - Can explain WHY things work the way they do
   
   Question Examples:
   - "How does X affect Y?"
   - "What is the relationship between A and B?"
   - "Compare and contrast X and Y"
   - "Why does Z happen when X is present?"
   - "Explain how these parts work together as a system"
   
   Key Point: Moving from "knowing facts" to "understanding systems." Student can see the big picture.

5. EXTENDED ABSTRACT (Deep Learning - Qualitative):
   Definition: Student has sophisticated understanding and can apply knowledge in various contexts BEYOND what was directly taught. Essence is going beyond what was given. Creates new knowledge through deep understanding.
   
   Characteristics:
   - Can apply knowledge to entirely new and different contexts
   - Generates theoretical ideas
   - Makes predictions about future events using principles learned
   - Can create new combinations of ideas
   - Understands principles at an abstract level
   - Can work with knowledge outside the classroom/original context
   - Sophisticated, nuanced understanding
   
   Question Examples:
   - "What would happen if X were different?"
   - "How would you apply principles of X in a completely new situation Y?"
   - "If we changed Z, what would be the consequences?"
   - "How would concept X change our understanding of unrelated field Y?"
   - "Predict what would happen when you apply X to scenario Z"
   
   Key Point: Student can transfer knowledge to NEW contexts and generate NEW knowledge. Highest level of thinking.

IMPORTANT NOTES:
- Levels 1-3 are SURFACE learning (quantitative, fact-focused)
- Levels 4-5 are DEEP learning (qualitative, understanding-focused)
- Each level builds on the previous one
- Questions should test ONLY the specified level, not multiple levels
"""
        
        # Use more content for better context (1000 chars instead of 500)
        content_preview = content[:1000]
        
        prompts = {
            'prestructural': f"""{solo_definitions}

TASK: Create a PRESTRUCTURAL level question based on the content about '{context}'.

THIS LEVEL TESTS: Basic recognition and recall with minimal understanding. Student may not understand the topic at all.

REQUIREMENTS:
✓ Question should test if student has heard of or can identify a BASIC TERM/CONCEPT
✓ No deep understanding required - just recognition
✓ Question should be simple and direct
✓ Example patterns:
  - "What is [term]?"
  - "Which of these is an example of [concept]?"
  - "What does [term] mean?" (basic definition)
✓ Keep question under 150 characters (SHORT and SIMPLE)
✓ Keep each option under 120 characters
✓ Create 4 multiple choice options (A, B, C, D)
✓ Only ONE correct answer
✓ Explanation should be brief (under 250 characters)

WHAT NOT TO DO:
✗ Don't ask about relationships or connections
✗ Don't require listing multiple items
✗ Don't ask students to explain WHY or HOW
✗ Don't make it trick questions or too complex
✗ Don't ask students to apply knowledge to new situations

Content: {content_preview}

Return ONLY valid JSON with these fields:
{{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ...", "explanation": "..."}}

IMPORTANT: Return ONLY the JSON object, no other text. Make questions SIMPLE and test RECOGNITION only.""",
            
            'unistructural': f"""{solo_definitions}

TASK: Create a UNISTRUCTURAL level question based on the content about '{context}'.

THIS LEVEL TESTS: Understanding of ONE or TWO specific elements from the content. Student knows some key concepts but hasn't yet seen the broader picture or multiple aspects.

REQUIREMENTS:
✓ Question should focus on ONE main aspect, characteristic, or concept from the content
✓ Student should be able to identify or explain a SINGLE important element
✓ Question can ask about simple cause-effect or a single relationship
✓ Example patterns:
  - "What is the main characteristic/purpose of [single concept]?"
  - "What does [single element] do or represent?"
  - "Which of these best describes [one specific aspect]?"
  - "What is the primary function/role of [single thing]?"
✓ Keep question under 150 characters
✓ Keep each option under 120 characters
✓ Create 4 multiple choice options (A, B, C, D)
✓ Only ONE correct answer
✓ Explanation should be brief (under 250 characters)

WHAT NOT TO DO:
✗ Don't ask about multiple unrelated components
✗ Don't ask how different parts connect or relate
✗ Don't require listing multiple items
✗ Don't ask students to compare or contrast
✗ Don't ask about broader systems or integrated understanding
✗ Don't ask students to apply to new situations

Content: {content_preview}

Return ONLY valid JSON with these fields:
{{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ...", "explanation": "..."}}

IMPORTANT: Return ONLY the JSON object, no other text. Questions should focus on ONE element only.""",
            
            'multistructural': f"""{solo_definitions}

TASK: Create a MULTISTRUCTURAL level question based on the content about '{context}'.

THIS LEVEL TESTS: Multiple independent facts, components, or characteristics that are NOT connected. Student knows the pieces but can't see how they relate.

REQUIREMENTS:
✓ Question should ask student to LIST or IDENTIFY multiple separate items
✓ The listed items should NOT require explaining HOW they connect
✓ Question should enumerate components, features, or characteristics
✓ Example patterns:
  - "Which of these are characteristics/components/features of [topic]?"
  - "List the factors/parts/elements involved in [concept]"
  - "What are the different [plural noun] that [verb]?"
  - "Which of these are examples of [concept]?" (multiple independent examples)
✓ Keep question under 150 characters
✓ Keep each option under 120 characters
✓ Create 4 multiple choice options (A, B, C, D) where CORRECT option lists multiple items
✓ Only ONE correct answer
✓ Explanation should be brief (under 250 characters)

WHAT NOT TO DO:
✗ Don't ask HOW or WHY things are related
✗ Don't ask about cause-and-effect
✗ Don't ask students to compare or contrast
✗ Don't ask about relationships between items
✗ Don't require system-level thinking
✗ Don't ask students to apply to new situations

Content: {content_preview}

Return ONLY valid JSON with these fields:
{{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ...", "explanation": "..."}}

IMPORTANT: Return ONLY the JSON object, no other text. Question should test LISTING or IDENTIFYING, not UNDERSTANDING relationships.""",
            
            'relational': f"""{solo_definitions}

TASK: Create a RELATIONAL level question based on the content about '{context}'.

THIS LEVEL TESTS: How parts connect and work together as an integrated system. Student understands cause-and-effect, relationships, and patterns. Deep understanding of how things fit together.

REQUIREMENTS:
✓ Question should ask about RELATIONSHIPS, CONNECTIONS, or INTEGRATION
✓ Student must show understanding of HOW or WHY things relate
✓ Question should require seeing patterns or systems
✓ Example patterns:
  - "How does [X] affect [Y]?"
  - "What is the relationship between [A] and [B]?"
  - "Why does [X] happen when [Y] is present?"
  - "Compare and contrast [A] and [B]"
  - "Explain how [components] work together to create [result]"
  - "What pattern connects [X] and [Y]?"
✓ Keep question under 150 characters
✓ Keep each option under 120 characters
✓ Create 4 multiple choice options (A, B, C, D)
✓ Correct answer should explain a CONNECTION or RELATIONSHIP
✓ Only ONE correct answer
✓ Explanation should clarify the relationship (under 250 characters)

WHAT NOT TO DO:
✗ Don't just ask for definitions or names
✗ Don't ask for simple lists without connections
✗ Don't ask about applying to completely new contexts
✗ Don't make it only require basic recall
✗ Don't avoid asking about systematic thinking

Content: {content_preview}

Return ONLY valid JSON with these fields:
{{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ...", "explanation": "..."}}

IMPORTANT: Return ONLY the JSON object, no other text. Question MUST require understanding of HOW/WHY things connect and work together.""",
            
            'extended_abstract': f"""{solo_definitions}

TASK: Create an EXTENDED ABSTRACT level question based on the content about '{context}'.

THIS LEVEL TESTS: Ability to apply knowledge to NEW contexts not directly taught. Student creates new knowledge and can generalize principles. Highest level of cognitive thinking.

REQUIREMENTS:
✓ Question should ask student to apply content to a NEW, DIFFERENT context or hypothetical situation
✓ The situation should NOT be directly mentioned in the source content
✓ Student must use principles learned to work with something unfamiliar
✓ Example patterns:
  - "What would happen if [different scenario] occurred?"
  - "How would you apply [principle from content] to [completely new situation]?"
  - "If we changed [variable], what would be the consequences?"
  - "Predict what would happen when [new context] is combined with [principle]"
  - "How might [new field/situation] be affected by [principle learned]?"
✓ Keep question under 150 characters
✓ Keep each option under 120 characters
✓ Create 4 multiple choice options (A, B, C, D)
✓ Correct answer should show transfer of learning to new context
✓ Only ONE correct answer
✓ Explanation should show why the principle transfers (under 250 characters)

WHAT NOT TO DO:
✗ Don't ask questions directly answered in the content
✗ Don't ask for simple recall or definitions
✗ Don't ask for basic listings
✗ Don't ask only about relationships within the original content
✗ Don't make the new context too similar to original (must be genuinely different)

Content: {content_preview}

Return ONLY valid JSON with these fields:
{{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ...", "explanation": "..."}}

IMPORTANT: Return ONLY the JSON object, no other text. Question MUST require applying knowledge to a NEW scenario not directly in the content."""
        }
        
        return prompts.get(level, prompts['prestructural'])
    
    def _call_api(self, prompt: str) -> str:
        """Call OpenRouter API"""
        try:
            api_key = self.api_keys[self.current_key_index]
            
            if api_key == 'mock':
                return None
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "SOLO Quiz Generator"
            }
            
            data = {
                "model": "tngtech/deepseek-r1t2-chimera:free",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 800
            }
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            elif response.status_code == 429:
                # Rate limit - try next key
                print(f"Rate limited on key {self.current_key_index}. Trying next key...")
                if self.current_key_index < len(self.api_keys) - 1:
                    self.current_key_index += 1
                    return self._call_api(prompt)
                else:
                    print("All API keys rate limited")
                    return None
            else:
                print(f"API error {response.status_code}: {response.text[:200]}")
                return None
            
        except requests.Timeout:
            print("API request timeout")
            return None
        except Exception as e:
            print(f"API call error: {str(e)}")
            return None
    
    def _parse_question_response(self, response: str) -> Dict[str, Any]:
        """Parse API response to extract question data and validate length"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                return self._validate_and_clean_question(parsed)
            else:
                return None
        except json.JSONDecodeError:
            return None
    
    def _validate_and_clean_question(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean question data to ensure reasonable lengths
        
        Args:
            question_data: Raw question data from API
            
        Returns:
            Cleaned question data with enforced length limits
        """
        try:
            # Enforce length limits
            MAX_QUESTION_LEN = 200  # Maximum characters for question
            MAX_ANSWER_LEN = 150    # Maximum characters for answer/option
            MAX_EXPLANATION_LEN = 300  # Maximum characters for explanation
            
            # Clean question
            if 'question' in question_data:
                q = question_data['question']
                if len(q) > MAX_QUESTION_LEN:
                    # Try to find first sentence
                    sentences = q.split('?')
                    question_data['question'] = sentences[0] + '?' if sentences else q[:MAX_QUESTION_LEN]
            
            # Clean options
            if 'options' in question_data and isinstance(question_data['options'], list):
                cleaned_options = []
                for opt in question_data['options']:
                    if len(opt) > MAX_ANSWER_LEN:
                        # Truncate at word boundary
                        truncated = opt[:MAX_ANSWER_LEN]
                        last_space = truncated.rfind(' ')
                        if last_space > 20:
                            truncated = truncated[:last_space] + '...'
                        cleaned_options.append(truncated)
                    else:
                        cleaned_options.append(opt)
                question_data['options'] = cleaned_options
            
            # Clean correct answer
            if 'correct_answer' in question_data:
                ans = question_data['correct_answer']
                if len(ans) > MAX_ANSWER_LEN:
                    truncated = ans[:MAX_ANSWER_LEN]
                    last_space = truncated.rfind(' ')
                    if last_space > 20:
                        truncated = truncated[:last_space] + '...'
                    question_data['correct_answer'] = truncated
            
            # Clean explanation
            if 'explanation' in question_data:
                exp = question_data['explanation']
                if len(exp) > MAX_EXPLANATION_LEN:
                    sentences = exp.split('. ')
                    cleaned_exp = sentences[0]
                    if len(cleaned_exp) > MAX_EXPLANATION_LEN:
                        cleaned_exp = cleaned_exp[:MAX_EXPLANATION_LEN-3] + '...'
                    question_data['explanation'] = cleaned_exp
            
            return question_data
        except Exception as e:
            print(f"Error validating question: {str(e)}")
            return question_data
    
    
    def _generate_mock_question(self, content: str, level: str, context: str) -> Dict[str, Any]:
        """Generate mock question for testing - extracts real content for better fallback"""
        
        # Extract key terms from content
        sentences = content.split('.')
        key_sentence = sentences[0] if sentences else content[:100]
        
        # Extract some key words from content
        words = [w.strip() for w in content.split() if len(w) > 5 and w[0].isupper()]
        key_term = words[0] if words else "concept"
        
        level_templates = {
            'prestructural': {
                'question': f"What is {key_term}?",
                'options': [
                    f'A) {key_sentence[:50]}...',
                    'B) A type of technology',
                    'C) An irrelevant concept',
                    'D) A historical fact'
                ],
                'correct_answer': f'A) {key_sentence[:50]}...',
                'explanation': f'This prestructural question tests basic recognition of {key_term} from the content.'
            },
            'unistructural': {
                'question': f"What is the main characteristic or role of {key_term} in '{context}'?",
                'options': [
                    f'A) It provides {key_sentence[:40]}',
                    'B) It has no specific function',
                    'C) It contradicts other concepts',
                    'D) It is completely unrelated'
                ],
                'correct_answer': f'A) It provides {key_sentence[:40]}',
                'explanation': 'This unistructural question tests understanding of ONE main aspect or characteristic of a concept.'
            },
            'multistructural': {
                'question': f"Which of these are components or characteristics mentioned in '{context}'?",
                'options': [
                    'A) Energy flow, populations, and ecosystems',
                    'B) Only abstract concepts',
                    'C) Personal opinions',
                    'D) Random unrelated facts'
                ],
                'correct_answer': 'A) Energy flow, populations, and ecosystems',
                'explanation': 'This multistructural question identifies multiple components without explaining their relationships.'
            },
            'relational': {
                'question': f"How do the different aspects in '{context}' connect to form a coherent understanding?",
                'options': [
                    'A) They are completely independent',
                    'B) They work together in an integrated system',
                    'C) Only one aspect is important',
                    'D) They contradict each other'
                ],
                'correct_answer': 'B) They work together in an integrated system',
                'explanation': 'This relational question asks about how concepts integrate and relate to each other systemically.'
            },
            'extended_abstract': {
                'question': f"If we applied the principles from '{context}' to a new situation, what might we predict?",
                'options': [
                    'A) The principles cannot be applied elsewhere',
                    'B) We could predict outcomes in similar systems',
                    'C) The concepts are too specific to one context',
                    'D) There is no way to transfer this knowledge'
                ],
                'correct_answer': 'B) We could predict outcomes in similar systems',
                'explanation': 'This extended abstract question requires transferring learned principles to new, hypothetical scenarios.'
            }
        }
        
        return level_templates.get(level, level_templates['prestructural'])
