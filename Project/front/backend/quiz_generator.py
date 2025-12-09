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
                
                # Base calculation: roughly 1 question per 500 characters, min 4 per chapter
                questions_by_length = max(4, content_length // 500)
                questions_by_chapters = chapter_count * 4
                
                # Use the higher of the two to avoid too few questions for continuous text
                total_questions = max(questions_by_length, questions_by_chapters)
                # Cap at reasonable max (100 questions)
                total_questions = min(total_questions, 100)
                
                question_mode = 'auto'
            else:
                total_questions = config.get('total_questions', len(chapters) * 4)
                question_mode = 'manual'
            
            # Determine SOLO distribution
            if config.get('distribution_mode') == 'auto' or config.get('solo_distribution') is None:
                # Auto mode: use balanced distribution
                solo_distribution = {
                    'prestructural': 0.15,
                    'multistructural': 0.35,
                    'relational': 0.35,
                    'extended_abstract': 0.15
                }
                distribution_mode = 'auto'
            else:
                solo_distribution = config.get('solo_distribution', {
                    'prestructural': 0.15,
                    'multistructural': 0.35,
                    'relational': 0.35,
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
            questions_per_chapter = max(1, total_questions // len(chapters)) if chapters else 4
            
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
        return self._process_chapter_smart(chapter_content, chapter_num, 4, {
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
                'prestructural': 0.20,
                'multistructural': 0.20,
                'relational': 0.30,
                'extended_abstract': 0.10
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
            
            # Calculate questions per level based on distribution (only 4 SOLO levels)
            solo_levels = ['prestructural', 'multistructural', 'relational', 'extended_abstract']
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
SOLO TAXONOMY - DETAILED LEVEL DEFINITIONS (Based on Biggs & Collis):

1. PRESTRUCTURAL: The task is not attacked appropriately; the student hasn't really understood the point and uses too simple a way of going about it. Students respond with irrelevant comments, exhibit lack of understanding, often missing the point entirely.
   - Questions test basic recognition of terms with minimal understanding
   - Simple identification without comprehension
   - "What is X?" (basic recall)

2. UNISTRUCTURAL: The student's response only focuses on one relevant aspect. Students give slightly relevant but vague answers that lack depth.
   - Focus on a single aspect or characteristic
   - Direct recognition or definition of a concept
   - "Define X" or "What does Y mean?"

3. MULTISTRUCTURAL: The student's response focuses on several relevant aspects but they are treated independently and additively. Assessment is primarily quantitative. Students may know the concept in bits but don't know how to connect or explain relationships.
   - Listing multiple characteristics or components
   - Enumeration without explaining connections between elements
   - "List the components of X" or "What are the characteristics of Y?"

4. RELATIONAL: The different aspects have become integrated into a coherent whole. This level represents adequate understanding of a topic. Students can identify various patterns and view a topic from distinct perspectives.
   - Explaining cause and effect relationships
   - Comparisons and contrasts
   - Analysis of relationships between concepts
   - "How does X affect Y?" or "Compare A and B"

5. EXTENDED ABSTRACT: The previous integrated whole may be conceptualized at a higher level of abstraction and generalized to a new topic or area. Students may apply classroom concepts in real life.
   - Application of knowledge in new situations
   - Hypotheses and predictions
   - Evaluation and creation of new approaches
   - "What would happen if..." or "How would you apply X in situation Y?"
"""
        
        # Use more content for better context (1000 chars instead of 500)
        content_preview = content[:1000]
        
        prompts = {
            'prestructural': f"""{solo_definitions}

TASK: Based on the content about '{context}' below, create a PRESTRUCTURAL level question.

REQUIREMENTS:
- Test basic recognition of terms with minimal understanding
- Simple identification or recall without deep comprehension
- Follow pattern: "What is X?" or "What does Y mean?"
- Keep question under 150 characters (SHORT, NOT PARAGRAPHS)
- Keep each option under 120 characters (concise answers)
- Create 4 multiple choice options (A, B, C, D)
- Only one correct answer
- Provide clear explanation (under 250 characters)

Content: {content_preview}

Return ONLY valid JSON with these fields:
{{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ...", "explanation": "..."}}

IMPORTANT: Return ONLY the JSON object, no other text. Make questions CONCISE, not wordy.""",
            
            'multistructural': f"""{solo_definitions}

TASK: Based on the content about '{context}' below, create a MULTISTRUCTURAL level question.

REQUIREMENTS:
- Focus on several relevant aspects that are treated independently
- Ask student to list multiple components or characteristics
- Do NOT ask about connections between elements
- Keep question under 150 characters (SHORT, NOT PARAGRAPHS)
- Keep each option under 120 characters (concise answers)
- Follow pattern: "List the components of X" or "Which of these are characteristics of Y?"
- Create 4 multiple choice options (A, B, C, D)
- Only one correct answer
- Provide clear explanation (under 250 characters)

Content: {content_preview}

Return ONLY valid JSON with these fields:
{{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ...", "explanation": "..."}}

IMPORTANT: Return ONLY the JSON object, no other text. Make questions CONCISE, not wordy.""",
            
            'relational': f"""{solo_definitions}

TASK: Based on the content about '{context}' below, create a RELATIONAL level question.

REQUIREMENTS:
- Integrate multiple aspects into a coherent whole
- Ask about cause-and-effect relationships
- Ask for comparisons and contrasts
- Ask how concepts are connected
- Keep question under 150 characters (SHORT, NOT PARAGRAPHS)
- Keep each option under 120 characters (concise answers)
- Follow pattern: "How does X affect Y?" or "What is the relationship between A and B?"
- Create 4 multiple choice options (A, B, C, D)
- Only one correct answer
- Provide clear explanation (under 250 characters)

Content: {content_preview}

Return ONLY valid JSON with these fields:
{{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ...", "explanation": "..."}}

IMPORTANT: Return ONLY the JSON object, no other text. Make questions CONCISE, not wordy.""",
            
            'extended_abstract': f"""{solo_definitions}

TASK: Based on the content about '{context}' below, create an EXTENDED ABSTRACT level question.

REQUIREMENTS:
- Ask student to apply concepts to new or hypothetical situations
- Go beyond the content with real-world application
- Ask for predictions, hypotheses, or creative solutions
- Keep question under 150 characters (SHORT, NOT PARAGRAPHS)
- Keep each option under 120 characters (concise answers)
- Follow pattern: "What would happen if...?" or "How would you apply X in situation Y?"
- Present a novel scenario not directly in the original content
- Create 4 multiple choice options (A, B, C, D)
- Only one correct answer
- Provide clear explanation (under 250 characters)

Content: {content_preview}

Return ONLY valid JSON with these fields:
{{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ...", "explanation": "..."}}

IMPORTANT: Return ONLY the JSON object, no other text. Make questions CONCISE, not wordy."""
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
