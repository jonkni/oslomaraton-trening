# Google Calendar Integration Setup

Automatisk synkronisering av treningsplan til Google Calendar.

## Steg 1: Opprett Google Cloud Project

1. Gå til [Google Cloud Console](https://console.cloud.google.com/)
2. Klikk "Create Project" eller velg et eksisterende
3. Gi prosjektet et navn (f.eks. "Oslo Marathon Training")

## Steg 2: Aktiver Google Calendar API

1. I Google Cloud Console, gå til **APIs & Services** → **Library**
2. Søk etter "Google Calendar API"
3. Klikk på "Google Calendar API"
4. Klikk **Enable**

## Steg 3: Opprett OAuth 2.0 Credentials

1. Gå til **APIs & Services** → **Credentials**
2. Klikk **Create Credentials** → **OAuth client ID**
3. Hvis du får beskjed om å konfigurere OAuth consent screen:
   - Velg **External**
   - Fyll ut obligatoriske felter:
     - App name: `Oslo Marathon Training`
     - User support email: din e-post
     - Developer contact: din e-post
   - Klikk **Save and Continue** gjennom alle steg
   - Klikk **Back to Dashboard**

4. Gå tilbake til **Credentials** → **Create Credentials** → **OAuth client ID**
5. Velg **Application type**: `Desktop app`
6. Navn: `Oslo Marathon Desktop Client`
7. Klikk **Create**

## Steg 4: Last ned credentials

1. Klikk på **Download** (↓) ikonet ved siden av din nye OAuth 2.0 Client ID
2. Lagre filen som `credentials.json` i prosjektmappen
3. Beskytt filen:
   ```bash
   chmod 600 credentials.json
   ```

## Steg 5: Installer Python-pakker

Legg til Google Calendar API-pakker i requirements.txt og installer:

```bash
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

## Steg 6: Første gangs autentisering

Kjør synkroniseringsskriptet:

```bash
python google_calendar_sync.py
```

Dette vil:
1. Åpne nettleser for autentisering
2. Be deg logge inn på Google-kontoen din
3. Be om tillatelse til å administrere kalenderhendelser
4. Lagre token i `token.pickle` for fremtidig bruk

## Steg 7: Synkroniser treningsplan

Hver gang du oppdaterer treningsplanen:

```bash
# 1. Generer ny plan
python training_plan.py

# 2. Synkroniser til Google Calendar
python google_calendar_sync.py
```

Scriptet vil:
- ✓ Slette gamle treningsøkter fra planen
- ✓ Opprette nye økter med oppdaterte detaljer
- ✓ Inkludere oppvarming og sykkelalternativer
- ✓ Sette påminnelser (1 time før)

## Hva legges inn i kalenderen?

Hver treningsøkt får:
- 📅 **Dato og tid** (basert på økttype)
  - Tidlig morgen-økter: 06:30
  - Terskel/intervaller: 17:00
  - Langtur: 09:00 (lørdag)
  - Andre økter: 18:00

- 📝 **Beskrivelse** med:
  - Øktdetaljer (pace, distanse, intervaller)
  - 🔥 Oppvarming
  - 🚴 Sykkel-alternativ (hvis kne betendt)
  - Fase (Oppbygging, Base, Peak, etc.)

- ⏰ **Påminnelse**: 1 time før økten

- 🎨 **Farge**: Blå (sports-farge)

## Automatisk oppdatering

For å holde kalenderen oppdatert:

1. Kjør `python training_plan.py` hver uke for å justere basert på ny Strava-data
2. Kjør `python google_calendar_sync.py` for å synkronisere endringene

Gamle økter slettes automatisk og erstattes med oppdaterte versjoner!

## Sikkerhet

- `credentials.json` - ALDRI commit til git (allerede i `.gitignore`)
- `token.pickle` - ALDRI commit til git (allerede i `.gitignore`)
- Begge filene bør ha `chmod 600` (kun eier kan lese/skrive)

## Feilsøking

### "Mangler credentials.json"
- Last ned OAuth 2.0 credentials fra Google Cloud Console
- Lagre som `credentials.json` i prosjektmappen

### "Access blocked" under autentisering
- Gå til Google Cloud Console → OAuth consent screen
- Legg til din egen e-post under "Test users"
- Prøv autentisering på nytt

### "Token expired"
- Slett `token.pickle`
- Kjør `python google_calendar_sync.py` på nytt for å re-autentisere

---

**Nå er du klar til å automatisk synkronisere treningsplanen din! 📅🏃‍♂️**
