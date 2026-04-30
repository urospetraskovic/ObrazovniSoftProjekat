# SOLO Quiz Generator — Struktura projekta

Ovaj dokument opisuje arhitekturu, glavne module i tok podataka kroz aplikaciju.
Namenjen je kao brz orijentir za razvoj i buduće promene.

---

## 1. Šta je projekat

**SOLO Quiz Generator** je obrazovna aplikacija koja:

- prima PDF lekcije (npr. iz predmeta "Operativni sistemi"),
- automatski (LLM) parsira lekciju u **sekcije** i **learning objekte**,
- gradi **domensku ontologiju** (relacije među pojmovima),
- generiše pitanja po **SOLO taksonomiji** (Unistructural, Multistructural,
  Relational, Extended Abstract),
- omogućava ručno dodavanje, prevođenje i eksport pitanja u kvizove,
- nudi **chatbot** za obrazovnu pomoć i **SPARQL** upite nad ontologijom.

LLM backend je lokalni **Ollama** (model `qwen2.5:14b-instruct-q4_K_M`),
tako da nema cloud API troškova.

---

## 2. Tehnološki stek

| Sloj      | Tehnologije                                                           |
|-----------|-----------------------------------------------------------------------|
| Backend   | Python 3, Flask, Flask-CORS, SQLAlchemy 2 (SQLite), rdflib, PyPDF2    |
| LLM       | Ollama (HTTP API), model `qwen2.5:14b-instruct-q4_K_M`                |
| Frontend  | React 18, axios, react-scripts (CRA)                                  |
| Ontologija| OWL/RDF (RDF/XML i Turtle), SPARQL                                    |
| Skladište | SQLite fajl `backend/quiz_database.db`                                |

---

## 3. Struktura direktorijuma (top-level)

```
Project/front/
├── backend/                # Flask API + servisi + ML pipeline
├── frontend/               # React SPA
├── raw_materials/          # Test PDF/TXT lekcije
├── downloaded_quizzes/     # Eksportovani JSON kvizovi
├── Paper/                  # Akademski rad o projektu
├── ollama.ps1              # PowerShell pokretač za Ollama
├── start.sh                # Bash skripta za pokretanje
├── README.md / README_SRB.md / START_GUIDE.md
└── structure.md            # (ovaj fajl)
```

---

## 4. Backend (`backend/`)

### 4.1 Ulazna tačka

- **`app.py`** — Flask application factory.
  - poziva `config.ensure_folders()` i `config.apply_to(app)`,
  - `_bootstrap_services()` inicijalizuje DB, SPARQL ontologiju i chatbot sesiju,
  - `register_routes(app)` registruje sve blueprintove.
  - Pokreće se sa `python app.py` (debug, `localhost:5000`).

- **`config.py`** — folder konstante (`UPLOAD_FOLDER`, `LESSON_FOLDER`,
  `DOWNLOAD_FOLDER`), `ALLOWED_EXTENSIONS`, `MAX_FILE_SIZE` (30 MB) i helperi
  `ensure_folders()` / `apply_to(app)`.

### 4.2 Routes (`backend/routes/`)

Svaki blueprint pokriva jedan domen i zove servise + repozitorijum.
`routes/__init__.py` izlaže `register_routes(app)` koji ih sve montira.

| Fajl                       | Domen / prefiks         | Sažetak                                                   |
|----------------------------|-------------------------|-----------------------------------------------------------|
| `health.py`                | `/api/health`           | Health-check endpoint                                     |
| `sparql.py`                | `/api/sparql`           | Izvršavanje SPARQL upita, predefinisani primeri           |
| `courses.py`               | `/api/courses`          | CRUD nad kursevima                                        |
| `lessons.py`               | `/api/...`              | Upload PDF lekcije, parsiranje sadržaja                   |
| `sections.py`              | `/api/...`              | Lista i detalji sekcija jedne lekcije                     |
| `learning_objects.py`      | `/api/...`              | CRUD nad learning objektima                               |
| `ontology.py`              | `/api/...`              | Generisanje, brisanje, eksport (OWL/Turtle), KB statistika|
| `questions.py`             | `/api/...`              | Generisanje pitanja (LLM), CRUD nad pitanjima             |
| `quizzes.py`               | `/api/...`              | Kreiranje kvizova, dodavanje pitanja, JSON eksport        |
| `translations.py`          | `/api/translate, /api/...` | Prevod pitanja, lekcija, sekcija, LO, ontologija, kursa |
| `chat.py`                  | `/api/chat`             | Chatbot razgovor i objašnjenja kvizovskih odgovora        |
| `errors.py`                | n/a                     | `register_error_handlers(app)` (413, 500)                 |

### 4.3 Models (`backend/models/`)

`models/models.py` sadrži sve SQLAlchemy ORM klase. `__init__.py` ih reeksportuje.

Klase i njihova svrha:

- **`Course`** — predmet (top-level kontejner).
- **`Lesson`** — jedna lekcija (PDF + sirovi tekst + summary).
- **`Section`** — logička sekcija unutar lekcije.
- **`LearningObject`** — atomska jedinica znanja (definicija, koncept...).
- **`ConceptRelationship`** — relacija između dva LO-a (osnova ontologije).
- **`Question`** — pitanje sa SOLO nivoom (`SoloLevel` enum), opcijama, odgovorom.
- **`Quiz`** + **`QuizQuestion`** — kviz i veza N–N na pitanja.
- **`QuestionTranslation`** / **`LessonTranslation`** /
  **`SectionTranslation`** / **`LearningObjectTranslation`** /
  **`OntologyTranslation`** — prevodi za svaki tip resursa.

`engine` i `Session` se kreiraju nad lokalnim SQLite fajlom
`backend/quiz_database.db`.

### 4.4 Repository (`backend/repository.py`)

Tanak DAO sloj iznad SQLAlchemy. Sadrži:

- `init_database()` — kreira sve tabele.
- `Database` klasa sa CRUD metodama (`get_all_courses`, `create_course`,
  `delete_course`, `get_lessons_for_course`, `create_lesson`,
  `bulk_create_sections_and_learning_objects`, `update_question`,
  `bulk_create_relationships`, ...).
- Singleton `db = Database()` koji koriste route-ovi i servisi.

Cilj je da rute ne dotiču SQLAlchemy direktno, osim za par specifičnih upita.

### 4.5 Services (`backend/services/`)

Poslovna logika i AI integracije.

| Fajl                       | Uloga                                                                                |
|----------------------------|--------------------------------------------------------------------------------------|
| `lesson_service.py`        | `LessonService.parse_lesson()` — orkestracija parsiranja lekcije                     |
| `question_service.py`      | `QuestionService.generate_questions()` — generisanje SOLO pitanja                    |
| `quiz_service.py`          | Pomoćne operacije nad kvizovima                                                      |
| `ontology_service.py`      | `generate_owl_from_relationships()`, `generate_turtle_from_relationships()`         |
| `ontology_manager.py`      | `OntologyManager` — spaja seed TBox (`ontology/`) sa DB ABox-om u kompletan KB        |
| `sparql_service.py`        | Učitava ontologiju i izvršava SPARQL upite (rdflib)                                  |
| `chatbot_service.py`       | `ChatbotService` — pozivi prema Ollama, kontekstualni odgovori, fallback offline mod |
| `translation_service.py`   | Prevodi sve resurse, `SUPPORTED_LANGUAGES` mapa, batch prevod                        |

`services/__init__.py` reeksportuje glavne entitete (`LessonService`,
`QuestionService`, `QuizService`, `ontology_manager`, `get_translation_service`,
`chatbot_service`, ...).

### 4.6 Core (`backend/core/`)

LLM pipeline za parsiranje sadržaja i generisanje pitanja.

- **`content_parser.py`** — `ContentParser` (zove Ollama):
  - `extract_pdf_text_from_stream()` — PyPDF2 ekstrakcija,
  - `parse_lesson_structure()` — multi-pass podela na sekcije + LO,
  - `extract_ontology_relationships()` — vadi odnose iz teksta.
- **`quiz_generator.py`** — `SoloQuizGeneratorLocal`:
  - po jedan prompt po SOLO nivou,
  - generiše distraktore i tačan odgovor,
  - radi u "MAXIMUM QUALITY" multi-pass režimu.
- **`__init__.py`** reeksportuje `content_parser` (instanca) i
  `SoloQuizGeneratorLocal`.

### 4.7 Ontology (`backend/ontology/`)

Statički resursi za RDF/OWL:

- `seed_ontology.owl` / `seed_ontology.ttl` — bazna ontologija (TBox: klase,
  property-ji),
- `seed_ontology_base.owl` — fallback minimalna seed,
- `OS_ontology_exported.owl` — eksportovana puna ontologija (sa primerom
  podataka).

`OntologyManager` čita seed, dodaje individue iz baze i vraća kompletan KB.

### 4.8 Ostalo

- `uploads/` — privremene PDF datoteke (uglavnom prazno; PDF se obrađuje iz
  streama bez snimanja).
- `lessons/` — opciono trajno skladište PDF-ova ako se koristi `file_path`.
- `quiz_database.db` — SQLite baza (~4 MB sa test podacima).
- `requirements.txt` — pinovane verzije Flask 2.3, SQLAlchemy 2.0.36,
  rdflib 7.0, PyPDF2 3.0.1.

---

## 5. Frontend (`frontend/`)

CRA aplikacija (React 18 + axios). Pokretanje: `npm start` (port 3000).
Build: `npm run build` (produkcijski bundle ~85 KB gz).

### 5.1 Ulazna tačka

- **`src/index.js`** — montira `<App />` u `#root`.
- **`src/App.js`** — orchestrator.
  - drži `activeTab`, `chatbotOpen` u lokalnom stanju,
  - sve API/data state delegira na hook `useAppData`,
  - render se svodi na `Sidebar`, `TopBar`, `AlertMessages`, `TabContent`,
    `HowItWorksCard`, `ChatBot`.

### 5.2 API klijent

- **`src/api.js`** — jedna axios instanca + grupisani objekti
  (`courseApi`, `lessonApi`, `sectionApi`, `learningObjectApi`, `questionApi`,
  `quizApi`, `healthApi`, `ontologyApi`, `chatApi`, `translationApi`).
  Bazni URL: `http://localhost:5000/api`.

### 5.3 Custom hook (`src/hooks/`)

- **`useAppData.js`** — centralni state-management hook:
  - drži `courses`, `selectedCourse`, `selectedLesson`, `questions`,
    `loading`, `error`, `success`, `apiStatus`,
  - izlaže `fetchCourses`, `fetchQuestions`, `handleSelectCourse`,
    `handleSelectLesson`, `showSuccess`, `showError`, `clearMessages`,
  - polluje `/api/health` svakih 30s.

### 5.4 Layout komponente (`src/components/layout/`)

- **`Sidebar.js`** — leva navigacija. Stavke su definisane u `NAV_ITEMS`
  konstanti (po grupama: workflow, questions, content); ikonice su inlajn SVG.
  Svaka stavka može imati `requires: 'course' | 'lesson'` zbog disabled stanja.
- **`TopBar.js`** — breadcrumb (course / lesson) + status API ključeva.
- **`AlertMessages.js`** — error/success/api-exhausted alert kartice.
- **`HowItWorksCard.js`** — info kartica vidljiva samo na "Courses" tabu.
- **`TabContent.js`** — switch po `activeTab` koji bira odgovarajuću feature
  komponentu (fallback `MissingSelection` kad nedostaje course/lesson).

### 5.5 Feature komponente (`src/components/`)

| Fajl                       | Funkcija                                                              |
|----------------------------|-----------------------------------------------------------------------|
| `CourseManager.js`         | Lista kurseva + kreiranje/brisanje                                    |
| `LessonManager.js`         | Upload PDF lekcija u izabrani kurs                                    |
| `ContentViewer.js`         | Pregled lekcije, sekcija, LO-a, generisanje/prikaz ontologije         |
| `QuestionGenerator.js`     | UI za pokretanje LLM generisanja pitanja po SOLO nivoima              |
| `QuestionBank.js`          | Pregled, filtriranje, brisanje pitanja                                |
| `ManualQuestionAdder.js`   | Forma za ručno dodavanje pitanja                                      |
| `QuizBuilder.js`           | Kreiranje kviza iz odabranih pitanja, dodavanje pitanja u kviz        |
| `QuizSolver.js`            | UI za rešavanje kviza, snimanje rezultata                             |
| `TranslationManager.js`    | Pregled prevoda kviza, pokretanje prevoda po jezicima                 |
| `TranslationViewer.js`     | Prikaz prevedenog sadržaja                                            |
| `SPARQLQueryTool.js`       | Editor SPARQL upita + tabelarni prikaz rezultata                      |
| `ChatBot.js`               | Floating chat sa kontekstom (course/lesson) i objašnjenjima           |

CSS je deljen kroz `App.css` + per-komponentni fajlovi
(`ChatBot.css`, `SPARQLQueryTool.css`, `TranslationManager.css`).

### 5.6 Context (`src/context/`)

- **`LanguageContext.js`** — `LanguageProvider` koji obavija aplikaciju i
  drži aktivni jezik za prevode (koristi se u `TranslationManager` i
  `TranslationViewer`).

---

## 6. Tok podataka (high-level)

1. **Upload** PDF lekcije → `POST /api/courses/<id>/lessons` → PyPDF2
   ekstrakcija → snima se `Lesson.raw_content`.
2. **Parsiranje** → `POST /api/lessons/<id>/parse` → `content_parser` →
   `Section`-i + `LearningObject`-i u DB.
3. **Ontologija** → `POST /api/lessons/<id>/ontology/generate` →
   `content_parser.extract_ontology_relationships()` →
   `ConceptRelationship` zapisi.
4. **Pitanja** → `POST /api/generate-questions` → `QuestionService` +
   `SoloQuizGeneratorLocal` → `Question` zapisi (sa SOLO nivoima).
5. **Kviz** → `POST /api/quizzes` + `add-questions` → `Quiz` + `QuizQuestion`.
6. **Prevodi** → `POST /api/translate/...` → `TranslationService` (Ollama) →
   tabela odgovarajućeg `*Translation` modela.
7. **Eksport** → OWL/Turtle za ontologiju, JSON za kviz
   (`downloaded_quizzes/`).
8. **Chatbot** → `POST /api/chat` → kontekst (course + lesson + sections
   prefix) prosleđuje se `chatbot_service`.

---

## 7. Pokretanje

Tri terminala (vidi `START_GUIDE.md`):

1. **Ollama**: `./ollama.ps1 serve` (port `11434`/`11435` po konfiguraciji).
2. **Backend**: `cd backend && python app.py` (Flask na `:5000`).
3. **Frontend**: `cd frontend && npm start` (CRA dev server na `:3000`).

---

## 8. Konvencije i napomene za buduće promene

- **Rute** treba dodavati u odgovarajući blueprint u `backend/routes/`.
  Novi domen → novi fajl + dodati ga u `ALL_BLUEPRINTS` u
  `routes/__init__.py`.
- **Repozitorijum** (`repository.py`) je izvor istine za jednostavan CRUD.
  Kompleksni upiti i agregati su u servisima ili (gde je to čist SQLAlchemy)
  direktno u rutama (npr. quiz × translation join u `routes/quizzes.py`).
- **Servisi** ne smeju zvati Flask `request`; ulazne argumente prosleđuju rute.
- **Ontologija** se sastoji iz seed TBox-a (`backend/ontology/`) i ABox-a
  generisanog iz baze. `OntologyManager` ih spaja u `rdflib.Graph`.
- **Prevodi** su sinhroni preko Ollama-e; `translate_batch` i
  `translate_course_content` rade redom (ne paralelno) — može biti sporo.
- **Front state** je centralizovan u `useAppData`; tab-routing je još
  uvek lokalni `useState` u `App.js`. Ako se uvodi pravi router, najbolje je
  uvesti ga oko `<App />` u `index.js` i derivirati `activeTab` iz URL-a.
- **CSS** je čist (bez Tailwind-a, bez CSS-in-JS); klase iz `App.css` su
  deljene (npr. `.card`, `.btn-primary`, `.alert`).
- Kod je pisan da bude bez tipova (ni TS, ni Pydantic) — validacija je ad-hoc
  u rutama. Pri proširenju razmotriti pydantic za request body shape.
