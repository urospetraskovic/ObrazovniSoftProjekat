# Kako koristiti besplatne modele (Ollama)

Ako ne želiš da plaćaš OpenAI, možeš koristiti **Ollama** da pokrećeš modele lokalno na svom računaru.

## 1. Instalacija Ollama
1. Preuzmi Ollama sa [ollama.com](https://ollama.com).
2. Instaliraj program.
3. Otvori PowerShell i pokreni sledeću komandu da preuzmeš model:
   ```powershell
   ollama pull llama3
   ```
   (Možeš koristiti i `mistral` ili `gemma` ako želiš manje modele).

## 2. Korišćenje u projektu
Skripta `main.py` je ažurirana da automatski detektuje ako imaš instaliranu `ollama` biblioteku i ako OpenAI ključ nedostaje.

Samo pokreni:
```powershell
python main.py
```

Sistem će pokušati da kontaktira tvoj lokalni Ollama server.

## Alternativa: Groq (Cloud, Besplatno)
Ako ti je računar spor, možeš koristiti [Groq](https://console.groq.com/).
1. Registruj se besplatno.
2. Kreiraj API Key.
3. Ubaci ga u `.env` fajl kao `GROQ_API_KEY=...`.
(Ovo zahteva malu izmenu u kodu ako se odlučiš za ovu opciju).
