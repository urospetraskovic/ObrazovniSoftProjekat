# SOLO Generator Kvizova

Inteligentni obrazovni softverski sistem koji automatski generiše pitanja za kvizove zasnovane na SOLO (Structure of Observed Learning Outcomes) taksonomiji. Aplikacija koristi lokalnu veštačku inteligenciju putem Ollama servisa za kreiranje pedagoški strukturiranih pitanja iz učitanih materijala za kurseve.

## Pregled

Ovaj projekat je dizajniran da pomogne nastavnicima da automatski kreiraju pitanja za procenu znanja na različitim kognitivnim nivoima. Sistem parsira PDF materijale za kurseve, gradi semantički graf znanja (ontologiju) i generiše pitanja sa višestrukim izborom kategorisana po SOLO taksonomskim nivoima:

- **Unistrukturalni** - Jednostavno prisećanje pojedinačnih činjenica
- **Multistrukturalni** - Identifikacija više povezanih činjenica
- **Relacioni** - Razumevanje veza između koncepata
- **Prošireni apstraktni** - Viši opseg mišljenja i primena

## Ključne funkcionalnosti

### Generisanje pitanja
- Učitavanje PDF materijala za kurseve
- Automatsko parsiranje u lekcije, sekcije i objekte učenja
- Generisanje pitanja pomoću veštačke inteligencije na svim SOLO nivoima
- Ručno kreiranje i uređivanje pitanja
- Upravljanje bankom pitanja

### Ontološki sistem
- Automatsko generisanje grafa znanja iz sadržaja
- SPARQL interfejs za upite i istraživanje relacija
- Izvoz u OWL format za korišćenje u Protégé-u
- Izvoz u Turtle format za RDF alate
- Vizuelno mapiranje relacija

### AI Chatbot
- Odgovori zasnovani na kontekstu sadržaja kursa
- Koristi RAG (Retrieval-Augmented Generation) arhitekturu
- Objašnjava odgovore na kvizu kada je studentima potrebna pomoć
- Offline rezervni režim kada AI nije dostupan

### Upravljanje kvizovima
- Kreiranje kvizova iz banke pitanja
- Filtriranje pitanja po temi, SOLO nivou ili lekciji
- Izvoz kvizova u JSON format
- Interaktivni interfejs za rešavanje kvizova
- Podrška za prevođenje na više jezika

### Sistem prevođenja
- Prevođenje pitanja na više jezika
- Grupno prevođenje
- Očuvanje SOLO metapodataka

## Tehnološki stek

**Backend:**
- Python 3.10+
- Flask 2.3.0 (REST API)
- SQLAlchemy 2.0.36 (ORM)
- SQLite (Baza podataka)
- RDFLib 7.0.0 (Ontologija/SPARQL)
- PyPDF2 (Parsiranje PDF-a)

**Frontend:**
- React 18
- Axios (HTTP klijent)
- CSS3 stilizacija

**AI sloj:**
- Ollama (lokalni LLM pokretač)
- Qwen 2.5 14B model 

## Preduslovi

Pre pokretanja aplikacije, uverite se da imate:

1. **Python 3.10 ili noviji** - [Preuzimanje](https://www.python.org/downloads/)
2. **Node.js 18 ili noviji** - [Preuzimanje](https://nodejs.org/)
3. **Ollama** - [Preuzimanje](https://ollama.com/)

## Instalacija

### 1. Kloniranje repozitorijuma

```bash
git clone <https://github.com/urospetraskovic/ObrazovniSoftProjekat>
cd front
```

### 2. Podešavanje Backend-a

```bash
cd backend

# Kreiranje virtualnog okruženja
python -m venv venv

# Aktiviranje virtualnog okruženja (Windows)
.\venv\Scripts\activate

# Aktiviranje virtualnog okruženja (Linux/Mac)
source venv/bin/activate

# Instaliranje zavisnosti
pip install -r requirements.txt
```

### 3. Podešavanje Frontend-a

```bash
cd frontend
npm install
```

### 4. Podešavanje Ollama

Preuzmite i instalirajte Ollama, zatim preuzmite preporučeni model:

```bash
ollama pull qwen2.5:14b
```

## Pokretanje aplikacije

Potrebno je pokrenuti 3 terminala istovremeno. Pogledajte [START_GUIDE.md](START_GUIDE.md) za brzi vodič za pokretanje.

**Terminal 1 - Ollama AI Server:**
```bash
.\ollama.ps1 serve
```

**Terminal 2 - Backend API:**
```bash
cd backend
.\venv\Scripts\python.exe app.py
```

**Terminal 3 - Frontend:**
```bash
cd frontend
npm start
```

Aplikacija će biti dostupna na `http://localhost:3000`

## Struktura projekta

```
front/
├── backend/
│   ├── app.py              # Flask API sa 60+ endpoint-a
│   ├── repository.py       # Konfiguracija baze podataka
│   ├── requirements.txt    # Python zavisnosti
│   ├── core/
│   │   ├── content_parser.py    # Logika parsiranja PDF-a
│   │   └── quiz_generator.py    # Generisanje SOLO pitanja
│   ├── models/
│   │   └── models.py       # SQLAlchemy modeli
│   ├── ontology/
│   │   └── seed_ontology.ttl    # Bazni ontološki šablon
│   ├── services/
│   │   ├── chatbot_service.py   # RAG chatbot
│   │   ├── sparql_service.py    # SPARQL upiti
│   │   ├── ontology_service.py  # OWL/Turtle izvoz
│   │   ├── translation_service.py # Prevodi
│   │   ├── quiz_service.py     # Kvizovi  
│   │   ├── lesson_service.py   # Vadjenje lekcija
│   │   └── question_service.py # Pravljenje pitanja
│   ├── uploads/            # Privremeni PDF upload-i
├── frontend/
│   ├── src/
│   │   ├── App.js          # Glavna aplikacija
│   │   ├── api.js          # API klijent
│   │   └── components/
│   │       ├── ChatBot.js
│   │       ├── QuizBuilder.js
│   │       ├── QuizSolver.js
│   │       ├── QuestionGenerator.js
│   │       ├── SPARQLQueryTool.js
│   │       └── ...
│   └── public/
│       └── index.html
├── raw_materials/          # Primeri fajlova lekcija
├── downloaded_quizzes/     # Izvezeni kviz fajlovi
├── ollama.ps1             # Ollama startup skripta
└── START_GUIDE.md         # Vodič za brzo pokretanje
```

## API Endpoint-i

Backend pruža 60+ REST API endpoint-a grupisanih po funkcionalnosti:

### Osnovni endpoint-i
- `GET /api/health` - Provera stanja
- `POST /api/sparql` - Izvršavanje SPARQL upita
- `GET /api/sparql/examples` - Primeri SPARQL upita

### Upravljanje kursevima
- `GET/POST /api/courses` - Lista/kreiranje kurseva
- `GET/DELETE /api/courses/:id` - Preuzimanje/brisanje kursa
- `GET/POST /api/courses/:id/lessons` - Lekcije kursa

### Upravljanje lekcijama
- `GET/DELETE /api/lessons/:id` - Preuzimanje/brisanje lekcije
- `POST /api/lessons/:id/parse` - Parsiranje sadržaja lekcije
- `GET /api/lessons/:id/sections` - Preuzimanje sekcija lekcije

### Ontologija
- `GET /api/lessons/:id/ontology` - Preuzimanje ontologije
- `POST /api/lessons/:id/ontology/generate` - Generisanje ontologije
- `GET /api/lessons/:id/ontology/export/owl` - Izvoz u OWL
- `GET /api/lessons/:id/ontology/export/turtle` - Izvoz u Turtle

### Pitanja
- `POST /api/generate-questions` - Generisanje pitanja pomoću AI
- `GET/POST /api/questions` - Lista/kreiranje pitanja
- `PUT/DELETE /api/questions/:id` - Ažuriranje/brisanje pitanja

### Kvizovi
- `GET/POST /api/quizzes` - Lista/kreiranje kvizova
- `GET /api/quizzes/:id/export` - Izvoz kviza

### Prevođenje
- `GET /api/translate/languages` - Dostupni jezici
- `POST /api/translate/question` - Prevođenje pitanja
- `POST /api/translate/quiz/:id` - Prevođenje celog kviza

### Chatbot
- `POST /api/chat` - Slanje poruke chatbot-u
- `POST /api/chat/explain-answer` - Objašnjenje odgovora na kvizu

## Šema baze podataka

Aplikacija koristi SQLite sa sledećim glavnim entitetima:

- **Course** - Kontejner najvišeg nivoa za lekcije
- **Lesson** - Pojedinačne lekcije sa PDF sadržajem
- **Section** - Podsekcije lekcija
- **LearningObject** - Atomske jedinice sadržaja za pitanja
- **Question** - Kviz pitanja sa SOLO nivoom
- **QuestionTranslation** - Prevedeni sadržaj pitanja
- **Quiz** - Kolekcija pitanja
- **OntologyRelationship** - Ivice grafa znanja

## Saveti za korišćenje

### Generisanje kvalitetnih pitanja

1. Učitajte dobro strukturirane PDF materijale
2. Parsirajte sadržaj da biste izdvojili objekte učenja
3. Generišite ontologiju da biste izgradili relacije znanja
4. Generišite pitanja - AI koristi i sadržaj i ontologiju
5. Pregledajte i uredite generisana pitanja po potrebi

### Korišćenje SPARQL upita

SPARQL alat vam omogućava da istražujete graf znanja:

```sparql
# Pronađi sve koncepte u lekciji
SELECT ?concept WHERE {
  ?concept a :Concept .
}

# Pronađi relacije između koncepata
SELECT ?subject ?predicate ?object WHERE {
  ?subject ?predicate ?object .
}
```

### Izvoz za Protégé

1. Idite na prikaz ontologije
2. Kliknite "Izvoz u OWL"
3. Otvorite preuzetu .owl datoteku u Protégé-u
4. Vizualizujte sa OntoGraf ili OWLViz dodacima

## Doprinos projektu

Ovaj projekat je razvijen kao deo istraživačkog projekta obrazovnog softvera fokusiranog na primenu SOLO taksonomije na automatsko generisanje pitanja.

## Licenca

Ovaj projekat je namenjen obrazovnim svrhama.
