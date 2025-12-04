# SOLO Taxonomy Question Generator

# SOLO Taxonomy Question Generator

Automatski generator pitanja iz nastavnog materijala klasifikovanih prema SOLO taksonomiji.

## ✨ Nove funkcionalnosti v2.0

- **🔄 Dvofazni pristup**: Prvo izdvajanje koncepata, zatim generisanje pitanja
- **🌏 Više LLM providera**: DeepSeek, Claude, Gemini, Grok, OpenAI
- **📚 Podela po poglavljima**: Automatska segmentacija tekstualnog sadržaja
- **✅ Validacija odgovora**: Tačni odgovori samo iz materijala
- **🎯 Poboljšani SOLO promptovi**: Detaljne definicije nivoa taksonomije

## 🎓 SOLO Taksonomija

Sistem generiše pitanja za 4 nivoa SOLO taksonomije:

1. **Prestructural/Unistructural**: Jednostavno prepoznavanje i definisanje
2. **Multistructural**: Nabrajanje komponenti bez povezivanja  
3. **Relational**: Objašnjavanje veza i uzročno-posledičnih odnosa
4. **Extended Abstract**: Primena principa u novim situacijama

## 📋 Instalacija

```bash
# 1. Kloniraj repozitorijum
git clone <repository-url>
cd ObrazovniSoftProjekat/Project

# 2. Instaliraj dependencies (biranje po potrebi)
pip install python-dotenv requests

# Za DeepSeek, Claude, Gemini ili OpenAI:
pip install openai anthropic google-generativeai

# 3. Konfiguriši API ključ
cp .env.example .env
# Edituj .env i dodaj jedan od API ključeva

# 4. Pokreni
python main.py
```

## 🔑 Podržani LLM Provideri

Sistem automatski detektuje dostupne providere po prioritetu:

### DeepSeek (Preporučeno)
- Kineski model, brz i jeftin
- Registracija: https://platform.deepseek.com/
- Dodaj: `DEEPSEEK_API_KEY=your_key`

### Claude/Anthropic
- Odličan za obrazovni sadržaj
- Registracija: https://console.anthropic.com/
- Dodaj: `ANTHROPIC_API_KEY=your_key`

### Google Gemini  
- Možda besplatno uz Google nalog
- Registracija: https://makersuite.google.com/app/apikey
- Dodaj: `GOOGLE_API_KEY=your_key`

### Grok (xAI)
- Registracija: https://console.x.ai/
- Dodaj: `GROK_API_KEY=your_key`

### OpenAI (Fallback)
- Stariji modeli (gpt-3.5-turbo)
- Dodaj: `OPENAI_API_KEY=your_key`

## 📂 Kako koristiti

1. **Pripremi materijal**: Stavi tekstualni sadržaj u `.txt` fajl
2. **Pokreni generator**: `python main.py`
3. **Preuzmi rezultate**: Otvori `generisana_pitanja.json`

### Format input fajla
```
POGLAVLJE 1: NASLOV

Sadržaj poglavlja...
Definicije, objašnjenja, primeri.

POGLAVLJE 2: DRUGI NASLOV

Drugo poglavlje...
```

## 📊 Izlazni format

```json
{
  "poglavlje_broj": 1,
  "sadrzaj_preview": "Tekst poglavlja...",
  "koncepti": [
    {
      "naziv": "Fotosinteza",
      "definicija": "Proces pretvaranja...", 
      "solo_nivoi": ["unistructural", "relational"]
    }
  ],
  "pitanja": [
    {
      "solo_nivo": "relational",
      "pitanje_data": {
        "pitanje": "Kako svetlost utiče na fotosintezu?",
        "opcije": ["A) ...", "B) ...", "C) ..."],
        "tacan_odgovor": "A",
        "objasnjenje": "..."
      },
      "validacija": {
        "likely_from_material": true
      }
    }
  ]
}
```

## 🎯 Karakteristike

- **Offline rad**: Može da radi preko noći bez prekida
- **Validacija**: Tačni odgovori zasnovani na materijalu
- **Skalabilnost**: Obrađuje velike tekstove po poglavljima
- **Fleksibilnost**: Podrška za različite LLM providere
- **Preciznost**: Detaljni SOLO promptovi za tačnu klasifikaciju

## 🔧 Troubleshooting

### "Nema dostupnih API ključeva"
- Proverite da li ste kopirali `.env.example` u `.env`
- Dodajte validan API ključ za jedan od providera

### "Greška sa parsing JSON"
- Rezultati se čuvaju kao 'raw_content' za manual pregled
- Pokušajte sa drugim LLM providerom

### "Nema izdvojenih koncepata"  
- Proverite format teksta (dodajte poglavlja ili paragrafe)
- Povećajte chunk_size u split_by_chapters metodi
