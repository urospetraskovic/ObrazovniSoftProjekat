# Kako podesiti OpenAI API

Da bi ovaj projekat mogao da "razmišlja" i generiše pitanja, potreban mu je pristup OpenAI modelima (GPT-3.5 ili GPT-4). To se radi preko **API ključa**.

Evo korak-po-korak uputstva kako da dođeš do ključa i povežeš ga sa projektom.

## 1. Kreiranje OpenAI naloga
1. Idi na [OpenAI Platform](https://platform.openai.com/).
2. Klikni na **Sign Up** (ili **Log In** ako već imaš nalog).
3. *Napomena*: OpenAI API nije besplatan (iako je jeftin za ovakve testove). Moraćeš da dodaš kreditnu karticu i uplatiš minimalni iznos (npr. 5$) na [Billing settings](https://platform.openai.com/settings/organization/billing/overview).

## 2. Generisanje API Ključa
1. Kada se uloguješ, idi na [API Keys stranicu](https://platform.openai.com/api-keys).
2. Klikni na dugme **+ Create new secret key**.
3. Daj mu ime (npr. "ObrazovniSoftver").
4. **Kopiraj ključ odmah!** (Izgleda kao `sk-...`). Nećeš moći da ga vidiš ponovo.

## 3. Povezivanje sa projektom
1. U folderu projekta (`d:\GitHub\ObrazovniSoftProjekat\Project`), napravi novi fajl i nazovi ga `.env` (samo tačka i env, bez imena ispred).
2. Otvori taj fajl i zalepi svoj ključ ovako:

```
OPENAI_API_KEY=sk-tvoj-dugacki-kljuc-koji-si-kopirao
```

3. Sačuvaj fajl.

## 4. Testiranje
Kada to uradiš, skripta `main.py` će automatski učitati taj ključ i moći će da šalje zahteve OpenAI-u umesto da koristi "mock" (lažne) podatke.
