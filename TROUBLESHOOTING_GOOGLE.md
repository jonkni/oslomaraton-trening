# Feilsøking: Google Calendar "Tilgang blokkert" (403)

## Problem
```
Feil 403: access_denied
```

Dette skjer fordi OAuth consent screen er i "Testing"-modus, og du må legge til din egen e-post som test user.

## Løsning

### Steg 1: Gå til OAuth consent screen

1. Åpne [Google Cloud Console](https://console.cloud.google.com/)
2. Velg ditt prosjekt (Oslo Marathon Training)
3. Gå til **APIs & Services** → **OAuth consent screen**

### Steg 2: Legg til test user

1. Scroll ned til **Test users**
2. Klikk **+ ADD USERS**
3. Legg til din egen e-postadresse (den du bruker for Google Calendar)
4. Klikk **Save**

### Steg 3: Prøv på nytt

```bash
# Slett gammel token først
rm token.pickle

# Kjør synkronisering på nytt
python google_calendar_sync.py
```

Nå skal autentiseringen fungere!

---

## Alternativ: Publiser appen (ikke nødvendig for personlig bruk)

Hvis du vil unngå "test user"-begrensningen:

1. Gå til **OAuth consent screen**
2. Klikk **PUBLISH APP**
3. Bekreft publisering

**OBS:** Dette er IKKE nødvendig for personlig bruk. Å legge til deg selv som test user er enklere og tryggere.

---

## Andre vanlige feil

### "Invalid client" / "Client ID not found"
- Sjekk at `credentials.json` er riktig lastet ned
- Sjekk at du bruker riktig prosjekt i Google Cloud Console

### "Redirect URI mismatch"
- Dette skal ikke skje med Desktop app
- Hvis det skjer, slett `credentials.json` og last ned på nytt

### "API not enabled"
- Gå til **APIs & Services** → **Library**
- Søk etter "Google Calendar API"
- Klikk **Enable**
