import os
import json
import re
from datetime import datetime
from dotenv import load_dotenv
import requests
from typing import Dict, List, Any

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

class SoloQuizGenerator:
    """
    SOLO Taxonomy Quiz Generator
    Generates educational quizzes from text content using SOLO taxonomy levels
    Supports OpenRouter API with GitHub Models as fallback
    """
    
    def __init__(self):
        """Initialize the quiz generator with API configuration"""
        # OpenRouter API keys
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
        
        # GitHub Models API token (fallback)
        self.github_token = os.getenv('GITHUB_TOKEN')
        
        if not self.api_keys:
            print("Warning: No OpenRouter API keys configured.")
            self.api_keys = ['mock']
        else:
            print(f"[INIT] OpenRouter: {len(self.api_keys)} API keys loaded")
        
        if not self.github_token:
            print("[INIT] Warning: No GitHub token configured for fallback model.")
        else:
            print(f"[INIT] GitHub Models: Token loaded ({self.github_token[:30]}...)")
        
        self.current_key_index = 0
        self.provider = "openrouter"
        self.api_exhausted = False
    
    def generate_quiz(self, content: str, filename: str, config: Dict[str, Any] = None, resume_from_chapter: int = 1, existing_quiz: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main method to generate quiz from content with resume capability
        
        Args:
            content: Text content to generate quiz from
            filename: Name of the uploaded file
            config: Optional configuration dict with keys:
                - total_questions: int or None (None = let model decide)
                - question_mode: 'auto' or 'manual'
                - solo_distribution: dict with level percentages or None
                - distribution_mode: 'auto' or 'manual'
                - use_smart_chunking: bool (default: True)
            resume_from_chapter: Chapter number to resume from (default: 1)
            existing_quiz: Existing quiz data to resume (optional)
            
        Returns:
            Dictionary containing quiz data with chapters and questions
        """
        try:
            is_resuming = resume_from_chapter > 1 or existing_quiz is not None
            if is_resuming:
                print(f"\n[RESUME] Continuing quiz from chapter {resume_from_chapter}")
            else:
                print(f"\n[START] Generating quiz from: {filename}")
            print(f"[PROVIDERS] Primary: OpenRouter (9 keys) | Fallback: GitHub Models gpt-4o")
            # Use smart chunking by default
            chapters = self._split_into_chapters_smart(content, config)
            
            # Cap chapters to limit total questions to ~25 (API constraint: 50 prompts/day)
            # With 2-3 questions per chapter, max chapters = 10
            max_chapters = 10
            if len(chapters) > max_chapters:
                chapters = chapters[:max_chapters]
            
            # Determine config
            if config is None:
                config = {}
            
            # Determine total questions
            if config.get('question_mode') == 'auto' or config.get('total_questions') is None:
                # Auto mode: calculate based on content length and chapters
                # More intelligent calculation: base on content length + chapter count
                content_length = len(content)
                chapter_count = len(chapters)
                
                # Base calculation: roughly 1 question per 500 characters, min 2-3 per chapter
                questions_by_length = max(3, content_length // 500)
                questions_by_chapters = chapter_count * 2
                
                # Use the higher of the two to avoid too few questions for continuous text
                total_questions = max(questions_by_length, questions_by_chapters)
                # Cap at 25 questions (OpenRouter API limit: 50 prompts per day)
                total_questions = min(total_questions, 25)
                
                question_mode = 'auto'
            else:
                total_questions = min(config.get('total_questions', len(chapters) * 2), 25)
                question_mode = 'manual'
            
            # Determine SOLO distribution
            if config.get('distribution_mode') == 'auto' or config.get('solo_distribution') is None:
                # Auto mode: use balanced distribution (4 SOLO levels)
                solo_distribution = {
                    'unistructural': 0.20,
                    'multistructural': 0.30,
                    'relational': 0.30,
                    'extended_abstract': 0.20
                }
                distribution_mode = 'auto'
            else:
                solo_distribution = config.get('solo_distribution', {
                    'unistructural': 0.20,
                    'multistructural': 0.30,
                    'relational': 0.30,
                    'extended_abstract': 0.20
                })
                distribution_mode = 'manual'
            
            # Initialize or resume quiz data
            if existing_quiz is not None:
                quiz_data = existing_quiz
                questions_generated = quiz_data['metadata']['progress']['questions_generated']
                # Remove the "API Limit Reached" placeholder if it exists
                quiz_data['chapters'] = [ch for ch in quiz_data['chapters'] if ch.get('title') != '⚠️ API Limit Reached']
            else:
                quiz_data = {
                    'metadata': {
                        'filename': filename,
                        'generated_at': datetime.now().isoformat(),
                        'total_chapters': len(chapters),
                        'total_questions': 0,
                        'question_mode': question_mode,
                        'distribution_mode': distribution_mode,
                        'config': config,
                        'progress': {
                            'chapters_completed': 0,
                            'total_chapters': len(chapters),
                            'questions_generated': 0,
                            'total_questions_target': total_questions
                        }
                    },
                    'chapters': []
                }
                questions_generated = 0
            
            questions_per_chapter = max(1, total_questions // len(chapters)) if chapters else 2
            
            # Generate questions for each chapter (resume from specified chapter)
            for idx in range(resume_from_chapter - 1, len(chapters)):
                if questions_generated >= total_questions or self.api_exhausted:
                    break
                
                chapter_content = chapters[idx]
                    
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
                    # Check if we got actual questions or if API is exhausted
                    if chapter_data.get('questions'):
                        quiz_data['chapters'].append(chapter_data)
                        questions_generated += len(chapter_data.get('questions', []))
                        quiz_data['metadata']['total_questions'] = questions_generated
                        quiz_data['metadata']['progress']['chapters_completed'] = idx + 1
                        quiz_data['metadata']['progress']['questions_generated'] = questions_generated
                    else:
                        # No questions generated - API exhausted
                        if self.api_exhausted:
                            break
            
            # If API was exhausted, add a note chapter
            if self.api_exhausted or (questions_generated < total_questions and questions_generated > 0):
                next_chapter = len(quiz_data['chapters']) + 1
                quiz_data['chapters'].append({
                    'chapter_number': next_chapter,
                    'title': '⚠️ API Limit Reached',
                    'content_preview': 'Quiz generation was limited by API constraints.',
                    'questions': [{
                        'solo_level': 'info',
                        'question_data': {
                            'question': 'Quiz generation stopped due to API limits',
                            'explanation': f'Generated {questions_generated}/{total_questions} questions. Click "Resume Quiz" to continue from chapter {next_chapter}.',
                            'options': [f'Note: Resume from chapter {next_chapter}'],
                            'correct_answer': f'Note: Resume from chapter {next_chapter}'
                        }
                    }]
                })
                quiz_data['metadata']['resume_from_chapter'] = next_chapter
            
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
            'unistructural': 0.25,
            'multistructural': 0.30,
            'relational': 0.30,
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
                'unistructural': 0.20,
                'multistructural': 0.30,
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
            
            # Calculate questions per level based on distribution (all 4 SOLO levels)
            solo_levels = ['unistructural', 'multistructural', 'relational', 'extended_abstract']
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
            Dictionary with question data, or None if API unavailable
        """
        try:
            if self.api_keys[0] == 'mock':
                print(f"Using mock questions (no API keys configured)")
                return None
            
            # Call API to generate question
            prompt = self._build_prompt(content, level, context)
            response = self._call_api(prompt)
            
            if response:
                parsed = self._parse_question_response(response)
                if parsed:
                    return parsed
                else:
                    print(f"Failed to parse API response for {level}. API exhausted.")
                    return None
            else:
                print(f"API returned None for {level} question. API exhausted.")
                return None
                
        except Exception as e:
            print(f"Error generating {level} question: {str(e)}")
            return None
    
    def _build_prompt(self, content: str, level: str, context: str) -> str:
        """Build optimized prompt with detailed SOLO Taxonomy definitions"""
        
        # Keep content preview SHORT (600 chars)
        content_preview = content[:600]
        
        prompts = {
            'unistructural': f"""Create a UNISTRUCTURAL level question about '{context}'.

Content: {content_preview}

UNISTRUCTURAL LEVEL DEFINITION:
At this stage, the learner gets to know just a single relevant aspect of a task or subject; the student gets a basic understanding of a concept or task. Therefore, a student is able to make easy and apparent connections, but he or she does not have any idea how significant that information be or not. In addition, the students' response indicates a concrete understanding of the task, but it focuses on only one relevant aspect.

TASK: Create a question that tests knowledge of ONE specific fact/concept. Student should identify or name a single element directly stated in the content.

Requirements:
- Focus on ONE isolated aspect only
- No connections to other concepts required
- Question < 150 chars
- 4 MC options (A-D), one correct
- Explanation < 250 chars

Return ONLY JSON: {{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ...", "explanation": "..."}}""",

            'multistructural': f"""Create a MULTISTRUCTURAL level question about '{context}'.

Content: {content_preview}

MULTISTRUCTURAL LEVEL DEFINITION:
At this stage, students gain an understanding of numerous relevant independent aspects. Despite understanding the relationship between different aspects, its relationship to the whole remains unclear. Suppose the teacher is teaching about several topics and ideas, the students can make varied connections, but they fail to understand the significance of the whole. The students' responses are based on relevant aspects, but their responses are handled independently.

TASK: Create a question that tests knowledge of MULTIPLE separate facts/features. Student should list or identify several independent elements WITHOUT explaining how they connect.

Requirements:
- Multiple items or aspects, but handled independently
- Don't require showing relationships between items
- Question < 150 chars
- 4 MC options (A-D), one correct
- Explanation < 250 chars

Return ONLY JSON: {{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ...", "explanation": "..."}}""",

            'relational': f"""Create a RELATIONAL level question about '{context}'.

Content: {content_preview}

RELATIONAL LEVEL DEFINITION:
This stage relates to aspects of knowledge combining to form a structure. By this stage, the student is able to understand the importance of different parts in relation to the whole. They are able to connect concepts and ideas, so it provides a coherent knowledge of the whole thing. Moreover, the students' response indicates an understanding of the task by combining all the parts, and they can demonstrate how each part contributes to the whole.

TASK: Create a question that tests understanding of HOW parts CONNECT and work TOGETHER. Student should explain relationships, patterns, or cause-effect between elements. Shows deep integrated understanding.

Requirements:
- Ask about relationships, connections, or cause-effect WITHIN the content
- Require understanding of how parts fit together into a coherent whole
- Student must show how different elements relate to each other
- Question < 150 chars
- 4 MC options (A-D), one correct
- Explanation < 250 chars

Return ONLY JSON: {{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ...", "explanation": "..."}}""",

            'extended_abstract': f"""Create an EXTENDED ABSTRACT level question about '{context}'.

Content: {content_preview}

EXTENDED ABSTRACT LEVEL DEFINITION:
By this level, students are able to make connections within the provided task, and they also create connections beyond that. They develop the ability to transfer and generalise the concepts and principles from one subject area into a particular domain. Therefore, the students' response indicates that they can conceptualise beyond the level of what has been taught. They are able to propose new concepts and ideas depending on their understanding of the task or subject taught.

TASK: Create a question that tests ability to APPLY knowledge to NEW contexts NOT in the content. Student should predict, generalize, or solve scenarios beyond what was directly taught. Requires transfer of learning to new domains.

Requirements:
- Ask about applying/generalizing content to a NEW different situation
- Scenario should NOT be directly mentioned in the content
- Requires student to conceptualize beyond what was taught
- Student must demonstrate ability to transfer knowledge to new contexts
- Question < 150 chars
- 4 MC options (A-D), one correct
- Explanation < 250 chars

Return ONLY JSON: {{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ...", "explanation": "..."}}"""
        }
        
        return prompts.get(level, prompts['unistructural'])
    
    def _call_api(self, prompt: str) -> str:
        """
        Call API for question generation
        Primary: OpenRouter API with key rotation (9 keys)
        Fallback: GitHub Models API
        """
        try:
            api_key = self.api_keys[self.current_key_index]
            
            if api_key == 'mock':
                return None
            
            # OpenRouter request
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
                print(f"[OK] OpenRouter key {self.current_key_index + 1}/{len(self.api_keys)}")
                return response.json()["choices"][0]["message"]["content"]
            elif response.status_code == 429:
                # Rate limited - try next key
                print(f"[429] Rate limited on key {self.current_key_index + 1}/{len(self.api_keys)}")
                if self.current_key_index < len(self.api_keys) - 1:
                    self.current_key_index += 1
                    return self._call_api(prompt)
                else:
                    # All OpenRouter keys exhausted - try GitHub
                    print("[FALLBACK] All OpenRouter keys rate-limited. Switching to GitHub Models...")
                    github_result = self._call_github_api(prompt)
                    if github_result:
                        return github_result
                    else:
                        print("[CRITICAL] Both OpenRouter AND GitHub Models APIs are exhausted!")
                        self.api_exhausted = True
                        return None
            else:
                # Other error - try next key
                print(f"[{response.status_code}] OpenRouter error. Trying next key...")
                if self.current_key_index < len(self.api_keys) - 1:
                    self.current_key_index += 1
                    return self._call_api(prompt)
                else:
                    print("[FALLBACK] All OpenRouter keys failed. Switching to GitHub Models...")
                    return self._call_github_api(prompt)
            
        except requests.Timeout:
            print("[TIMEOUT] Request timeout - trying fallback")
            if self.current_key_index < len(self.api_keys) - 1:
                self.current_key_index += 1
                return self._call_api(prompt)
            else:
                return self._call_github_api(prompt)
        except Exception as e:
            print(f"[ERROR] API call error: {type(e).__name__}: {str(e)}")
            if self.current_key_index < len(self.api_keys) - 1:
                self.current_key_index += 1
                return self._call_api(prompt)
            else:
                print("[FALLBACK] All OpenRouter keys failed. Trying GitHub Models...")
                return self._call_github_api(prompt)
    
    def _call_github_api(self, prompt: str) -> str:
        """Call GitHub Models API (gpt-4o) as fallback"""
        try:
            if not self.github_token:
                print("[ERROR] GitHub token not configured - cannot use fallback API")
                self.api_exhausted = True
                return None
            
            print("[GitHub API] Calling gpt-4o model...")
            headers = {
                "Authorization": f"Bearer {self.github_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": "You are a helpful educational assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 800,
                "top_p": 1
            }
            
            response = requests.post(
                "https://models.github.ai/inference/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                print("[SUCCESS] GitHub Models API working (gpt-4o)")
                return response.json()["choices"][0]["message"]["content"]
            elif response.status_code == 429:
                print("[RATE_LIMIT] GitHub Models also rate-limited (quota exhausted)")
                self.api_exhausted = True
                return None
            else:
                print(f"[GitHub API Error] Status {response.status_code}: {response.text[:300]}")
                return None
                
        except requests.Timeout:
            print("[GitHub API] Request timeout (30s)")
            self.api_exhausted = True
            return None
        except requests.ConnectionError as e:
            print(f"[GitHub API] Connection error: {str(e)}")
            self.api_exhausted = True
            return None
        except Exception as e:
            print(f"[GitHub API Exception] {type(e).__name__}: {str(e)}")
            self.api_exhausted = True
            return None
    
    def _parse_question_response(self, response: str) -> Dict[str, Any]:
        """Parse API response to extract question data"""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                return self._validate_and_clean_question(parsed)
            else:
                return None
        except json.JSONDecodeError:
            return None
    
    def _validate_and_clean_question(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean question data to enforce reasonable lengths"""
        try:
            MAX_QUESTION_LEN = 200
            MAX_ANSWER_LEN = 150
            MAX_EXPLANATION_LEN = 300
            
            # Clean question
            if 'question' in question_data:
                q = question_data['question']
                if len(q) > MAX_QUESTION_LEN:
                    sentences = q.split('?')
                    question_data['question'] = sentences[0] + '?' if sentences else q[:MAX_QUESTION_LEN]
            
            # Clean options
            if 'options' in question_data and isinstance(question_data['options'], list):
                cleaned_options = []
                for opt in question_data['options']:
                    if len(opt) > MAX_ANSWER_LEN:
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

