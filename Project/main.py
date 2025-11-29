import os
import json
from dotenv import load_dotenv
import pypdf

# Pokušaj importa ollama biblioteke
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# Učitaj environment varijable iz .env fajla
load_dotenv()

# Uvoz promptova
from prompts import SYSTEM_PROMPT, SOLO_GENERATION_PROMPTS, ANALYSIS_PROMPT

class SoloQuestionGenerator:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.use_ollama = False
        
        if self.api_key:
            print("✅ OpenAI API ključ pronađen.")
            # self.client = openai.OpenAI(api_key=self.api_key)
        elif OLLAMA_AVAILABLE:
            print("✅ OpenAI ključ nije nađen, ali 'ollama' biblioteka jeste. Koristim lokalni Llama3 model.")
            self.use_ollama = True
        else:
            print("⚠️  Nema API ključa ni Ollama biblioteke. Radim u simuliranom (MOCK) režimu.")

    def generate_completion(self, prompt, system_message=""):
        """
        Univerzalna funkcija koja šalje zahtev ili OpenAI-u ili Ollami.
        """
        full_prompt = f"{system_message}\n\n{prompt}"
        
        if self.use_ollama:
            model_name = os.getenv("OLLAMA_MODEL", "llama3")
            try:
                print(f"   (Šaljem zahtev lokalnom Ollama modelu: {model_name}...)")
                response = ollama.chat(model=model_name, messages=[
                    {'role': 'system', 'content': system_message},
                    {'role': 'user', 'content': prompt},
                ])
                return response['message']['content']
            except Exception as e:
                print(f"Greška sa Ollama: {e}")
                return None
        
        elif self.api_key:
            # Ovde bi išao pravi OpenAI poziv
            # return self.client.chat.completions.create(...)
            return "OpenAI poziv još nije implementiran (placeholder)."
        
        else:
            # Mock response
            return None

    def load_text(self, file_path):
        """Učitava tekst iz fajla (txt ili pdf)."""
        print(f"Učitavam fajl: {file_path}")
        try:
            if file_path.lower().endswith('.pdf'):
                return self.load_pdf(file_path)
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            return f"Greška pri učitanju: {e}"

    def load_pdf(self, file_path):
        """Ekstrakcija teksta iz PDF-a."""
        text = ""
        try:
            with open(file_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                print(f"  - PDF ima {len(reader.pages)} stranica.")
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Greška pri čitanju PDF-a: {e}")
            return ""

    def chunk_text(self, text, chunk_size=2000):
        """Jednostavna podela teksta na delove."""
        # Povećavamo chunk_size da šaljemo manje zahteva
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

    def analyze_text_structure(self, text_chunk):
        """
        Korak A: Analizira tekst i izvlači ključne elemente (definicije, nabrajanja, veze).
        """
        print("  -> Analiziram strukturu teksta...")
        prompt = ANALYSIS_PROMPT.format(text=text_chunk)
        response = self.generate_completion(prompt, system_message=SYSTEM_PROMPT)
        return response

    def generate_questions_with_llm(self, analysis_data, level):
        """
        Generiše pitanja koristeći dostupni LLM (Ollama ili OpenAI).
        Koristi prethodno analizirane podatke.
        """
        # Formatiramo prompt sa analiziranim podacima
        prompt = SOLO_GENERATION_PROMPTS[level].format(analysis_data=analysis_data)
        
        response_text = self.generate_completion(prompt, system_message=SYSTEM_PROMPT)
        
        if response_text:
            # Pokušavamo da parsiramo odgovor ili ga samo vratimo
            return response_text
        else:
            # Fallback na mock ako LLM ne radi
            return self.mock_generate_questions(analysis_data)

    def mock_generate_questions(self, text_chunk):
        """
        Privremena funkcija koja simulira rad LLM-a dok ne povežemo API.
        Vraća strukturu pitanja kakvu očekujemo od modela.
        """
        print("--- Simuliram generisanje pitanja za chunk (MOCK) ---")
        # Simulirani odgovor
        return {
            "mock_data": True,
            "questions": [
                {
                    "level": "Unistructural",
                    "question": "Šta je glavni pojam definisan u tekstu?",
                    "answer_key": "Definicija X..."
                }
            ]
        }

    def run_pipeline(self, file_path):
        text = self.load_text(file_path)
        if not text:
            return []

        chunks = self.chunk_text(text)
        all_questions = []
        
        # OGRANIČENJE: Uzimamo samo PRVI chunk za testiranje brzine
        # Kada budeš hteo sve, skloni [:1]
        demo_chunks = chunks[:1] 
        
        for i, chunk in enumerate(demo_chunks):
            print(f"Obrađujem deo {i+1}/{len(demo_chunks)}...")
            
            # KORAK 1: Analiza strukture (Sarsa et al. metodologija)
            analysis_result = self.analyze_text_structure(chunk)
            if not analysis_result:
                print("  ! Analiza nije uspela, preskačem chunk.")
                continue

            chunk_results = {"source_chunk": chunk[:50] + "...", "analysis": analysis_result[:100]+"...", "questions": []}
            
            # KORAK 2: Generisanje pitanja po nivoima
            # Sada možemo uključiti više nivoa jer je analiza urađena jednom
            target_levels = ["prestructural", "multistructural", "relational", "extended_abstract"]
            
            for level in target_levels:
                print(f"  - Generišem {level} pitanje...")
                result = self.generate_questions_with_llm(analysis_result, level)
                
                # Pokušaj da očistiš JSON ako model vrati dodatni tekst
                try:
                    # Pronađi prvi { i poslednji }
                    start = result.find('{')
                    end = result.rfind('}') + 1
                    if start != -1 and end != -1:
                        json_str = result[start:end]
                        parsed_json = json.loads(json_str)
                        chunk_results["questions"].append({
                            "level": level,
                            "data": parsed_json
                        })
                    else:
                        chunk_results["questions"].append({
                            "level": level,
                            "raw_content": result
                        })
                except:
                     chunk_results["questions"].append({
                        "level": level,
                        "raw_content": result
                    })
            
            all_questions.append(chunk_results)
            
        # Čuvanje u fajl umesto ispisivanja na ekran
        output_file = "generisana_pitanja.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_questions, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Gotovo! Rezultati sačuvani u '{output_file}'")
            
        return all_questions

if __name__ == "__main__":
    # Ime fajla koji želimo da obradimo
    # Možeš promeniti ovo u "2024_7_SBSG_Malware.pdf" kada ga ubaciš u folder
    input_file = "lekcija_primer.txt" 
    
    # Provera da li postoji PDF koji je korisnik pomenuo
    pdf_file = "2024_7_SBSG_Malware.pdf"
    if os.path.exists(pdf_file):
        input_file = pdf_file
        print(f"Pronađen PDF fajl: {input_file}")

    # Kreiramo dummy fajl za test ako ne postoji ni jedan drugi
    if not os.path.exists(input_file):
        print(f"Fajl {input_file} nije pronađen. Kreiram test primer.")
        input_file = "lekcija_primer.txt"
        with open(input_file, "w", encoding="utf-8") as f:
            f.write("Fotosinteza je proces kojim biljke koriste sunčevu svetlost da pretvore ugljen-dioksid i vodu u glukozu i kiseonik. Ovaj proces je ključan za život na Zemlji jer proizvodi kiseonik koji udišemo. Hlorofil je pigment koji biljkama daje zelenu boju i omogućava apsorpciju svetlosti.")
    
    generator = SoloQuestionGenerator() 
    rezultat = generator.run_pipeline(input_file)
    
    print("\nGenerisana pitanja su sačuvana u fajl.")
    # print(json.dumps(rezultat, indent=2, ensure_ascii=False))
