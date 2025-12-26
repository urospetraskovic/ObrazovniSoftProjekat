import os
import json
import re
from datetime import datetime
from dotenv import load_dotenv
import requests
from typing import Dict, List, Any
import google.generativeai as genai

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

# Initialize Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class SoloQuizGenerator:
    """
    SOLO Taxonomy Quiz Generator
    Generates educational quizzes from text content using SOLO taxonomy levels
    Supports OpenRouter API with GitHub Models as fallback
    """
    
    def __init__(self):
        """Initialize the quiz generator with API configuration"""
        # Gemini API (Primary)
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel("gemini-2.0-flash")
            print("[INIT] Gemini API: Primary provider loaded")
        else:
            self.gemini_model = None
            print("[INIT] Warning: Gemini API key not configured")
        
        # Groq API (Secondary fallback)
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if self.groq_api_key:
            print(f"[INIT] Groq API: Configured (key loaded)")
        else:
            print("[INIT] Warning: Groq API key not configured")
        
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
        ]
        # Filter out None values
        self.api_keys = [key for key in self.api_keys if key]
        
        # GitHub Models API token (fallback)
        self.github_token = os.getenv('GITHUB_TOKEN')
        
        if not self.api_keys:
            print("[INIT] Warning: No OpenRouter API keys configured (fallback).")
            self.api_keys = ['mock']
        else:
            print(f"[INIT] OpenRouter: {len(self.api_keys)} API keys loaded (fallback)")
        
        if not self.github_token:
            print("[INIT] Warning: No GitHub token configured for fallback model.")
        else:
            print(f"[INIT] GitHub Models: Token loaded ({self.github_token[:30]}...)")
        
        self.current_key_index = 0
        self.provider = "gemini"  # Primary provider
        self.api_exhausted = False
        self._content_summary_cache = {}  # Cache summaries to avoid regenerating
    
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
                # Reset API exhaustion flag when resuming to allow more generations
                self.api_exhausted = False
                self.current_key_index = 0
            else:
                print(f"\n[START] Generating quiz from: {filename}")
            print(f"[PROVIDERS] Primary: OpenRouter (9 keys) | Fallback: GitHub Models gpt-4o")
            # Use smart chunking by default
            chapters = self._split_into_chapters_smart(content, config)
            
            # Cap chapters to limit total questions (API constraint)
            # For 50 questions max, allow up to 25 chapters (2 questions per chapter)
            max_chapters = 25
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
                
                # Base calculation: roughly 1 question per 500 characters, min 2 per chapter
                questions_by_length = max(3, content_length // 500)
                questions_by_chapters = chapter_count * 2
                
                # Use the higher of the two to avoid too few questions for continuous text
                total_questions = max(questions_by_length, questions_by_chapters)
                # Cap at 50 questions for comprehensive coverage of entire file
                total_questions = min(total_questions, 50)
                
                question_mode = 'auto'
            else:
                total_questions = min(config.get('total_questions', len(chapters) * 2), 50)
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
                # Continue until we reach target or API is exhausted
                if questions_generated >= total_questions:
                    break
                if self.api_exhausted and questions_generated == 0:
                    # Only break on exhaustion if we haven't generated anything this session
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
            
            # If API was exhausted and we have more chapters to process, add a resume note
            if self.api_exhausted and questions_generated > 0:
                # Find next unprocessed chapter
                next_chapter = quiz_data['metadata']['progress']['chapters_completed'] + 1
                if next_chapter <= len(chapters):
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
            elif questions_generated < total_questions and (resume_from_chapter - 1 + len([ch for ch in quiz_data['chapters'] if ch.get('title') != '⚠️ API Limit Reached'])) < len(chapters):
                # We didn't reach target but have more chapters - offer resume
                next_chapter = len(quiz_data['chapters']) + 1
                quiz_data['chapters'].append({
                    'chapter_number': next_chapter,
                    'title': '⚠️ More Content Available',
                    'content_preview': 'More content available to generate questions from.',
                    'questions': [{
                        'solo_level': 'info',
                        'question_data': {
                            'question': 'More content is available',
                            'explanation': f'Generated {questions_generated}/{total_questions} questions so far. Click "Resume Quiz" to continue from chapter {next_chapter}.',
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
        Prioritizes page-based splitting for PDF content to ensure full coverage
        
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
        
        # Strategy 0: Check for page markers (--- Page X ---) - best for PDF content
        # This ensures we cover the ENTIRE file from start to finish
        page_pattern = r'--- Page (\d+) ---'
        page_matches = list(re.finditer(page_pattern, content))
        
        if page_matches:
            # Found page markers - use page-based splitting for complete coverage
            chapters = self._split_by_page_ranges(content, page_matches)
            if chapters:
                return chapters
        
        # Strategy 1: Try to find existing chapter markers
        chapter_pattern = r'CHAPTER\s+\d+:|={2,}.*?={2,}|\n[A-Z][A-Z\s]+\n(?=[A-Z])'
        parts = re.split(chapter_pattern, content)
        chapters = [part.strip() for part in parts if part.strip() and len(part.strip()) > 200]
        
        # If found good chapters, use them (allow up to 25 for comprehensive coverage)
        if len(chapters) >= 2:
            return chapters[:25]
        
        # Strategy 2: Split by paragraph breaks (multiple newlines)
        paragraphs = re.split(r'\n\s*\n+', content)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        # Group paragraphs into semantic chunks
        if len(paragraphs) > 5:
            chapters = self._group_by_semantic_similarity(paragraphs)
            if chapters:
                return chapters[:25]
        
        # Strategy 3: Split by word count (roughly equal chunks)
        if len(paragraphs) > 1:
            return self._split_by_content_length(content, target_chunks=20)
        
        # Fallback: Return whole content as single chapter
        return [content]
    
    def _split_into_chapters(self, content: str) -> List[str]:
        """
        Basic chapter splitting fallback method
        Splits by common chapter markers or paragraph breaks
        
        Args:
            content: Full text content
            
        Returns:
            List of chapter contents
        """
        # Try common chapter markers
        chapter_pattern = r'(?:CHAPTER|Chapter|PART|Part)\s+\d+'
        parts = re.split(chapter_pattern, content)
        chapters = [p.strip() for p in parts if p.strip() and len(p.strip()) > 200]
        
        if len(chapters) >= 2:
            return chapters[:25]
        
        # Fallback to paragraph splitting
        paragraphs = content.split('\n\n')
        return [p.strip() for p in paragraphs if len(p.strip()) > 200][:25]
    
    def _generate_content_summary(self, content: str, chapter_context: str = "") -> str:
        """
        Generate a LOCAL summary from the content WITHOUT calling the API.
        Extracts key sentences to help with higher-order questions.
        This is a lightweight extraction, NOT an API call.
        
        Args:
            content: The text content to summarize
            chapter_context: Optional chapter title/context
            
        Returns:
            A summary string extracted from the content
        """
        # Check cache first
        cache_key = hash(content[:500])  # Use first 500 chars as key
        if cache_key in self._content_summary_cache:
            return self._content_summary_cache[cache_key]
        
        try:
            # LOCAL extraction - NO API CALL
            # Extract key sentences based on heuristics
            lines = content.split('\n')
            key_sentences = []
            
            for line in lines:
                line = line.strip()
                # Skip empty lines, page markers, and very short lines
                if not line or line.startswith('---') or len(line) < 30:
                    continue
                # Prioritize sentences with key indicators
                if any(keyword in line.lower() for keyword in [
                    'important', 'key', 'main', 'significant', 'essential',
                    'because', 'therefore', 'thus', 'result', 'cause',
                    'relationship', 'connection', 'leads to', 'affects',
                    'principle', 'concept', 'definition', 'means that'
                ]):
                    key_sentences.append(line)
                # Also include first substantive sentences
                elif len(key_sentences) < 3 and len(line) > 50:
                    key_sentences.append(line)
                
                # Limit to 5 key sentences
                if len(key_sentences) >= 5:
                    break
            
            # Build summary from extracted sentences
            summary = ' '.join(key_sentences[:5])
            
            # Limit summary length
            if len(summary) > 400:
                summary = summary[:400]
            
            # Cache it
            self._content_summary_cache[cache_key] = summary
            if summary:
                print(f"[SUMMARY] Extracted key points (no API call): {summary[:60]}...")
            return summary
            
        except Exception as e:
            print(f"[SUMMARY] Error extracting summary: {str(e)}")
            return ""
    
    def _analyze_page_density(self, content: str, page_matches) -> List[Dict[str, Any]]:
        """
        Analyze content density of each page
        
        Args:
            content: Full text content
            page_matches: List of page match objects
            
        Returns:
            List of dicts with page info: {page_num, start_pos, end_pos, density, char_count}
        """
        page_list = list(page_matches)
        page_info = []
        
        for i, match in enumerate(page_list):
            page_num = int(match.group(1))
            start_pos = match.end()
            
            # Find end position (start of next page or end of content)
            if i < len(page_list) - 1:
                end_pos = page_list[i + 1].start()
            else:
                end_pos = len(content)
            
            page_content = content[start_pos:end_pos]
            
            # Calculate density: ratio of non-whitespace to total characters
            total_chars = len(page_content)
            non_whitespace = len(page_content.strip())
            density = non_whitespace / total_chars if total_chars > 0 else 0
            
            # Count actual text (ignore very short lines like just headers)
            lines = [l.strip() for l in page_content.split('\n') if l.strip()]
            avg_line_length = sum(len(l) for l in lines) / len(lines) if lines else 0
            
            page_info.append({
                'page_num': page_num,
                'start_pos': match.start(),
                'end_pos': end_pos,
                'content_length': non_whitespace,
                'density': density,
                'line_count': len(lines),
                'avg_line_length': avg_line_length,
                'is_light': non_whitespace < 500  # Light pages: < 500 chars of actual content
            })
        
        return page_info
    
    def _split_by_page_ranges(self, content: str, page_matches) -> List[str]:
        """
        Split content by page markers and group into ranges based on content density
        Heavy content pages get smaller groups, light pages are combined or skipped
        
        Args:
            content: Full text content with "--- Page X ---" markers
            page_matches: Iterator of page marker matches
            
        Returns:
            List of page range chunks, optimized for content density
        """
        page_info = self._analyze_page_density(content, page_matches)
        
        if not page_info:
            return []
        
        chapters = []
        current_group = []
        current_density_sum = 0
        target_density = 2000  # Aim for ~2000 chars of content per chapter
        
        for page in page_info:
            current_group.append(page)
            current_density_sum += page['content_length']
            
            # Decide if we should finalize this group
            should_finalize = False
            
            # Heavy content page: finalize sooner to give it more attention
            if page['content_length'] > 1500:
                should_finalize = len(current_group) >= 2
            # Normal content: follow target density
            elif current_density_sum >= target_density:
                should_finalize = True
            # Light page: combine with next unless it's the last page
            elif page['is_light'] and page != page_info[-1]:
                continue  # Don't finalize, keep combining
            # Last page: always finalize
            elif page == page_info[-1]:
                should_finalize = True
            
            if should_finalize and current_group:
                # Create chapter from grouped pages
                start_page_num = current_group[0]['page_num']
                end_page_num = current_group[-1]['page_num']
                
                start_pos = current_group[0]['start_pos']
                end_pos = current_group[-1]['end_pos']
                
                chapter_content = content[start_pos:end_pos].strip()
                
                if len(chapter_content) > 100:
                    chapters.append(chapter_content)
                
                current_group = []
                current_density_sum = 0
        
        # Handle any remaining pages
        if current_group:
            start_page_num = current_group[0]['page_num']
            end_page_num = current_group[-1]['page_num']
            
            start_pos = current_group[0]['start_pos']
            end_pos = current_group[-1]['end_pos']
            
            chapter_content = content[start_pos:end_pos].strip()
            if len(chapter_content) > 100:
                chapters.append(chapter_content)
        
        total_pages = len(page_info)
        heavy_pages = sum(1 for p in page_info if p['content_length'] > 1500)
        light_pages = sum(1 for p in page_info if p['is_light'])
        
        print(f"[CHUNKING] Detected {total_pages} pages ({heavy_pages} heavy, {light_pages} light)")
        print(f"[CHUNKING] Created {len(chapters)} content-aware chapters")
        
        return chapters
    
    def _group_by_semantic_similarity(self, paragraphs: List[str]) -> List[str]:
        """
        Group paragraphs into semantic chunks based on content length and breaks
        Distributes chunks more evenly across the entire content
        
        Args:
            paragraphs: List of paragraph strings
            
        Returns:
            List of grouped content chunks
        """
        chapters = []
        current_chunk = ""
        target_length = 600  # Reduced from 800 to create more chapters covering more content
        
        for para in paragraphs:
            if len(current_chunk) + len(para) < target_length:
                current_chunk += " " + para if current_chunk else para
            else:
                if current_chunk:
                    chapters.append(current_chunk)
                current_chunk = para
        
        if current_chunk:
            chapters.append(current_chunk)
        
        result = [ch for ch in chapters if len(ch) > 200]
        # Return more chapters to cover the entire content
        return result[:25]
    
    def _split_by_content_length(self, content: str, target_chunks: int = 15) -> List[str]:
        """
        Split content into approximately equal-sized chunks
        Increased target chunks to ensure coverage of entire file
        
        Args:
            content: Full text content
            target_chunks: Target number of chunks (increased to 15 for better coverage)
            
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
        
        return chapters[:20]
    
    def _extract_page_range(self, content: str) -> str:
        """
        Extract page range information from content
        Looks for "--- Page X ---" markers
        
        Args:
            content: Chapter content that may contain page markers
            
        Returns:
            Page range string like "Page 3-8" or single page "Page 5"
        """
        page_pattern = r'--- Page (\d+) ---'
        matches = re.findall(page_pattern, content)
        
        if not matches:
            return ""
        
        pages = sorted([int(p) for p in matches])
        if not pages:
            return ""
        
        start_page = pages[0]
        end_page = pages[-1]
        
        if start_page == end_page:
            return f"Page {start_page}"
        else:
            return f"Page {start_page}-{end_page}"
    
    def _calculate_content_density(self, content: str) -> float:
        """
        Calculate content density of a chapter
        Returns ratio of non-whitespace to total characters
        """
        total_chars = len(content)
        non_whitespace = len(content.strip())
        return non_whitespace / total_chars if total_chars > 0 else 0
    
    def _process_chapter_smart(
        self, 
        chapter_content: str, 
        chapter_num: int,
        target_questions: int = 4,
        solo_distribution: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Process a single chapter and generate configurable number of questions
        Adjusts question count based on content density
        
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
            # Extract page range information
            page_range = self._extract_page_range(chapter_content)
            
            # Calculate content density and adjust questions accordingly
            content_length = len(chapter_content.strip())
            density = self._calculate_content_density(chapter_content)
            
            # Scale target_questions based on content density
            # Light content (density < 0.4): reduce questions by 50%
            # Normal content (0.4-0.6): keep as is
            # Heavy content (> 0.6): increase questions by 25%
            if density < 0.4:
                adjusted_target = max(1, round(target_questions * 0.5))
            elif density > 0.6:
                adjusted_target = round(target_questions * 1.25)
            else:
                adjusted_target = target_questions
            
            # Extract chapter title (first non-empty, non-marker line)
            lines = chapter_content.split('\n')
            title = ""
            for line in lines:
                line = line.strip()
                # Skip page markers and empty lines
                if line and not line.startswith('---'):
                    title = line
                    break
            
            if not title:
                title = f"Chapter {chapter_num}"
            
            # Limit title length to 60 characters (leave room for page range)
            if len(title) > 60:
                # Find first sentence boundary
                sentences = title.split('. ')
                title = sentences[0]
                if len(title) > 60:
                    title = title[:57] + '...'
            
            # Add page range to title if available - this is CRITICAL for clarity
            if page_range:
                title = f"{page_range} - {title}"
            else:
                title = f"Chapter {chapter_num} - {title}"
            
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
                count = max(1, round(adjusted_target * solo_distribution.get(level, 0.25)))
                questions_per_level[level] = count
            
            # Generate content summary for higher-order questions (relational & extended_abstract)
            # This helps the AI understand broader themes and relationships
            content_summary = ""
            has_higher_order = questions_per_level.get('relational', 0) > 0 or questions_per_level.get('extended_abstract', 0) > 0
            if has_higher_order:
                content_summary = self._generate_content_summary(chapter_content, title)
            
            # Generate questions for each SOLO level
            for level in solo_levels:
                for _ in range(questions_per_level[level]):
                    question = self._generate_question(chapter_content, level, title, content_summary)
                    if question:
                        chapter_data['questions'].append({
                            'solo_level': level,
                            'question_data': question
                        })
            
            return chapter_data if chapter_data['questions'] else None
            
        except Exception as e:
            print(f"Error processing chapter {chapter_num}: {str(e)}")
            return None
    
    def _generate_question(self, content: str, level: str, context: str, content_summary: str = "") -> Dict[str, Any]:
        """
        Generate a single question at specified SOLO level
        
        Args:
            content: Chapter content
            level: SOLO taxonomy level
            context: Chapter context/title
            content_summary: Summary of the content for higher-order questions
            
        Returns:
            Dictionary with question data, or None if API unavailable
        """
        try:
            # Check if API is already exhausted - don't waste calls
            if self.api_exhausted:
                return None
            
            if self.api_keys[0] == 'mock':
                print(f"Using mock questions (no API keys configured)")
                return None
            
            # Call API to generate question
            prompt = self._build_prompt(content, level, context, content_summary)
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
    
    def _build_prompt(self, content: str, level: str, context: str, content_summary: str = "") -> str:
        """Build optimized prompt with detailed SOLO Taxonomy definitions
        
        Args:
            content: Chapter content
            level: SOLO taxonomy level
            context: Chapter context/title  
            content_summary: Summary of content for higher-order questions (relational, extended_abstract)
        """
        
        # Keep content preview SHORT (600 chars)
        content_preview = content[:600]
        
        # Build summary section for higher-order questions
        summary_section = ""
        if content_summary and level in ['relational', 'extended_abstract']:
            summary_section = f"\n\nCONTENT SUMMARY (key themes and relationships):\n{content_summary}\n"
        
        prompts = {
            'unistructural': f"""Create a UNISTRUCTURAL level question about '{context}'.

Content: {content_preview}

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
- Question < 250 chars
- 4 MC options (A-D), one correct
- 3 distractors must be PLAUSIBLE and require reading comprehension to eliminate
- Explanation < 250 chars

Return ONLY JSON: {{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ...", "explanation": "..."}}""",

            'multistructural': f"""Create a MULTISTRUCTURAL level question about '{context}'.

Content: {content_preview}

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
- Question < 250 chars
- 4 MC options (A-D), one correct
- 3 distractors must combine PLAUSIBLE elements that seem correct at first glance
- Explanation < 250 chars

Return ONLY JSON: {{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ...", "explanation": "..."}}""",

            'relational': f"""Create a RELATIONAL level question about '{context}'.

Content: {content_preview}{summary_section}

RELATIONAL LEVEL DEFINITION:
This stage relates to aspects of knowledge combining to form a structure. By this stage, the student is able to understand the importance of different parts in relation to the whole. They are able to connect concepts and ideas, so it provides a coherent knowledge of the whole thing. Moreover, the students' response indicates an understanding of the task by combining all the parts, and they can demonstrate how each part contributes to the whole.

TASK: Create a question that tests understanding of HOW parts CONNECT and work TOGETHER. Use both the detailed content AND the summary to identify key relationships. Student should explain relationships, patterns, or cause-effect between elements. Shows deep integrated understanding.

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
- Question < 250 chars
- 4 MC options (A-D), one correct
- 3 distractors must be CHALLENGING and reflect real misconceptions
- Explanation < 250 chars

Return ONLY JSON: {{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ...", "explanation": "..."}}""",

            'extended_abstract': f"""Create an EXTENDED ABSTRACT level question about '{context}'.

Content: {content_preview}{summary_section}

EXTENDED ABSTRACT LEVEL DEFINITION:
By this level, students are able to make connections within the provided task, and they also create connections beyond that. They develop the ability to transfer and generalise the concepts and principles from one subject area into a particular domain. Therefore, the students' response indicates that they can conceptualise beyond the level of what has been taught. They are able to propose new concepts and ideas depending on their understanding of the task or subject taught.

TASK: Create a question that tests ability to APPLY knowledge to NEW contexts NOT in the content. Use the summary to understand the core principles, then create a scenario that requires applying those principles to a completely NEW situation. Student should predict, generalize, or solve scenarios beyond what was directly taught.

CRITICAL INSTRUCTIONS FOR DISTRACTORS:
- **DO NOT** create obviously wrong options
- **DO** create TRICKY distractors that:
  * Look correct if you misunderstand which principle applies
  * Correctly apply a DIFFERENT but related principle
  * Follow logically from the content but reach wrong conclusion
  * Represent COMMON OVERGENERALIZATIONS of the principles
  * Seem reasonable on surface but violate subtle constraints
  * Apply the principle to SIMILAR but wrong context
- Example BAD distractor: "Blue elephants" (nonsense)
- Example GOOD distractor: "You should increase speed" (correct for acceleration problem, wrong for this momentum problem - different principle)
- Distractors should be SOPHISTICATED errors that good test-takers might make

Requirements:
- Use the summary to identify transferable concepts and principles
- Ask about applying/generalizing these concepts to a NEW different situation
- Scenario should NOT be directly mentioned in the content
- Requires student to conceptualize beyond what was taught
- Student must demonstrate ability to transfer knowledge to new contexts
- Question < 250 chars
- 4 MC options (A-D), one correct
- 3 distractors must be CHALLENGING: plausible applications of WRONG principles or MISAPPLICATIONS
- Explanation < 250 chars

Return ONLY JSON: {{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ...", "explanation": "..."}}"""
        }
        
        return prompts.get(level, prompts['unistructural'])
    
    def _call_api(self, prompt: str, retry_count: int = 0) -> str:
        """
        Call API for question generation
        Primary: Gemini API
        Fallback: OpenRouter API with key rotation (9 keys)
        Final Fallback: GitHub Models API
        
        Key rotation logic:
        - 429 (rate limit): rotate to next key
        - Connection error: retry same key up to 2 times, then try GitHub
        - Other errors: try next key
        """
        import time
        
        # Check if already exhausted - don't waste calls
        if self.api_exhausted:
            return None
        
        # Try Gemini API first (Primary)
        try:
            if self.gemini_model:
                print("[Gemini] Calling Gemini API (primary)...")
                response = self.gemini_model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=800,
                        temperature=0.7
                    )
                )
                if response and response.text:
                    print("[OK] Gemini API succeeded")
                    return response.text
        except Exception as e:
            print(f"[Gemini Error] {str(e)[:100]}")
            print("[FALLBACK] Gemini quota exhausted. Switching to OpenRouter...")
        
        # Fallback to OpenRouter API with key rotation
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
                timeout=1
            )
            
            if response.status_code == 200:
                print(f"[OK] OpenRouter key {self.current_key_index + 1}/{len(self.api_keys)}")
                return response.json()["choices"][0]["message"]["content"]
            elif response.status_code == 429:
                # Rate limited - rotate to next key (this is the ONLY case to rotate)
                print(f"[429] Rate limited on key {self.current_key_index + 1}/{len(self.api_keys)}")
                if self.current_key_index < len(self.api_keys) - 1:
                    self.current_key_index += 1
                    return self._call_api(prompt, 0)  # Reset retry count for new key
                else:
                    # All OpenRouter keys exhausted - try Groq
                    print("[FALLBACK] All OpenRouter keys rate-limited. Switching to Groq API...")
                    self.current_key_index = 0  # Reset for next batch of calls
                    groq_result = self._call_groq_api(prompt)
                    if groq_result:
                        return groq_result
                    else:
                        # Then try GitHub
                        github_result = self._call_github_api(prompt)
                        if github_result:
                            return github_result
                        else:
                            print("[CRITICAL] All API providers are exhausted!")
                            self.api_exhausted = True
                            return None
            else:
                # Other HTTP error - log and try GitHub directly (don't burn through keys)
                print(f"[{response.status_code}] OpenRouter error: {response.text[:100]}")
                return self._call_github_api(prompt)
            
        except requests.Timeout:
            # Timeout - retry same key once, then try GitHub
            print(f"[TIMEOUT] Request timeout on key {self.current_key_index + 1}")
            if retry_count < 1:
                time.sleep(1)  # Wait 1 second before retry
                return self._call_api(prompt, retry_count + 1)
            else:
                print("[FALLBACK] Timeout persists. Trying Groq API...")
                return self._call_groq_api(prompt)
        except requests.ConnectionError as e:
            # Connection error (DNS, network) - DON'T burn through keys!
            # This is a network issue, not an API issue
            print(f"[NETWORK] Connection error: {str(e)[:80]}")
            if retry_count < 2:
                print(f"[RETRY] Waiting 1 second before retry {retry_count + 1}/2...")
                time.sleep(1)  # Wait before retry
                return self._call_api(prompt, retry_count + 1)
            else:
                print("[NETWORK] Network appears down. Trying Groq as last resort...")
                return self._call_groq_api(prompt)
        except Exception as e:
            print(f"[ERROR] API call error: {type(e).__name__}: {str(e)}")
            # For unknown errors, try Groq first
            return self._call_groq_api(prompt)
    
    def _call_groq_api(self, prompt: str) -> str:
        """Call Groq API (mixtral-8x7b-32768) as fallback"""
        try:
            if not self.groq_api_key:
                print("[ERROR] Groq API key not configured - cannot use fallback")
                return None
            
            print("[Groq API] Calling Mixtral 8x7b model...")
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "mixtral-8x7b-32768",
                "messages": [
                    {"role": "system", "content": "You are a helpful educational assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 800
            }
            
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=1
            )
            
            if response.status_code == 200:
                print("[SUCCESS] Groq API working (Mixtral 8x7b)")
                return response.json()["choices"][0]["message"]["content"]
            elif response.status_code == 429:
                print("[RATE_LIMIT] Groq API rate-limited")
                return None
            else:
                print(f"[Groq API Error] Status {response.status_code}: {response.text[:300]}")
                return None
                
        except requests.Timeout:
            print("[Groq API] Request timeout")
            return None
        except requests.ConnectionError as e:
            print(f"[Groq API] Connection error: {str(e)[:80]}")
            return None
        except Exception as e:
            print(f"[Groq API Exception] {type(e).__name__}: {str(e)}")
            return None
    
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
                timeout=1
            )
            
            if response.status_code == 200:
                print("[SUCCESS] GitHub Models API working (gpt-4o)")
                return response.json()["choices"][0]["message"]["content"]
            elif response.status_code == 429:
                print("[RATE_LIMIT] GitHub Models also rate-limited (quota exhausted)")
                self.api_exhausted = True  # True exhaustion - all APIs rate limited
                return None
            else:
                print(f"[GitHub API Error] Status {response.status_code}: {response.text[:300]}")
                # Don't set exhausted - could be temporary server error
                return None
                
        except requests.Timeout:
            print("[GitHub API] Request timeout (30s)")
            # Don't set exhausted - network issue, not API issue
            return None
        except requests.ConnectionError as e:
            print(f"[GitHub API] Connection error (network issue): {str(e)[:80]}")
            # Don't set exhausted - this is a network problem, not API exhaustion
            return None
        except Exception as e:
            print(f"[GitHub API Exception] {type(e).__name__}: {str(e)}")
            # Don't set exhausted for unknown errors
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
    
    def _remove_page_references(self, text: str) -> str:
        """
        Remove page number references from questions and explanations
        Handles both English and Serbian patterns
        
        Examples:
        - "According to page 79, why doesn't..." → "Why doesn't..."
        - "na strani 86" → removed
        - "Page 5 states that" → "States that"
        - "prema algoritmu ... na strani 86" → "prema algoritmu ..."
        """
        if not text:
            return text
        
        # English patterns
        text = re.sub(r'According to [Pp]age\s+\d+[,:]?\s*', '', text)
        text = re.sub(r'[Pp]age\s+\d+\s+(?:states?|says?|defines?|explains?|shows?)\s+that\s+', '', text)
        text = re.sub(r'\s*\([Pp]age\s+\d+\)\s*', ' ', text)
        text = re.sub(r'\s*on\s+[Pp]age\s+\d+', '', text)
        
        # Serbian patterns
        text = re.sub(r'\s*na\s+strani\s+\d+', '', text)
        text = re.sub(r'\s*na\s+stranici\s+\d+', '', text)
        text = re.sub(r'Šta\s+se\s+[^?]*?\s+prema\s+[^?]*?\s+na\s+strani\s+\d+\?', 
                     lambda m: 'Šta se ' + m.group(0)[len('Šta se '):].split(' prema ')[0] + '?', text)
        text = re.sub(r'prema\s+[^,]*\s+na\s+strani\s+\d+', '', text)
        
        # Clean up extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _validate_and_clean_question(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean question data to enforce reasonable lengths"""
        try:
            MAX_QUESTION_LEN = 200
            MAX_ANSWER_LEN = 150
            MAX_EXPLANATION_LEN = 300
            
            # Clean question - REMOVE PAGE REFERENCES FIRST
            if 'question' in question_data:
                q = question_data['question']
                # Remove page references
                q = self._remove_page_references(q)
                # Then handle length
                if len(q) > MAX_QUESTION_LEN:
                    sentences = q.split('?')
                    q = sentences[0] + '?' if sentences else q[:MAX_QUESTION_LEN]
                question_data['question'] = q
            
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
            
            # Clean explanation - REMOVE PAGE REFERENCES FIRST
            if 'explanation' in question_data:
                exp = question_data['explanation']
                # Remove page references
                exp = self._remove_page_references(exp)
                # Then handle length
                if len(exp) > MAX_EXPLANATION_LEN:
                    sentences = exp.split('. ')
                    cleaned_exp = sentences[0]
                    if len(cleaned_exp) > MAX_EXPLANATION_LEN:
                        cleaned_exp = cleaned_exp[:MAX_EXPLANATION_LEN-3] + '...'
                    exp = cleaned_exp
                question_data['explanation'] = exp
            
            return question_data
        except Exception as e:
            print(f"Error validating question: {str(e)}")
            return question_data

    # ==================== NEW SOLO-BASED GENERATION ====================
    
    def generate_solo_questions(
        self,
        lessons_data: List[Dict[str, Any]],
        solo_levels: List[str],
        questions_per_level: int = 3,
        section_ids: List[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate questions based on SOLO taxonomy levels from parsed lessons.
        
        SOLO Level Requirements:
        - unistructural: From LEARNING OBJECTS (single discrete knowledge unit)
        - multistructural: From SECTIONS (multiple related facts within a section)
        - relational: From SECTIONS + LEARNING OBJECTS (analyze relationships)
        - extended_abstract: Requires 2 LESSONS to combine knowledge
        
        Args:
            lessons_data: List of lesson dicts with sections and learning objects
            solo_levels: List of SOLO levels to generate questions for
            questions_per_level: Number of questions per SOLO level
            section_ids: Optional list of specific section IDs to use
            
        Returns:
            List of question dicts ready for database storage
        """
        print(f"\n[SOLO GENERATOR] Starting question generation")
        print(f"[SOLO GENERATOR] Lessons: {len(lessons_data)}, Levels: {solo_levels}")
        
        generated_questions = []
        
        # Prepare content from lessons
        primary_lesson = lessons_data[0] if lessons_data else None
        secondary_lesson = lessons_data[1] if len(lessons_data) > 1 else None
        
        if not primary_lesson:
            raise ValueError("At least one lesson is required")
        
        # Build content context for each level
        for level in solo_levels:
            print(f"\n[SOLO] Generating {questions_per_level} {level} questions...")
            
            if level == 'extended_abstract' and not secondary_lesson:
                print(f"[SOLO] Skipping extended_abstract - requires 2 lessons")
                continue
            
            for i in range(questions_per_level):
                try:
                    if level == 'extended_abstract':
                        # Combine knowledge from two lessons
                        question = self._generate_extended_abstract_question(
                            primary_lesson, secondary_lesson
                        )
                    elif level == 'unistructural':
                        # From learning objects only
                        question = self._generate_unistructural_question(
                            primary_lesson, section_ids
                        )
                    elif level == 'multistructural':
                        # From sections
                        question = self._generate_multistructural_question(
                            primary_lesson, section_ids
                        )
                    elif level == 'relational':
                        # From sections AND learning objects
                        question = self._generate_relational_question(
                            primary_lesson, section_ids
                        )
                    else:
                        question = None
                    
                    if question:
                        question['solo_level'] = level
                        generated_questions.append(question)
                        print(f"[SOLO] Generated {level} question {i+1}/{questions_per_level}")
                    
                except Exception as e:
                    print(f"[SOLO] Error generating {level} question: {e}")
                    if self.api_exhausted:
                        print("[SOLO] API exhausted, stopping generation")
                        break
            
            if self.api_exhausted:
                break
        
        print(f"\n[SOLO GENERATOR] Total questions generated: {len(generated_questions)}")
        return generated_questions
    
    def _generate_unistructural_question(
        self,
        lesson: Dict[str, Any],
        section_ids: List[int] = None
    ) -> Dict[str, Any]:
        """Generate UNISTRUCTURAL question from LEARNING OBJECTS"""
        
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
                    'content': lo.get('content', ''),
                    'type': lo.get('object_type', 'concept'),
                    'keywords': lo.get('keywords', [])
                })
        
        if not learning_objects:
            # Fallback to raw content
            return self._generate_fallback_question(lesson, 'unistructural')
        
        # Pick a random learning object for variety
        import random
        lo = random.choice(learning_objects)
        
        prompt = f"""Generate a UNISTRUCTURAL level multiple choice question in ENGLISH ONLY.

LESSON: {lesson_title}

LEARNING OBJECT:
Title: {lo['title']}
Type: {lo['type']}
Content: {lo['content']}
Keywords: {', '.join(lo.get('keywords', []))}

UNISTRUCTURAL LEVEL DEFINITION (SOLO Taxonomy):
At this level, students can identify, name, and recall ONE piece of information. They focus on a SINGLE relevant aspect. The response shows understanding of ONE element without seeing connections to others.

TASK: Create a question that tests recall of ONE specific fact, term, definition, or concept from this learning object.

Requirements:
- **ALL TEXT MUST BE IN ENGLISH** - no Serbian, no other languages
- Question must focus on a SINGLE piece of information
- Tests basic recall/recognition/identification
- Has ONE clear correct answer directly from the content
- Question < 200 characters
- 4 options (A-D), one correct, others plausible but wrong
- Explanation < 200 chars, state the fact being tested

Return ONLY valid JSON:
{{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ...", "explanation": "..."}}"""

        response = self._call_api(prompt)
        if not response:
            return None
        
        question_data = self._parse_question_response(response)
        if question_data:
            question_data = self._validate_and_clean_question(question_data)
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
        section_ids: List[int] = None
    ) -> Dict[str, Any]:
        """Generate MULTISTRUCTURAL question from SECTIONS"""
        
        lesson_title = lesson.get('title', 'Lesson')
        sections = lesson.get('sections', [])
        
        if section_ids:
            sections = [s for s in sections if s.get('id') in section_ids]
        
        if not sections:
            return self._generate_fallback_question(lesson, 'multistructural')
        
        # Pick a section
        import random
        section = random.choice(sections)
        
        # Get section content and its learning objects
        section_title = section.get('title', '')
        section_content = section.get('content', '')[:2500]
        
        los_text = ""
        for lo in section.get('learning_objects', [])[:5]:
            los_text += f"\n- {lo.get('title', '')}: {lo.get('content', '')[:200]}"
        
        prompt = f"""Generate a MULTISTRUCTURAL level multiple choice question in ENGLISH ONLY.

LESSON: {lesson_title}

SECTION: {section_title}
Content: {section_content}

Key concepts in this section:{los_text}

MULTISTRUCTURAL LEVEL DEFINITION (SOLO Taxonomy):
At this level, students can describe, list, enumerate, and combine MULTIPLE pieces of information. They understand SEVERAL independent aspects but don't yet see how they connect. The response involves quantitative increase in knowledge.

TASK: Create a question that requires knowledge of MULTIPLE facts, steps, or elements from this section.

Requirements:
- **ALL TEXT MUST BE IN ENGLISH** - no Serbian, no other languages
- Question must involve MULTIPLE pieces of information (not just one fact)
- Tests ability to list, describe, enumerate, or sequence
- May ask "which of the following are..." or "what are the steps..."
- Question < 250 characters
- 4 options (A-D), one correct
- Explanation < 200 chars, reference the multiple elements

Return ONLY valid JSON:
{{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ...", "explanation": "..."}}"""

        response = self._call_api(prompt)
        if not response:
            return None
        
        question_data = self._parse_question_response(response)
        if question_data:
            question_data = self._validate_and_clean_question(question_data)
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
        section_ids: List[int] = None
    ) -> Dict[str, Any]:
        """Generate RELATIONAL question from SECTIONS + LEARNING OBJECTS"""
        
        lesson_title = lesson.get('title', 'Lesson')
        sections = lesson.get('sections', [])
        
        if section_ids:
            sections = [s for s in sections if s.get('id') in section_ids]
        
        if not sections:
            return self._generate_fallback_question(lesson, 'relational')
        
        # Build comprehensive content from sections and their learning objects
        content_parts = []
        all_los = []
        
        for section in sections[:3]:
            section_title = section.get('title', '')
            content_parts.append(f"### {section_title}")
            
            for lo in section.get('learning_objects', []):
                all_los.append({
                    'title': lo.get('title', ''),
                    'content': lo.get('content', ''),
                    'type': lo.get('object_type', ''),
                    'section': section_title
                })
                content_parts.append(f"- {lo.get('title', '')}: {lo.get('content', '')[:250]}")
        
        combined_content = "\n".join(content_parts)[:3000]
        
        prompt = f"""Generate a RELATIONAL level multiple choice question in ENGLISH ONLY.

LESSON: {lesson_title}

CONTENT (Sections with Learning Objects):
{combined_content}

RELATIONAL LEVEL DEFINITION (SOLO Taxonomy):
At this level, students can compare, contrast, explain causes, analyze, relate, and apply. They see how parts fit together into a COHERENT WHOLE. They understand relationships between concepts and can explain WHY something happens.

TASK: Create a question that requires ANALYZING RELATIONSHIPS between concepts, explaining cause-effect, or comparing/contrasting ideas.

Requirements:
- **ALL TEXT MUST BE IN ENGLISH** - no Serbian, no other languages
- Question must require understanding how concepts RELATE to each other
- Tests analysis, comparison, cause-effect reasoning, or application
- May ask "why does X lead to Y" or "how does X relate to Y" or "compare X and Y"
- Should NOT be answerable by memorizing isolated facts
- Question < 280 characters
- 4 options (A-D), one correct
- Explanation < 250 chars, explain the relationship

Return ONLY valid JSON:
{{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ...", "explanation": "..."}}"""

        response = self._call_api(prompt)
        if not response:
            return None
        
        question_data = self._parse_question_response(response)
        if question_data:
            question_data = self._validate_and_clean_question(question_data)
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
    
    def _generate_fallback_question(
        self,
        lesson: Dict[str, Any],
        solo_level: str
    ) -> Dict[str, Any]:
        """Fallback when no sections/LOs available - use raw content"""
        
        lesson_title = lesson.get('title', 'Lesson')
        content = lesson.get('raw_content', '')[:4000]
        
        prompt = self._build_solo_prompt(content, lesson_title, solo_level)
        
        response = self._call_api(prompt)
        if not response:
            return None
        
        question_data = self._parse_question_response(response)
        if question_data:
            question_data = self._validate_and_clean_question(question_data)
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
                'bloom_level': self._solo_to_bloom(solo_level)
            }
        return None
    
    def _generate_extended_abstract_question(
        self,
        lesson1: Dict[str, Any],
        lesson2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate an extended abstract question combining two lessons"""
        
        # Build combined content from both lessons
        title1 = lesson1.get('title', 'Lesson 1')
        title2 = lesson2.get('title', 'Lesson 2')
        
        # Get summaries or key content from each lesson
        content1 = self._extract_key_concepts(lesson1)
        content2 = self._extract_key_concepts(lesson2)
        
        prompt = f"""Create an EXTENDED ABSTRACT level question that COMBINES knowledge from TWO different topics in ENGLISH ONLY.

TOPIC 1: {title1}
Key concepts:
{content1}

TOPIC 2: {title2}
Key concepts:
{content2}

EXTENDED ABSTRACT LEVEL DEFINITION:
Students must make connections BETWEEN different topics and apply combined knowledge to NEW situations not directly covered in either topic. They must demonstrate ability to transfer, generalize, and synthesize concepts across subject areas.

TASK: Create a question that requires:
1. Understanding concepts from BOTH topics
2. Recognizing relationships BETWEEN the two topics  
3. Applying combined knowledge to a NEW scenario
4. Demonstrating higher-order thinking that goes beyond either topic alone

Requirements:
- **ALL TEXT MUST BE IN ENGLISH** - no Serbian, no other languages
- Question must require knowledge from BOTH topics to answer correctly
- Scenario should involve applying combined principles to a new context
- Question < 300 chars
- 4 MC options (A-D), one correct
- Explanation should reference how both topics connect

Return ONLY JSON: {{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ...", "explanation": "..."}}"""

        response = self._call_api(prompt)
        if not response:
            return None
        
        question_data = self._parse_question_response(response)
        if question_data:
            question_data = self._validate_and_clean_question(question_data)
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
                'bloom_level': 'synthesis',
                'tags': [title1, title2, 'cross-topic'],
                'primary_lesson_id': lesson1.get('id'),
                'secondary_lesson_id': lesson2.get('id')
            }
        return None
    
    def _extract_key_concepts(self, lesson: Dict[str, Any]) -> str:
        """Extract key concepts from a lesson for extended abstract questions"""
        concepts = []
        
        # Use summary if available
        if lesson.get('summary'):
            concepts.append(lesson['summary'])
        
        # Add learning objects titles and types
        for section in lesson.get('sections', [])[:3]:
            for lo in section.get('learning_objects', [])[:4]:
                lo_type = lo.get('object_type', 'concept')
                concepts.append(f"- {lo.get('title', '')} ({lo_type})")
        
        # If no structured content, use raw content summary
        if not concepts and lesson.get('raw_content'):
            concepts.append(self._generate_content_summary(lesson['raw_content'][:3000]))
        
        return "\n".join(concepts)[:1500]
    
    def _build_solo_prompt(self, content: str, context: str, level: str) -> str:
        """Build a prompt for generating questions at a specific SOLO level"""
        
        level_definitions = {
            'unistructural': """UNISTRUCTURAL LEVEL:
Students identify, do simple procedures, and deal with terminology. They focus on ONE relevant aspect.
Create a question that tests recall of a SINGLE fact, term, or simple procedure from the content.
- Should have ONE clear correct answer based on direct content
- Tests basic recall/recognition
- Simple and straightforward""",
            
            'multistructural': """MULTISTRUCTURAL LEVEL:
Students describe, enumerate, combine, and do algorithms. They focus on SEVERAL independent aspects.
Create a question that tests understanding of MULTIPLE related facts or steps from the content.
- Should require knowledge of several related pieces of information
- Tests ability to list, describe, or sequence multiple elements
- More comprehensive than single-fact recall""",
            
            'relational': """RELATIONAL LEVEL:
Students compare, contrast, explain causes, analyze, relate, and apply. They integrate aspects into a structure.
Create a question that tests ability to RELATE concepts, explain cause-effect, or analyze relationships.
- Should require understanding how concepts connect
- Tests analysis, comparison, or explanation of relationships
- Requires integrating multiple concepts into coherent understanding"""
        }
        
        level_def = level_definitions.get(level, level_definitions['unistructural'])
        
        return f"""Generate a {level.upper()} level multiple choice question in ENGLISH ONLY based on this educational content.

CONTEXT: {context}

CONTENT:
{content}

{level_def}

Requirements:
- **ALL TEXT MUST BE IN ENGLISH** - no Serbian, no other languages
- Question should be clear and unambiguous
- Question length < 250 characters
- Provide exactly 4 options (A, B, C, D)
- One option must be clearly correct
- Explanation should justify the correct answer (< 250 chars)

Return ONLY valid JSON:
{{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ...", "explanation": "..."}}"""
    
    def _find_correct_index(self, options: List[str], correct_answer: str) -> int:
        """Find the index of the correct answer in options list"""
        if not options or not correct_answer:
            return 0
        
        # Try exact match first
        for i, opt in enumerate(options):
            if opt == correct_answer:
                return i
        
        # Try matching by letter prefix
        correct_letter = correct_answer[0].upper() if correct_answer else 'A'
        for i, opt in enumerate(options):
            if opt.startswith(correct_letter):
                return i
        
        return 0
    
    def _solo_to_bloom(self, solo_level: str) -> str:
        """Map SOLO level to approximate Bloom's taxonomy level"""
        mapping = {
            'unistructural': 'remember',
            'multistructural': 'understand',
            'relational': 'analyze',
            'extended_abstract': 'create'
        }
        return mapping.get(solo_level, 'understand')
