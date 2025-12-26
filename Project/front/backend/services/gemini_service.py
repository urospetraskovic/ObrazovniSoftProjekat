"""
Gemini API Service for generating quiz content and educational materials
"""

import os
import json
from typing import Optional
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

genai.configure(api_key=GEMINI_API_KEY)


class GeminiService:
    """Service for interacting with Google's Gemini API"""

    def __init__(self, model: str = "gemini-2.0-flash"):
        """
        Initialize the Gemini service
        
        Args:
            model: The Gemini model to use (default: gemini-2.0-flash for faster responses)
        """
        self.model = genai.GenerativeModel(model)

    def generate_quiz_from_content(
        self, content: str, num_questions: int = 10, question_type: str = "multiple_choice"
    ) -> dict:
        """
        Generate quiz questions from educational content
        
        Args:
            content: The educational material to generate questions from
            num_questions: Number of questions to generate
            question_type: Type of questions (multiple_choice, true_false, short_answer)
            
        Returns:
            Dictionary with generated questions
        """
        prompt = f"""
        Based on the following educational content, generate {num_questions} quiz questions.
        Each question should be of type: {question_type}
        
        For multiple choice questions, provide 4 options (A, B, C, D) with one correct answer.
        For true/false questions, provide a statement and the correct answer.
        For short answer questions, provide a question and the expected answer.
        
        Return the response as a JSON array with the following structure:
        [
            {{
                "id": 1,
                "question": "The question text",
                "type": "{question_type}",
                "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"] (for multiple_choice),
                "correct_answer": "A" or the answer text,
                "explanation": "Brief explanation of the correct answer"
            }},
            ...
        ]
        
        Content:
        {content}
        """

        try:
            response = self.model.generate_content(prompt)
            # Parse the response as JSON
            json_str = response.text
            # Remove markdown formatting if present
            if json_str.startswith("```"):
                json_str = json_str.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
            
            questions = json.loads(json_str)
            return {"success": True, "questions": questions}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_learning_summary(self, content: str) -> dict:
        """
        Generate a concise summary of educational content
        
        Args:
            content: The educational material to summarize
            
        Returns:
            Dictionary with summary
        """
        prompt = f"""
        Create a concise educational summary of the following content.
        Include:
        1. Main topics covered
        2. Key concepts (3-5 bullets)
        3. Learning objectives
        4. Key takeaways
        
        Keep it concise and suitable for students.
        
        Content:
        {content}
        """

        try:
            response = self.model.generate_content(prompt)
            return {"success": True, "summary": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_lesson_objectives(self, lesson_title: str, content: str) -> dict:
        """
        Generate learning objectives for a lesson
        
        Args:
            lesson_title: Title of the lesson
            content: The lesson content
            
        Returns:
            Dictionary with learning objectives
        """
        prompt = f"""
        For a lesson titled "{lesson_title}", generate clear learning objectives.
        The objectives should be SMART (Specific, Measurable, Achievable, Relevant, Time-bound).
        Generate 5-7 objectives in the format:
        "By the end of this lesson, students will be able to..."
        
        Base the objectives on this content:
        {content}
        """

        try:
            response = self.model.generate_content(prompt)
            objectives = [line.strip() for line in response.text.split("\n") if line.strip()]
            return {"success": True, "objectives": objectives}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_quiz_explanation(self, question: str, correct_answer: str) -> str:
        """
        Generate a detailed explanation for a quiz question
        
        Args:
            question: The quiz question
            correct_answer: The correct answer
            
        Returns:
            Detailed explanation
        """
        prompt = f"""
        Provide a clear, educational explanation for this quiz answer:
        
        Question: {question}
        Correct Answer: {correct_answer}
        
        Explanation should be:
        - Clear and understandable for students
        - 2-3 sentences
        - Include why this answer is correct
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating explanation: {str(e)}"

    def test_connection(self) -> bool:
        """
        Test if the Gemini API connection is working
        
        Returns:
            True if connection is successful
        """
        try:
            response = self.model.generate_content("Say 'Connection successful' in one word")
            return True
        except Exception as e:
            print(f"Gemini API connection error: {str(e)}")
            return False


# Create a singleton instance
gemini_service = GeminiService()
