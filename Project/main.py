import os
import json
import shutil
from datetime import datetime
from dotenv import load_dotenv
import requests
from typing import Optional, Dict, Any

# Uvoz promptova
from prompts import SYSTEM_PROMPT, SOLO_GENERATION_PROMPTS, ANALYSIS_PROMPT, CONCEPT_EXTRACTION_PROMPT

class SoloQuestionGenerator:
    def __init__(self):
        load_dotenv()
        # Multi-key rotation system
        self.api_keys = [
            os.getenv('OPENROUTER_API_KEY'),
            os.getenv('OPENROUTER_API_KEY_2'),
            os.getenv('OPENROUTER_API_KEY_3'),
            os.getenv('OPENROUTER_API_KEY_4'),
            os.getenv('OPENROUTER_API_KEY_5'),
            os.getenv('OPENROUTER_API_KEY_6')
        ]
        # Filter out None values
        self.api_keys = [key for key in self.api_keys if key]
        
        if not self.api_keys:
            raise ValueError("Please set at least OPENROUTER_API_KEY in your .env file")
        
        self.current_key_index = 0
        self.api_key = self.api_keys[self.current_key_index]
        self.provider = "openrouter"
        print(f"✅ Loaded {len(self.api_keys)} API key(s). Starting with key #{self.current_key_index + 1}")

    def generate_completion(self, prompt, system_message=""):
        """
        Universal function that sends requests to different LLM providers.
        """
        try:
            if self.provider == "openrouter":
                return self._call_openrouter(prompt, system_message)
            elif self.provider == "deepseek":
                return self._call_deepseek(prompt, system_message)
            elif self.provider == "claude":
                return self._call_claude(prompt, system_message)
            elif self.provider == "gemini":
                return self._call_gemini(prompt, system_message)
            elif self.provider == "grok":
                return self._call_grok(prompt, system_message)
            elif self.provider == "openai":
                return self._call_openai(prompt, system_message)
            else:
                return self._mock_response()
        except Exception as e:
            print(f"Error with {self.provider}: {e}")
            return None
            
    def _call_openrouter(self, prompt, system_message):
        """OpenRouter API call (OpenAI-compatible)."""
        print("   (Sending request to OpenRouter model...)")
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "SOLO Question Generator"
        }
        data = {
            "model": "tngtech/deepseek-r1t2-chimera:free",  # Free model you mentioned
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            # Check if it's a rate limit error and we have more keys
            if response.status_code == 429 and len(self.api_keys) > 1:
                return self._handle_rate_limit_and_retry(prompt, system_message)
            else:
                raise Exception(f"OpenRouter API error: {response.status_code} - {response.text}")
    
    def _handle_rate_limit_and_retry(self, prompt, system_message):
        """Switch to next API key when rate limit is hit."""
        if self.current_key_index < len(self.api_keys) - 1:
            self.current_key_index += 1
            self.api_key = self.api_keys[self.current_key_index]
            print(f"⚠️ Rate limit reached. Switching to API key #{self.current_key_index + 1}")
            return self._call_openrouter(prompt, system_message)
        else:
            print(f"❌ All {len(self.api_keys)} API keys have reached their rate limits")
            raise Exception("All API keys exhausted. Please wait for rate limits to reset or add more credits.")
    
    def switch_api_key(self):
        """Manually switch to next API key."""
        if len(self.api_keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            self.api_key = self.api_keys[self.current_key_index]
            print(f"🔄 Switched to API key #{self.current_key_index + 1}")
            return True
        else:
            print("⚠️ Only one API key available, cannot switch")
            return False
    
    def _switch_api_key(self):
        """Manually switch to next API key."""
        if len(self.api_keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            self.api_key = self.api_keys[self.current_key_index]
            print(f"🔄 Switched to API key #{self.current_key_index + 1}")
            return True
        return False
            
    def _call_deepseek(self, prompt, system_message):
        """DeepSeek API call."""
        print("   (Sending request to DeepSeek model...)")
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(f"DeepSeek API error: {response.status_code}")
            
    def _call_claude(self, prompt, system_message):
        """Claude/Anthropic API call."""
        print("   (Sending request to Claude model...)")
        message = self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=2000,
            system=system_message,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text
        
    def _call_gemini(self, prompt, system_message):
        """Google Gemini API call."""
        print("   (Sending request to Gemini model...)")
        full_prompt = f"{system_message}\n\n{prompt}"
        response = self.client.generate_content(full_prompt)
        return response.text
        
    def _call_grok(self, prompt, system_message):
        """Grok API call (xAI)."""
        print("   (Sending request to Grok model...)")
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "grok-beta",
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(f"Grok API error: {response.status_code}")
            
    def _call_openai(self, prompt, system_message):
        """OpenAI API call (older models)."""
        print("   (Sending request to OpenAI model...)")
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",  # Cheaper older model
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
        
    def _mock_response(self):
        """Mock response for testing."""
        return '{"question": "Mock question", "options": ["A) Mock", "B) Mock", "C) Mock"], "correct_answer": "A", "explanation": "Mock explanation"}'

    def load_text(self, file_path):
        """Loads clean textual content from file."""
        print(f"Loading text file: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"  - Loaded {len(content)} characters")
            return content
        except Exception as e:
            return f"Loading error: {e}"

    def split_by_chapters(self, text):
        """Splits text by chapters or logical sections."""
        # Try splitting by chapters (different markers)
        chapter_markers = [
            r'\n\s*(?:CHAPTER|SECTION|LESSON)\s*\d+',
            r'\n\s*(?:POGLAVLJE|GLAVA|LEKCIJA)\s*\d+',  # Keep Serbian support
            r'\n\s*\d+\.\s*[A-ZŠĐČĆŽ]',
            r'\n\s*[A-ZŠĐČĆŽ][A-ZŠĐČĆŽ\s]{10,}\n',
            r'\n\s*#{1,3}\s*[A-ZŠĐČĆŽ]'
        ]
        
        import re
        for pattern in chapter_markers:
            splits = re.split(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
            if len(splits) > 1:
                print(f"  - Split into {len(splits)} chapters using pattern: {pattern[:20]}...")
                return [chunk.strip() for chunk in splits if chunk.strip()]
        
        # If no clear chapters, split by paragraphs (double newline)
        paragraphs = text.split('\n\n')
        if len(paragraphs) > 3:
            print(f"  - Split into {len(paragraphs)} paragraphs")
            return [p.strip() for p in paragraphs if len(p.strip()) > 100]
        
        # Fallback to fixed chunks if nothing works
        chunk_size = 3000  # Larger chunks for better context understanding
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        print(f"  - Fallback split into {len(chunks)} chunks of {chunk_size} characters")
        return chunks

    def extract_concepts(self, text_chunk):
        """
        PHASE 1: Extracts key concepts from text that are suitable for SOLO questions.
        """
        print("  -> Extracting concepts from text...")
        prompt = CONCEPT_EXTRACTION_PROMPT.format(text=text_chunk)
        response = self.generate_completion(prompt, system_message=SYSTEM_PROMPT)
        return response

    def analyze_text_structure(self, text_chunk):
        """
        PHASE 2: Analyzes text and extracts key elements (definitions, enumerations, relationships).
        """
        print("  -> Analyzing text structure...")
        prompt = ANALYSIS_PROMPT.format(text=text_chunk)
        response = self.generate_completion(prompt, system_message=SYSTEM_PROMPT)
        return response

    def generate_questions_with_llm(self, analysis_data, level):
        """
        Generates questions using available LLM.
        Uses previously analyzed data.
        """
        # Format prompt with analyzed data
        prompt = SOLO_GENERATION_PROMPTS[level].format(analysis_data=analysis_data)
        
        response_text = self.generate_completion(prompt, system_message=SYSTEM_PROMPT)
        
        if response_text:
            # Try to parse response or just return it
            return response_text
        else:
            # Fallback to mock if LLM doesn't work
            return self.mock_generate_questions_by_level(level)

    def _parse_json_response(self, response_text):
        """Pokušava da parsira JSON odgovor iz LLM-a."""
        if not response_text:
            return {}
        
        # Pronađi prvi { i poslednji }
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        
        if start != -1 and end != -1:
            json_str = response_text[start:end]
            return json.loads(json_str)
        else:
            raise ValueError("Nema validni JSON u odgovoru")
            
    def _validate_answer_sources(self, question_data, source_text):
        """Validates that correct answers are based on source material."""
        if not isinstance(question_data, dict):
            return {"status": "invalid_format"}
            
        # Check for both English and Serbian field names for compatibility
        correct_answer = question_data.get("correct_answer", question_data.get("tacan_odgovor", ""))
        explanation = question_data.get("explanation", question_data.get("objasnjenje", ""))
        
        # Simple validation - check if key words from answer appear in source text
        answer_words = correct_answer.lower().split()
        explanation_words = explanation.lower().split()
        source_lower = source_text.lower()
        
        answer_match_count = sum(1 for word in answer_words if len(word) > 3 and word in source_lower)
        explanation_match_count = sum(1 for word in explanation_words if len(word) > 3 and word in source_lower)
        
        return {
            "status": "validated",
            "answer_source_coverage": answer_match_count / max(len(answer_words), 1),
            "explanation_source_coverage": explanation_match_count / max(len(explanation_words), 1),
            "likely_from_material": (answer_match_count + explanation_match_count) > 2
        }
            
        tacan_odgovor = question_data.get("tacan_odgovor", "")
        objasnjenje = question_data.get("objasnjenje", "")
        
        # Jednostavna validacija - da li se ključne reči iz odgovora nalaze u tekstu
        answer_words = tacan_odgovor.lower().split()
        explanation_words = objasnjenje.lower().split()
        source_lower = source_text.lower()
        
        answer_match_count = sum(1 for word in answer_words if len(word) > 3 and word in source_lower)
        explanation_match_count = sum(1 for word in explanation_words if len(word) > 3 and word in source_lower)
        
        return {
            "status": "validated",
            "answer_source_coverage": answer_match_count / max(len(answer_words), 1),
            "explanation_source_coverage": explanation_match_count / max(len(explanation_words), 1),
            "likely_from_material": (answer_match_count + explanation_match_count) > 2
        }

    def mock_generate_questions_by_level(self, level):
        """
        Generate realistic mock questions based on SOLO level.
        """
        mock_questions = {
            "prestructural": {
                "question": "What is a cell?",
                "options": ["A) The smallest unit of life", "B) A type of tissue", "C) A body organ"],
                "correct_answer": "A",
                "explanation": "A cell is the basic unit of life that can function independently."
            },
            "multistructural": {
                "question": "Which of the following are components of photosynthesis?",
                "options": ["A) Chlorophyll, sunlight, oxygen", "B) Carbon dioxide, water, sunlight", "C) Glucose, oxygen, nitrogen"],
                "correct_answer": "B", 
                "explanation": "Photosynthesis requires carbon dioxide, water, and sunlight to produce glucose and oxygen."
            },
            "relational": {
                "question": "How does cellular respiration relate to photosynthesis?",
                "options": ["A) They are the same process", "B) They are opposite processes", "C) They are unrelated"],
                "correct_answer": "B",
                "explanation": "Cellular respiration breaks down glucose using oxygen, while photosynthesis produces glucose and oxygen."
            },
            "extended_abstract": {
                "question": "If all plants on Earth suddenly disappeared, what would happen to animal life?",
                "options": ["A) Animals would adapt quickly", "B) Only herbivores would be affected", "C) Most animal life would eventually die"],
                "correct_answer": "C",
                "explanation": "Without plants, oxygen levels would drop and food webs would collapse, affecting most animal life."
            }
        }
        
        return json.dumps(mock_questions.get(level, mock_questions["prestructural"]))

    def run_pipeline(self, file_path):
        """Glavni tok rada - dvofazni pristup sa izdvajanjem koncepata."""
        text = self.load_text(file_path)
        if not text:
            return []

        # Podela po poglavljima umesto proizvoljnih chunk-ova
        chapters = self.split_by_chapters(text)
        all_results = []
        
        # Process all chapters (remove [:1] for full processing)
        demo_chapters = chapters  # Process all chapters 
        
        for i, chapter in enumerate(demo_chapters):
            print(f"\n=== PROCESSING CHAPTER {i+1}/{len(demo_chapters)} ===")
            print(f"Length: {len(chapter)} characters")
            
            chapter_results = {
                "chapter_number": i+1,
                "content_preview": chapter[:100] + "..." if len(chapter) > 100 else chapter,
                "concepts": [],
                "questions": []
            }
            
            # PHASE 1: Concept extraction
            print("\n📋 PHASE 1: Extracting concepts...")
            concepts_raw = self.extract_concepts(chapter)
            
            if not concepts_raw:
                print("  ! Concept extraction failed.")
                continue
            
            # Try parsing concepts
            try:
                concepts_data = self._parse_json_response(concepts_raw)
                chapter_results["concepts"] = concepts_data
                concepts_count = len(concepts_data.get('concepts', concepts_data.get('koncepti', [])))
                print(f"  ✅ Extracted {concepts_count} concepts")
            except:
                chapter_results["concepts"] = {"raw": concepts_raw}
                print("  ⚠️ Concepts could not be parsed, saved as raw")

            # PHASE 2: Generate questions for each concept
            print("\n❓ PHASE 2: Generating SOLO questions...")
            
            # Koristi originalni ANALYSIS_PROMPT za kompatibilnost sa postojećim promptovima
            analysis_result = self.analyze_text_structure(chapter)
            
            if analysis_result:
                target_levels = ["prestructural", "multistructural", "relational", "extended_abstract"]
                
                for level in target_levels:
                    print(f"  - Generating {level} question...")
                    question_raw = self.generate_questions_with_llm(analysis_result, level)
                    
                    if question_raw:
                        try:
                            question_data = self._parse_json_response(question_raw)
                            chapter_results["questions"].append({
                                "solo_level": level,
                                "question_data": question_data,
                                "validation": self._validate_answer_sources(question_data, chapter)
                            })
                        except:
                            chapter_results["questions"].append({
                                "solo_level": level,
                                "raw_content": question_raw
                            })
            
            all_results.append(chapter_results)
            
        # Save results
        output_file = "generisana_pitanja.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Done! Results saved in '{output_file}')")
            
        return all_results

if __name__ == "__main__":
    # Ime fajla koji želimo da obradimo - fokusiramo se na tekstualne fajlove
    input_file = "raw_material/ecology_lesson.txt"
    
    # Create test file if it doesn't exist
    if not os.path.exists(input_file):
        print(f"File {input_file} not found. Creating test example.")
        test_content = """
CHAPTER 1: PHOTOSYNTHESIS

Photosynthesis is the process by which plants use sunlight to convert carbon dioxide and water into glucose and oxygen.

Basic components of photosynthesis:
- Chlorophyll (green pigment)
- Sunlight
- Carbon dioxide from air
- Water from roots

CHAPTER 2: IMPORTANCE OF PHOTOSYNTHESIS

This process is crucial for life on Earth because:
1. It produces oxygen that we breathe
2. It allows plants to create food
3. It removes carbon dioxide from the atmosphere

Without photosynthesis, life as we know it would not be possible.
"""
        with open(input_file, "w", encoding="utf-8") as f:
            f.write(test_content.strip())
        print(f"✅ Created test file: {input_file}")

def get_next_version_number():
    """Get the next version number for Q&A file."""
    quiz_dir = "generated_quizzes"
    if not os.path.exists(quiz_dir):
        return 1
    
    # Find existing version files
    existing_files = [f for f in os.listdir(quiz_dir) if f.startswith("questions_and_answers_v") and f.endswith(".txt")]
    
    if not existing_files:
        return 1
    
    # Extract version numbers
    version_numbers = []
    for filename in existing_files:
        try:
            # Extract number from "questions_and_answers_v{number}.txt"
            version_str = filename.replace("questions_and_answers_v", "").replace(".txt", "")
            version_numbers.append(int(version_str))
        except ValueError:
            continue
    
    return max(version_numbers) + 1 if version_numbers else 1

if __name__ == "__main__":
    # Start main process
    print(f"\n🚀 Starting SOLO Question Generator...")
    print(f"📂 Input file: {input_file}")
    
    generator = SoloQuestionGenerator() 
    rezultat = generator.run_pipeline(input_file)
    
    print(f"\n🎉 Process completed! Generated questions for {len(rezultat)} chapters.")
    print("📄 Results saved in 'generisana_pitanja.json'")
    
    # Create versioned copy of Q&A file if it exists
    qa_file = "questions_and_answers.txt"
    if os.path.exists(qa_file):
        version_number = get_next_version_number()
        versioned_filename = f"questions_and_answers_v{version_number}.txt"
        versioned_path = os.path.join("generated_quizzes", versioned_filename)
        
        try:
            shutil.copy2(qa_file, versioned_path)
            print(f"📁 Created versioned copy: {versioned_path}")
        except Exception as e:
            print(f"⚠️ Could not create versioned copy: {e}")
    
