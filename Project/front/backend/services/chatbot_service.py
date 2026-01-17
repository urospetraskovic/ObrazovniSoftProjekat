"""
Chatbot Service for Learning Assistant
Uses Ollama for local processing, Gemini as fallback, with offline mode and database queries
"""

import os
import requests
import json
from typing import Optional, List, Dict
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

class ChatbotService:
    """Learning Assistant Chatbot Service"""

    def __init__(self, db_session=None):
        """Initialize chatbot with Ollama and Gemini support"""
        self.ollama_url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:14b-instruct-q4_K_M")
        self.gemini_model = genai.GenerativeModel("gemini-2.0-flash")
        self.max_context_length = 2000
        self.db_session = db_session
        
        # Simple offline knowledge base
        self.offline_responses = {
            "hello": "Hello! I'm your Learning Assistant. How can I help you today?",
            "hi": "Hi there! What would you like to learn about?",
            "help": "I can help you with:\n- Questions about course content\n- Explanations of concepts\n- Quiz answer discussions\n- Study tips\n- Course and lesson information\n\nJust ask me anything!",
            "what can you do": "I'm here to help you learn! I can answer questions about:\n- Your course materials\n- Difficult concepts\n- Quiz questions and answers\n- Study strategies\n- Your courses and lessons",
            "thanks": "You're welcome! Feel free to ask more questions!",
            "thank you": "Happy to help! Let me know if you need anything else.",
        }
        
        print(f"[ChatbotService] Initialized with Ollama: {self.ollama_url}/{self.ollama_model}")
        print("[ChatbotService] Offline mode available as fallback")

    def set_db_session(self, db_session):
        """Set database session for database queries"""
        self.db_session = db_session

    def _test_ollama_connection(self) -> bool:
        """Test if Ollama is running"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False

    def _search_learning_content(self, query: str, course_id: Optional[int] = None) -> Optional[str]:
        """
        Search through lessons, sections, learning objects, and ontology 
        to find relevant content for the user's question
        """
        if not self.db_session:
            return None
        
        query_lower = query.lower().strip()
        # Extract key terms (remove common question words)
        stop_words = ["what", "is", "a", "an", "the", "whats", "what's", "how", "why", "does", "do", "can", "you", "tell", "me", "about", "explain"]
        query_terms = [w for w in query_lower.split() if w not in stop_words and len(w) > 2]
        
        if not query_terms:
            return None
        
        try:
            from models import Course, Lesson, Section, LearningObject, ConceptRelationship
            
            results = []
            
            # Search in Learning Objects (most specific content)
            learning_objects = self.db_session.query(LearningObject).all()
            for lo in learning_objects:
                lo_text = f"{lo.title or ''} {lo.description or ''} {lo.content or ''}".lower()
                match_score = sum(1 for term in query_terms if term in lo_text)
                # Boost score if the term appears in the title
                for term in query_terms:
                    if term in (lo.title or '').lower():
                        match_score += 2
                if match_score > 0:
                    results.append({
                        'type': 'learning_object',
                        'title': lo.title,
                        'content': lo.description or lo.content,  # Prefer description, it has the actual content
                        'score': match_score
                    })
            
            # Search in Sections
            sections = self.db_session.query(Section).all()
            for section in sections:
                section_text = f"{section.title or ''} {section.content or ''}".lower()
                match_score = sum(1 for term in query_terms if term in section_text)
                if match_score > 0:
                    results.append({
                        'type': 'section',
                        'title': section.title,
                        'content': section.content,
                        'score': match_score
                    })
            
            # Search in Lessons
            lessons = self.db_session.query(Lesson).all()
            for lesson in lessons:
                lesson_text = f"{lesson.title or ''} {lesson.summary or ''}".lower()
                match_score = sum(1 for term in query_terms if term in lesson_text)
                if match_score > 0:
                    results.append({
                        'type': 'lesson',
                        'title': lesson.title,
                        'content': lesson.summary,
                        'score': match_score
                    })
            
            # Search in Ontology/Concept Relationships
            try:
                concepts = self.db_session.query(ConceptRelationship).all()
                for concept in concepts:
                    concept_text = f"{concept.source_concept or ''} {concept.target_concept or ''} {concept.relationship_type or ''}".lower()
                    match_score = sum(1 for term in query_terms if term in concept_text)
                    if match_score > 0:
                        results.append({
                            'type': 'ontology',
                            'title': f"{concept.source_concept} → {concept.target_concept}",
                            'content': f"Relationship: {concept.relationship_type}",
                            'score': match_score
                        })
            except Exception as e:
                print(f"[ChatbotService] Ontology search error: {e}")
            
            # Sort by score and return the best match
            if results:
                results.sort(key=lambda x: x['score'], reverse=True)
                best = results[0]
                
                # Format response based on content type
                if best['type'] == 'learning_object':
                    response = f"📖 **{best['title']}** (Learning Object)\n\n{best['content'][:800] if best['content'] else 'No detailed content available.'}"
                elif best['type'] == 'section':
                    response = f"📚 **{best['title']}** (Section)\n\n{best['content'][:800] if best['content'] else 'No detailed content available.'}"
                elif best['type'] == 'lesson':
                    response = f"📘 Found in lesson **{best['title']}**\n\n{best['content'][:800] if best['content'] else 'Check this lesson for more details.'}"
                else:
                    response = f"🔗 **Ontology**: {best['title']}\n{best['content']}"
                
                # If there are more results, mention them
                if len(results) > 1:
                    other_titles = [r['title'] for r in results[1:4] if r['title'] != best['title']]
                    if other_titles:
                        response += f"\n\n💡 *Related content in: {', '.join(other_titles)}*"
                
                return response
            
            return None
            
        except Exception as e:
            print(f"[ChatbotService] Search error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _get_offline_response(self, user_message: str, course_id: Optional[int] = None) -> Optional[str]:
        """Generate response from simple offline knowledge base and database queries"""
        message_lower = user_message.lower().strip()
        
        # Check for exact matches first
        for key, response in self.offline_responses.items():
            if key in message_lower:
                return response
        
        # Search through learning content (lessons, sections, learning objects, ontology)
        content_result = self._search_learning_content(user_message, course_id)
        if content_result:
            return content_result
        
        # Database queries for course/lesson information
        if self.db_session:
            try:
                # Import models here to avoid circular imports
                from models import Course, Lesson, Question, Quiz
                
                # Flexible keyword matching (handles typos like "lessions")
                lesson_keywords = ["lesson", "lesion", "lession", "les"]
                course_keywords = ["course"]
                quiz_keywords = ["quiz", "quizzes"]
                question_keywords = ["question"]
                
                # Determine if user wants lessons or courses
                wants_lessons = any(kw in message_lower for kw in lesson_keywords)
                wants_courses = any(kw in message_lower for kw in course_keywords) and not wants_lessons
                wants_quizzes = any(kw in message_lower for kw in quiz_keywords)
                wants_questions = any(kw in message_lower for kw in question_keywords)
                wants_list = any(word in message_lower for word in ["list", "show", "what do i have", "tell me my", "give me", "them"])
                
                # If user asks for lessons, try to find them
                if wants_list and wants_lessons:
                    # First, check if course_id is provided
                    if course_id:
                        lessons = self.db_session.query(Lesson).filter_by(course_id=course_id).all()
                        if lessons:
                            lesson_list = "\n".join([f"- **{l.title}**" for l in lessons[:20]])
                            return f"📖 Lessons in this course:\n{lesson_list}" + (f"\n... and {len(lessons)-20} more" if len(lessons) > 20 else "")
                        else:
                            return "No lessons in this course yet."
                    
                    # If no course_id, get first course and list its lessons
                    courses = self.db_session.query(Course).all()
                    if courses:
                        first_course_id = courses[0].id
                        lessons = self.db_session.query(Lesson).filter_by(course_id=first_course_id).all()
                        if lessons:
                            lesson_list = "\n".join([f"- **{l.title}**" for l in lessons[:20]])
                            return f"📖 Lessons in '{courses[0].name}':\n{lesson_list}" + (f"\n... and {len(lessons)-20} more" if len(lessons) > 20 else "")
                        else:
                            return f"The course '{courses[0].name}' has no lessons yet."
                    else:
                        return "You don't have any courses yet. Create one to get started!"
                
                # Check for lesson/course count questions
                if any(word in message_lower for word in ["how many", "total", "count", "number of"]):
                    if wants_lessons:
                        if course_id:
                            lessons = self.db_session.query(Lesson).filter_by(course_id=course_id).all()
                            return f"📚 You have **{len(lessons)}** lesson(s) in this course."
                        else:
                            lessons = self.db_session.query(Lesson).all()
                            return f"📚 You have **{len(lessons)}** total lesson(s)."
                    
                    if wants_courses:
                        courses = self.db_session.query(Course).all()
                        return f"📚 You have **{len(courses)}** course(s)."
                    
                    if wants_quizzes:
                        if course_id:
                            quizzes = self.db_session.query(Quiz).filter_by(course_id=course_id).all()
                            return f"📋 You have **{len(quizzes)}** quiz(zes) in this course."
                        else:
                            quizzes = self.db_session.query(Quiz).all()
                            return f"📋 You have **{len(quizzes)}** total quiz(zes)."
                    
                    if wants_questions:
                        if course_id:
                            questions = self.db_session.query(Question).filter_by(course_id=course_id).all()
                            return f"❓ You have **{len(questions)}** question(s) in this course."
                        else:
                            questions = self.db_session.query(Question).all()
                            return f"❓ You have **{len(questions)}** total question(s)."
                
                # List courses
                if wants_list and (wants_courses or not wants_lessons):
                    courses = self.db_session.query(Course).all()
                    if courses:
                        course_list = "\n".join([f"- **{c.name}**: {c.description[:50]}..." if c.description else f"- **{c.name}**" for c in courses])
                        return f"📚 Your Courses:\n{course_list}"
                    
                    return "You don't have any courses yet. Create one to get started!"
                
            except Exception as e:
                print(f"[ChatbotService] Database error: {e}")
                import traceback
                traceback.print_exc()
        
        # Generic responses for various question types
        if any(word in message_lower for word in ["what", "how", "why", "explain", "tell"]):
            return f"That's a great question about '{user_message}'. To give you a better answer, I would need more context about your course material. Can you provide more details or let me know which lesson or topic this relates to?"
        
        if any(word in message_lower for word in ["quiz", "question", "answer", "test", "exam"]):
            return "I can help you understand quiz questions! Please provide the question and answer, and I'll explain the concept to you."
        
        if any(word in message_lower for word in ["study", "learn", "tip", "advice", "help"]):
            return "Great! Here are some study tips:\n1. Review concepts regularly\n2. Practice with examples\n3. Test yourself with quizzes\n4. Connect concepts to real-world scenarios\n5. Discuss with others\n\nWhat specific topic would you like help with?"
        
        # Default response
        return "I'm in offline mode right now. I can help with basic questions, but for more detailed explanations, please ensure Ollama is running or your Gemini API key is set up. What would you like to know?"

    def _get_response_from_ollama(self, prompt: str) -> Optional[str]:
        """Get response from Ollama"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.7,
                },
                timeout=120
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "").strip()
        except Exception as e:
            print(f"[ChatbotService] Ollama error: {e}")
        return None

    def _get_response_from_gemini(self, prompt: str) -> Optional[str]:
        """Get response from Gemini API"""
        try:
            response = self.gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"[ChatbotService] Gemini error: {e}")
        return None

    def _get_relevant_context(self, user_message: str, course_id: Optional[int] = None) -> str:
        """
        Fetch relevant content from database to provide context for the AI
        """
        if not self.db_session:
            return ""
        
        try:
            from models import Course, Lesson, Section, LearningObject
            
            query_lower = user_message.lower()
            stop_words = ["what", "is", "a", "an", "the", "whats", "what's", "how", "why", "does", "do", "can", "you", "tell", "me", "about", "explain", "?"]
            query_terms = [w for w in query_lower.split() if w not in stop_words and len(w) > 2]
            
            if not query_terms:
                return ""
            
            context_parts = []
            
            # Search Learning Objects for relevant content
            learning_objects = self.db_session.query(LearningObject).all()
            relevant_los = []
            for lo in learning_objects:
                lo_text = f"{lo.title or ''} {lo.description or ''}".lower()
                match_score = sum(1 for term in query_terms if term in lo_text)
                # Boost if term in title
                for term in query_terms:
                    if term in (lo.title or '').lower():
                        match_score += 3
                if match_score > 0:
                    relevant_los.append((match_score, lo))
            
            # Sort and get top 5 most relevant
            relevant_los.sort(key=lambda x: x[0], reverse=True)
            for score, lo in relevant_los[:5]:
                if lo.description:
                    context_parts.append(f"**{lo.title}**: {lo.description[:500]}")
            
            # Also get relevant sections
            sections = self.db_session.query(Section).all()
            relevant_sections = []
            for section in sections:
                section_text = f"{section.title or ''} {section.content or ''}".lower()
                match_score = sum(1 for term in query_terms if term in section_text)
                if match_score > 0:
                    relevant_sections.append((match_score, section))
            
            relevant_sections.sort(key=lambda x: x[0], reverse=True)
            for score, section in relevant_sections[:3]:
                if section.content:
                    context_parts.append(f"**Section - {section.title}**: {section.content[:400]}")
            
            if context_parts:
                return "\n\n".join(context_parts)
            
            return ""
            
        except Exception as e:
            print(f"[ChatbotService] Context fetch error: {e}")
            return ""

    def generate_response(
        self,
        user_message: str,
        course_context: Optional[str] = None,
        lesson_context: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None,
        course_id: Optional[int] = None
    ) -> Dict:
        """
        Generate chatbot response based on user message and context
        
        Args:
            user_message: The user's question/message
            course_context: Course name and description
            lesson_context: Current lesson content for context
            conversation_history: List of previous messages for context
            
        Returns:
            Dict with response and metadata
        """
        
        # Build system prompt with educational context
        system_prompt = """You are a helpful educational assistant for a learning platform. 
Your role is to:
- Answer questions about course content using the provided context
- Explain concepts clearly based on the learning materials
- Help students understand lessons and quiz answers
- Provide study guidance and tips
- Be encouraging and supportive

IMPORTANT: Use the "Relevant Course Content" below to answer the user's question. 
This content comes from their actual course materials.
Keep responses concise but thorough."""

        # Fetch relevant content from database
        db_context = self._get_relevant_context(user_message, course_id)
        
        # Add context if provided
        context_parts = []
        if course_context:
            context_parts.append(f"Current Course: {course_context}")
        if lesson_context:
            # Limit context to avoid token limits
            truncated_lesson = lesson_context[:self.max_context_length]
            context_parts.append(f"Lesson Content:\n{truncated_lesson}")
        
        # Add database context
        if db_context:
            context_parts.append(f"Relevant Course Content:\n{db_context}")

        # Build conversation history
        history_text = ""
        if conversation_history:
            for msg in conversation_history[-4:]:  # Keep last 4 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")
                history_text += f"{role.capitalize()}: {content}\n"

        # Combine into full prompt
        full_prompt = f"""{system_prompt}

{chr(10).join(context_parts)}

{history_text}

User: {user_message}
Assistant:"""

        # Debug: print the context being sent
        if db_context:
            print(f"[ChatbotService] Found relevant context: {len(db_context)} chars")

        # Try Ollama first
        response_text = None
        used_service = "ollama"
        ollama_available = self._test_ollama_connection()
        
        if ollama_available:
            print("[ChatbotService] Using Ollama for response")
            response_text = self._get_response_from_ollama(full_prompt)
        
        # Try Gemini second
        if not response_text:
            print("[ChatbotService] Trying Gemini for response")
            used_service = "gemini"
            response_text = self._get_response_from_gemini(full_prompt)
        
        # Fall back to offline mode
        if not response_text:
            print("[ChatbotService] Using offline mode")
            used_service = "offline"
            response_text = self._get_offline_response(user_message, course_id)

        return {
            "response": response_text.strip(),
            "service": used_service,
            "success": True
        }

    def generate_quiz_explanation(self, question: str, correct_answer: str, user_answer: Optional[str] = None) -> Dict:
        """
        Generate an explanation for a quiz question and answer
        
        Args:
            question: The quiz question
            correct_answer: The correct answer
            user_answer: User's answer (if incorrect, explain why)
            
        Returns:
            Dict with explanation
        """
        
        if user_answer and user_answer != correct_answer:
            prompt = f"""Please explain why the answer to this question is "{correct_answer}" and not "{user_answer}".

Question: {question}
Correct Answer: {correct_answer}
User's Answer: {user_answer}

Provide a brief, educational explanation that helps the student understand the concept."""
        else:
            prompt = f"""Please explain why this answer to the question is correct.

Question: {question}
Answer: {correct_answer}

Keep the explanation clear and educational."""

        response_text = None
        
        if self._test_ollama_connection():
            response_text = self._get_response_from_ollama(prompt)
        
        if not response_text:
            response_text = self._get_response_from_gemini(prompt)
        
        return {
            "explanation": response_text.strip() if response_text else "Unable to generate explanation",
            "success": response_text is not None
        }


# Singleton instance (db_session will be set from app.py)
chatbot_service = ChatbotService()
