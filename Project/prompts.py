# Prompt templates for SOLO Taxonomy Question Generation

SYSTEM_PROMPT = """Ti si ekspert za obrazovanje i didaktiku, specijalizovan za SOLO taksonomiju.
Tvoj zadatak je da analiziraš nastavni materijal i generišeš pitanja na SRPSKOM jeziku.
Odgovaraj ISKLJUČIVO u JSON formatu bez dodatnog teksta."""

# 1. Analiza strukture teksta (Korak A)
ANALYSIS_PROMPT = """
Analiziraj sledeći tekst i identifikuj elemente pogodne za SOLO taksonomiju.
Vrati JSON sa sledećim ključevima:
- "definicije": lista pojmova i njihovih definicija (za Unistructural).
- "nabrajanja": lista pojmova koji imaju više delova/osobina (za Multistructural).
- "veze": lista parova pojmova koji su povezani uzročno-posledično ili se porede (za Relational).
- "koncepti_za_primenu": lista apstraktnih principa koji se mogu primeniti u novim situacijama (za Extended Abstract).

Tekst:
{text}
"""

# 2. Generisanje pitanja na osnovu analize (Korak B)
SOLO_GENERATION_PROMPTS = {
    "prestructural": """
    Koristeći sledeće DEFINICIJE iz analize teksta: {analysis_data}
    
    Kreiraj 1 pitanje nivoa PRESTRUCTURAL / UNISTRUCTURAL.
    TEHNIKA: Izaberi jednu definiciju i traži prepoznavanje pojma.
    
    PRIMER 1:
    Ulaz: "CPU je centralna procesorska jedinica."
    Pitanje: "Šta označava skraćenica CPU?"
    
    PRIMER 2:
    Ulaz: "Malver je zlonamerni softver."
    Pitanje: "Koji termin se koristi za softver dizajniran da nanese štetu računaru?"
    
    Vrati SAMO JSON:
    {{
        "pitanje": "...",
        "opcije": ["A)...", "B)...", "C)..."],
        "tacan_odgovor": "...",
        "objasnjenje": "..."
    }}
    """,
    
    "multistructural": """
    Koristeći sledeća NABRAJANJA iz analize teksta: {analysis_data}
    
    Kreiraj 1 pitanje nivoa MULTISTRUCTURAL.
    TEHNIKA: Izaberi pojam koji ima više delova i traži da se identifikuju svi ili onaj koji ne pripada.
    
    PRIMER 1:
    Ulaz: "Osnovne boje su crvena, plava i žuta."
    Pitanje: "Koje od navedenih boja spadaju u osnovne boje?"
    
    PRIMER 2:
    Ulaz: "Komponente računara su CPU, RAM, HDD."
    Pitanje: "Šta od navedenog NIJE hardverska komponenta računara?"
    
    Vrati SAMO JSON:
    {{
        "pitanje": "...",
        "opcije": ["A)...", "B)...", "C)..."],
        "tacan_odgovor": "...",
        "objasnjenje": "..."
    }}
    """,
    
    "relational": """
    Koristeći sledeće VEZE iz analize teksta: {analysis_data}
    
    Kreiraj 1 pitanje nivoa RELATIONAL.
    TEHNIKA: Izaberi dva povezana pojma i traži objašnjenje njihove veze.
    
    PRIMER 1:
    Ulaz: "Veća količina RAM-a omogućava brži rad više aplikacija istovremeno."
    Pitanje: "Kako povećanje RAM memorije utiče na multitasking performanse računara?"
    
    PRIMER 2:
    Ulaz: "Virusi se šire kopiranjem, dok Trojanci zahtevaju da ih korisnik pokrene."
    Pitanje: "Koja je ključna razlika u načinu širenja između virusa i Trojanaca?"
    
    Vrati SAMO JSON:
    {{
        "pitanje": "...",
        "opcije": ["A)...", "B)...", "C)..."],
        "tacan_odgovor": "...",
        "objasnjenje": "..."
    }}
    """,
    
    "extended_abstract": """
    Koristeći sledeće KONCEPTE ZA PRIMENU iz analize teksta: {analysis_data}
    
    Kreiraj 1 pitanje nivoa EXTENDED ABSTRACT.
    TEHNIKA: Postavi hipotetičku situaciju koja nije u tekstu i traži primenu principa.
    
    PRIMER 1:
    Ulaz: "Princip enkripcije štiti podatke od neovlašćenog pristupa."
    Pitanje: "Kompanija želi da zaštiti poverljive mejlove zaposlenih koji rade od kuće. Koju sigurnosnu meru bi bilo najbolje primeniti i zašto?"
    
    Vrati SAMO JSON:
    {{
        "pitanje": "...",
        "opcije": ["A)...", "B)...", "C)..."],
        "tacan_odgovor": "...",
        "objasnjenje": "..."
    }}
    """
}

# 3. Validacija i Klasifikacija (Self-Correction)
CLASSIFICATION_PROMPT = """
Analiziraj sledeće pitanje i odgovor, i klasifikuj ga prema SOLO taksonomiji.
Pitanje: {question}
Očekivani odgovor: {answer}

Odredi nivo (Prestructural, Unistructural, Multistructural, Relational, Extended Abstract) i daj kratko obrazloženje.
"""
