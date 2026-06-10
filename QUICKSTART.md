# Quick Start Guide

Kom i gang på 5 minutter! ⚡

## Steg 1: Installer pakker (30 sek)

```bash
pip install -r requirements.txt
```

## Steg 2: Opprett Strava API App (2 min)

1. Gå til: **https://www.strava.com/settings/api**
2. Klikk "Create & Manage Your App"
3. Fyll ut:
   - **Application Name:** `Oslo Marathon Training`
   - **Category:** `Training`
   - **Website:** `http://localhost`
   - **Authorization Callback Domain:** `localhost`
4. Klikk "Create"
5. Kopier **Client ID** og **Client Secret**

## Steg 3: Lag .env fil (30 sek)

```bash
cat > .env << 'EOF'
STRAVA_CLIENT_ID=DITT_CLIENT_ID_HER
STRAVA_CLIENT_SECRET=DITT_CLIENT_SECRET_HER
EOF
```

**VIKTIG:** Erstatt `DITT_CLIENT_ID_HER` og `DITT_CLIENT_SECRET_HER` med verdiene fra Strava!

## Steg 4: Kjør! (1 min)

```bash
# Test autentisering
python strava_auth.py

# Generer treningsplan
python training_plan.py
```

En nettleser vil åpne - logg inn på Strava og godkjenn tilgang.

## ✅ Ferdig!

Du har nå:
- ✓ Hentet alle dine Strava-aktiviteter
- ✓ Analysert nåværende form
- ✓ Generert et 14-ukers treningsprogram for Oslo halvmaraton
- ✓ Fått et estimert tidsmål basert på din progresjon

Sjekk filene:
- `treningsplan_oslo_halvmaraton.csv` - Detaljert ukesplan
- `strava_activities.csv` - All treningsdata

---

**Neste steg:** Les [README.md](README.md) for full dokumentasjon!
