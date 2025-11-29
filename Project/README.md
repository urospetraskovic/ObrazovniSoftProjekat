# SOLO Taxonomy Question Generator

Ovaj projekat ima za cilj razvoj sistema koji automatski generiše pitanja iz nastavnog materijala i klasifikuje ih prema SOLO (Structure of the Observed Learning Outcome) taksonomiji.

## Cilj Projekta
Automatizacija kreiranja testova i pitanja koja proveravaju različite nivoe razumevanja, od jednostavnog prepoznavanja činjenica do složene sinteze i primene znanja.

## SOLO Taksonomija
Sistem generiše pitanja za sledeće nivoe:
1.  **Prestructural**: Jednostavna identifikacija, nema povezivanja. (Npr. "Šta je X?")
2.  **Unistructural**: Fokus na jedan relevantan aspekt. (Npr. "Navedi jednu osobinu X.")
3.  **Multistructural**: Fokus na više nezavisnih aspekata. (Npr. "Nabroj tri karakteristike X.")
4.  **Relational**: Povezivanje aspekata u celinu. (Npr. "Uporedi X i Y.", "Kako X utiče na Y?")
5.  **Extended Abstract**: Generalizacija i primena na nove domene. (Npr. "Šta bi se desilo da X ne postoji?", "Dizajniraj rešenje koristeći X.")

## Arhitektura Sistema
1.  **Ingestion & Preprocessing**: Učitavanje materijala (PDF, TXT) i čišćenje teksta.
2.  **Chunking**: Podela teksta na logičke celine (definicije, primeri).
3.  **Information Extraction**: Identifikacija ključnih koncepata i činjenica (uz pomoć LLM).
4.  **Question Generation**: Generisanje kandidata pitanja za svaki SOLO nivo koristeći specifične promptove.
5.  **Classification & Validation**: Verifikacija SOLO nivoa (Rule-based + LLM check).
6.  **Output**: Strukturirani JSON/Export sa pitanjima.

## Tehnologije
- **Python**: Osnovni programski jezik.
- **LLM (OpenAI GPT-4/3.5)**: Za generisanje teksta i semantičku analizu.
- **LangChain** (opciono): Za orkestraciju LLM poziva.
- **PDFMiner/PyMuPDF**: Za obradu dokumenata.

## Kako pokrenuti
1. Instalirati zavisnosti: `pip install -r requirements.txt`
2. Postaviti API ključ: `export OPENAI_API_KEY='sk-...'`
3. Pokrenuti skriptu: `python main.py --input materijal.txt`
