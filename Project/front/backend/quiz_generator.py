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
    
    def generate_quiz(self, content: str, filename: str) -> Dict[str, Any]:
        """
        Main method to generate quiz from content
        
        Args:
            content: Text content to generate quiz from
            filename: Name of the uploaded file
            
        Returns:
            Dictionary containing quiz data with chapters and questions
        """
        try:
            # Split content into chapters
            chapters = self._split_into_chapters(content)
            
            quiz_data = {
                'metadata': {
                    'filename': filename,
                    'generated_at': datetime.now().isoformat(),
                    'total_chapters': len(chapters),
                    'total_questions': 0
                },
                'chapters': []
            }
            
            # Generate questions for each chapter
            for idx, chapter_content in enumerate(chapters):
                chapter_data = self._process_chapter(chapter_content, idx + 1)
                if chapter_data:
                    quiz_data['chapters'].append(chapter_data)
                    quiz_data['metadata']['total_questions'] += len(chapter_data.get('questions', []))
            
            return quiz_data
            
        except Exception as e:
            print(f"Error in generate_quiz: {str(e)}")
            raise
    
    def _split_into_chapters(self, content: str) -> List[str]:
        """
        Split content into chapters based on headings
        
        Args:
            content: Full text content
            
        Returns:
            List of chapter contents
        """
        # Split by CHAPTER X: pattern or === headers or ALL CAPS headers
        chapter_pattern = r'CHAPTER\s+\d+:|={2,}.*?={2,}|\n[A-Z][A-Z\s]+\n(?=[A-Z])'
        
        parts = re.split(chapter_pattern, content)
        
        # Filter out empty parts and keep only substantial content
        chapters = [part.strip() for part in parts if part.strip() and len(part.strip()) > 100]
        
        # If no chapters found, split into chunks of ~500 words
        if not chapters:
            words = content.split()
            for i in range(0, len(words), 150):
                chunk = ' '.join(words[i:i+150])
                if len(chunk) > 100:
                    chapters.append(chunk)
        
        return chapters[:15]  # Limit to 15 chapters
    
    def _process_chapter(self, chapter_content: str, chapter_num: int) -> Dict[str, Any]:
        """
        Process a single chapter and generate questions
        
        Args:
            chapter_content: Text content of the chapter
            chapter_num: Chapter number
            
        Returns:
            Dictionary containing chapter data with questions
        """
        try:
            # Extract chapter title (first line)
            lines = chapter_content.split('\n')
            title = lines[0].strip() if lines else f"Chapter {chapter_num}"
            
            chapter_data = {
                'chapter_number': chapter_num,
                'title': title,
                'content_preview': chapter_content[:200] + '...',
                'questions': []
            }
            
            # Generate questions for each SOLO level
            # Generate 1-2 questions per level for better coverage
            solo_levels = ['prestructural', 'multistructural', 'relational', 'extended_abstract']
            
            for level in solo_levels:
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
- Create 4 multiple choice options (A, B, C, D)
- Only one correct answer
- Provide clear explanation traceable to content

Content: {content_preview}

Return ONLY valid JSON with these fields:
{{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ...", "explanation": "..."}}

IMPORTANT: Return ONLY the JSON object, no other text.""",
            
            'multistructural': f"""{solo_definitions}

TASK: Based on the content about '{context}' below, create a MULTISTRUCTURAL level question.

REQUIREMENTS:
- Focus on several relevant aspects that are treated independently
- Ask student to list multiple components or characteristics
- Do NOT ask about connections between elements
- Follow pattern: "List the components of X" or "Which of these are characteristics of Y?"
- Create 4 multiple choice options (A, B, C, D)
- Only one correct answer
- Provide clear explanation

Content: {content_preview}

Return ONLY valid JSON with these fields:
{{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ...", "explanation": "..."}}

IMPORTANT: Return ONLY the JSON object, no other text.""",
            
            'relational': f"""{solo_definitions}

TASK: Based on the content about '{context}' below, create a RELATIONAL level question.

REQUIREMENTS:
- Integrate multiple aspects into a coherent whole
- Ask about cause-and-effect relationships
- Ask for comparisons and contrasts
- Ask how concepts are connected
- Follow pattern: "How does X affect Y?" or "What is the relationship between A and B?"
- Create 4 multiple choice options (A, B, C, D)
- Only one correct answer
- Explain the integrated understanding required

Content: {content_preview}

Return ONLY valid JSON with these fields:
{{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ...", "explanation": "..."}}

IMPORTANT: Return ONLY the JSON object, no other text.""",
            
            'extended_abstract': f"""{solo_definitions}

TASK: Based on the content about '{context}' below, create an EXTENDED ABSTRACT level question.

REQUIREMENTS:
- Ask student to apply concepts to new or hypothetical situations
- Go beyond the content with real-world application
- Ask for predictions, hypotheses, or creative solutions
- Follow pattern: "What would happen if...?" or "How would you apply X in situation Y?"
- Present a novel scenario not directly in the original content
- Create 4 multiple choice options (A, B, C, D)
- Only one correct answer
- Explain how this demonstrates transfer of learning

Content: {content_preview}

Return ONLY valid JSON with these fields:
{{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ...", "explanation": "..."}}

IMPORTANT: Return ONLY the JSON object, no other text."""
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
        """Parse API response to extract question data"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return None
        except json.JSONDecodeError:
            return None
    
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
